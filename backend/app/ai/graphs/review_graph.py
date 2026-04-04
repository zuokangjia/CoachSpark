from typing import TypedDict, List
import json

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from app.ai.llm import get_llm
from app.ai.prompts.review import (
    REVIEW_SYSTEM_PROMPT,
    REVIEW_USER_PROMPT,
    SCORING_RUBRIC,
)


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
                    "assessment": "Unable to evaluate",
                    "improvement": "",
                }
            )

    return {"questions": scored}


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
            "questions": state.get("questions", []),
        }
    return {
        "weak_points": result.get("weak_points", []),
        "strong_points": result.get("strong_points", []),
        "next_round_prediction": result.get("next_round_prediction", []),
        "interviewer_signals": result.get("interviewer_signals", []),
        "questions": result.get("questions", state.get("questions", [])),
    }


def predict_next_round(state: ReviewState) -> dict:
    existing_prediction = state.get("next_round_prediction", [])
    if existing_prediction:
        return {"next_round_prediction": existing_prediction}

    weak_points = state.get("weak_points", [])
    questions = state.get("questions", [])
    low_scored = [
        q.get("question", "")
        for q in questions
        if isinstance(q, dict)
        and isinstance(q.get("score"), (int, float))
        and q["score"] <= 5
    ]

    if not weak_points and not low_scored:
        return {"next_round_prediction": []}

    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是资深技术面试官。基于候选人的薄弱点和本轮低分问题，预测下一轮面试最可能被问到的话题。考虑面试官通常会针对候选人薄弱的领域深入追问。返回 3-5 个具体的话题预测。使用中文。",
            ),
            (
                "human",
                "薄弱点：\n{weak_points}\n\n低分问题（≤5 分）：\n{low_scored}",
            ),
        ]
    )
    chain = prompt | llm | JsonOutputParser()
    try:
        result = chain.invoke(
            {
                "weak_points": "\n".join(f"- {wp}" for wp in weak_points),
                "low_scored": "\n".join(f"- {q}" for q in low_scored)
                if low_scored
                else "None",
            }
        )
        predictions = result if isinstance(result, list) else []
    except Exception:
        predictions = []

    return {"next_round_prediction": predictions}


def validate_output(state: ReviewState) -> dict:
    questions = state.get("questions", [])
    if not questions:
        return {"analysis_complete": False}
    has_valid_scores = all(
        isinstance(q.get("score"), (int, float)) and 1 <= q.get("score", 0) <= 10
        for q in questions
    )
    has_assessments = all(bool(q.get("assessment", "").strip()) for q in questions)
    analysis_complete = has_valid_scores and has_assessments
    return {"analysis_complete": analysis_complete}


def build_review_graph():
    from langgraph.graph import StateGraph, END

    graph = StateGraph(ReviewState)
    graph.add_node("extract", extract_questions)
    graph.add_node("score", batch_score_answers)
    graph.add_node("insights", generate_insights)
    graph.add_node("predict", predict_next_round)
    graph.add_node("validate", validate_output)

    graph.set_entry_point("extract")
    graph.add_edge("extract", "score")
    graph.add_edge("score", "insights")
    graph.add_edge("insights", "predict")
    graph.add_edge("predict", "validate")
    graph.add_conditional_edges(
        "validate",
        lambda s: "insights" if not s["analysis_complete"] else END,
    )

    return graph.compile()
