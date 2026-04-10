from typing import TypedDict, List, Any
import json

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from app.ai.llm import get_llm
from app.ai.prompts.review import (
    REVIEW_SYSTEM_PROMPT,
    REVIEW_USER_PROMPT,
    SCORING_RUBRIC,
)

"""
Design: Interview Review Analysis LangGraph
核心思想：状态机流水线：extract (问题提取) -> score (批量评分) -> insights (洞察生成)
-> predict (下轮预测) -> validate (输出验证) -> finalize (最终整理)。
extract 和 score 先于 insights 运行，确保评分结果可被洞察生成阶段使用。
validate 阶段检查完整性，不合格则回流到合适的节点重试。
"""


class ReviewState(TypedDict):
    raw_notes: str
    company_name: str
    position: str
    round_num: int
    jd_key_points: List[str]
    context: str
    questions: List[dict]
    weak_points: List[str]
    strong_points: List[str]
    next_round_prediction: List[str]
    interviewer_signals: List[str]
    analysis_complete: bool


def _to_clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _normalize_score(value: Any) -> int:
    if isinstance(value, bool):
        return 5
    if isinstance(value, (int, float)):
        score = int(round(value))
        return max(1, min(10, score))
    if isinstance(value, str):
        digits = "".join(ch for ch in value if ch.isdigit())
        if digits:
            score = int(digits)
            return max(1, min(10, score))
    return 5


def _normalize_string_list(
    values: Any, min_items: int = 0, max_items: int = 8
) -> List[str]:
    if not isinstance(values, list):
        values = []
    cleaned = []
    seen = set()
    for value in values:
        text = _to_clean_text(value)
        if not text:
            continue
        if text in seen:
            continue
        seen.add(text)
        cleaned.append(text)
        if len(cleaned) >= max_items:
            break
    while len(cleaned) < min_items:
        cleaned.append("待补充")
    return cleaned


def _normalize_questions(
    raw_questions: Any, fallback_questions: List[dict]
) -> List[dict]:
    base_questions = fallback_questions if isinstance(fallback_questions, list) else []
    if not isinstance(raw_questions, list):
        raw_questions = []

    normalized: List[dict] = []
    for idx, item in enumerate(raw_questions):
        if not isinstance(item, dict):
            continue
        fallback_item = (
            base_questions[idx]
            if idx < len(base_questions) and isinstance(base_questions[idx], dict)
            else {}
        )
        question_text = _to_clean_text(
            item.get("question") or fallback_item.get("question")
        )
        answer_summary = _to_clean_text(
            item.get("your_answer_summary") or fallback_item.get("your_answer_summary")
        )
        if not question_text:
            continue
        assessment = _to_clean_text(item.get("assessment"))
        if not assessment:
            assessment = "证据不足，建议补充更具体的回答细节后再评估。"
        improvement = _to_clean_text(item.get("improvement"))
        if not improvement:
            improvement = (
                "围绕该问题补齐概念定义、实现细节与项目案例，并进行 3 分钟口述演练。"
            )
        normalized.append(
            {
                "question": question_text,
                "your_answer_summary": answer_summary,
                "score": _normalize_score(
                    item.get("score", fallback_item.get("score", 5))
                ),
                "assessment": assessment,
                "improvement": improvement,
            }
        )

    if not normalized:
        return [q for q in base_questions if isinstance(q, dict)]
    return normalized


def extract_questions(state: ReviewState) -> dict:
    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "从以下面试笔记中提取所有提到的面试问题和候选人的回答。返回 JSON 数组，每项包含 'question'（面试问题）和 'your_answer_summary'（候选人回答摘要）。如果提到了问题但回答不清楚，your_answer_summary 设为空字符串。使用中文。",
            ),
            ("human", "{raw_notes}"),
        ]
    )
    chain = prompt | llm | JsonOutputParser()
    result = chain.invoke({"raw_notes": state["raw_notes"]})
    questions = result if isinstance(result, list) else []
    questions = [q for q in questions if isinstance(q, dict)]
    return {"questions": questions}


def batch_score_answers(state: ReviewState) -> dict:
    llm = get_llm()
    questions = state.get("questions", [])
    if not questions:
        return {"questions": []}

    jd_context = ", ".join(state.get("jd_key_points", []))
    questions_json = json.dumps(questions, ensure_ascii=False)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"你是资深技术面试官。为以下每道回答打分（1-10 分）。{SCORING_RUBRIC}\n\n返回 JSON 数组，每项包含 'score'（整数）、'assessment'（评分理由，1-2 句话）和 'improvement'（具体可执行的改进建议）。保持与输入问题的顺序一致。使用中文。",
            ),
            (
                "human",
                "JD 背景：{jd_context}\n\n需要评分的问题：\n{questions}",
            ),
        ]
    )
    chain = prompt | llm | JsonOutputParser()

    try:
        results = chain.invoke(
            {
                "jd_context": jd_context,
                "questions": questions_json,
            }
        )
        if not isinstance(results, list):
            results = []
    except Exception:
        results = []

    scored = []
    for i, q in enumerate(questions):
        if i < len(results) and isinstance(results[i], dict):
            scored.append(
                {
                    **q,
                    "score": results[i].get("score", 5),
                    "assessment": results[i].get("assessment", ""),
                    "improvement": results[i].get("improvement", ""),
                }
            )
        else:
            scored.append(
                {
                    **q,
                    "score": 5,
                    "assessment": "信息不足，暂无法完成有效评估。",
                    "improvement": "",
                }
            )

    return {"questions": _normalize_questions(scored, questions)}


def generate_insights(state: ReviewState) -> dict:
    llm = get_llm()
    context = state.get("context", "")
    context_section = f"\n\n## User History Context\n{context}" if context else ""

    system_prompt = REVIEW_SYSTEM_PROMPT + context_section
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", REVIEW_USER_PROMPT),
        ]
    )
    chain = prompt | llm | JsonOutputParser()
    result = chain.invoke(
        {
            "company_name": state.get("company_name", ""),
            "position": state.get("position", ""),
            "round_num": state.get("round_num", 1),
            "jd_key_points": state.get("jd_key_points", []),
            "raw_notes": state.get("raw_notes", ""),
        }
    )
    if not isinstance(result, dict):
        return {
            "weak_points": [],
            "strong_points": [],
            "next_round_prediction": [],
            "interviewer_signals": [],
            "questions": _normalize_questions([], state.get("questions", [])),
        }

    normalized_questions = _normalize_questions(
        result.get("questions", state.get("questions", [])),
        state.get("questions", []),
    )

    weak_points = _normalize_string_list(
        result.get("weak_points", []),
        max_items=10,
    )
    low_score_topics = _normalize_string_list(
        [
            q.get("question", "")
            for q in normalized_questions
            if q.get("score", 10) <= 5
        ],
        max_items=10,
    )
    if not weak_points and low_score_topics:
        weak_points = low_score_topics

    return {
        "weak_points": weak_points,
        "strong_points": _normalize_string_list(
            result.get("strong_points", []),
            max_items=10,
        ),
        "next_round_prediction": _normalize_string_list(
            result.get("next_round_prediction", []),
            min_items=0,
            max_items=5,
        ),
        "interviewer_signals": _normalize_string_list(
            result.get("interviewer_signals", []),
            max_items=6,
        ),
        "questions": normalized_questions,
    }


def predict_next_round(state: ReviewState) -> dict:
    weak_points = _normalize_string_list(state.get("weak_points", []), max_items=5)
    if weak_points:
        return {
            "next_round_prediction": _normalize_string_list(
                [f"围绕「{wp}」的深入追问" for wp in weak_points],
                min_items=3,
                max_items=5,
            )
        }

    questions = state.get("questions", [])
    low_scored = [
        q.get("question", "")
        for q in questions
        if isinstance(q, dict)
        and isinstance(q.get("score"), (int, float))
        and q.get("score", 10) <= 5
    ]
    return {
        "next_round_prediction": _normalize_string_list(
            [f"围绕「{q}」的深入追问" for q in low_scored],
            min_items=0,
            max_items=5,
        )
    }


def validate_output(state: ReviewState) -> dict:
    questions = state.get("questions", [])
    if not questions:
        return {"analysis_complete": False}
    has_valid_scores = all(
        isinstance(q.get("score"), (int, float)) and 1 <= q.get("score", 0) <= 10
        for q in questions
    )
    has_assessments = all(bool(q.get("assessment", "").strip()) for q in questions)
    has_improvements = all(bool(q.get("improvement", "").strip()) for q in questions)
    has_prediction = len(state.get("next_round_prediction", [])) >= 3
    analysis_complete = (
        has_valid_scores and has_assessments and has_improvements and has_prediction
    )
    return {"analysis_complete": analysis_complete}


def finalize_output(state: ReviewState) -> dict:
    questions = _normalize_questions(
        state.get("questions", []), state.get("questions", [])
    )

    weak_points = _normalize_string_list(state.get("weak_points", []), max_items=10)
    if not weak_points:
        weak_points = _normalize_string_list(
            [
                q.get("question", "")
                for q in questions
                if isinstance(q, dict)
                and isinstance(q.get("score"), (int, float))
                and q.get("score", 10) <= 5
            ],
            max_items=10,
        )

    strong_points = _normalize_string_list(state.get("strong_points", []), max_items=10)
    predictions = _normalize_string_list(
        state.get("next_round_prediction", []), min_items=0, max_items=5
    )
    if len(predictions) < 3 and weak_points:
        fallback = [f"围绕「{wp}」的深入追问" for wp in weak_points[:5]]
        predictions = _normalize_string_list(fallback, min_items=3, max_items=5)

    interviewer_signals = _normalize_string_list(
        state.get("interviewer_signals", []), max_items=6
    )

    for q in questions:
        if not q.get("assessment"):
            q["assessment"] = "证据不足，建议补充更具体的回答细节后再评估。"
        if not q.get("improvement"):
            q["improvement"] = (
                "围绕该问题补齐概念定义、实现细节与项目案例，并进行 3 分钟口述演练。"
            )

    return {
        "questions": questions,
        "weak_points": weak_points,
        "strong_points": strong_points,
        "next_round_prediction": predictions,
        "interviewer_signals": interviewer_signals,
        "analysis_complete": True,
    }


def build_review_graph():
    from langgraph.graph import StateGraph, END

    graph = StateGraph(ReviewState)
    graph.add_node("extract", extract_questions)
    graph.add_node("score", batch_score_answers)
    graph.add_node("insights", generate_insights)
    graph.add_node("predict", predict_next_round)
    graph.add_node("validate", validate_output)
    graph.add_node("finalize", finalize_output)

    graph.set_entry_point("extract")
    graph.add_edge("extract", "score")
    graph.add_edge("score", "insights")
    graph.add_edge("insights", "predict")
    graph.add_edge("predict", "validate")
    graph.add_edge("validate", "finalize")
    graph.add_edge("finalize", END)

    return graph.compile()
