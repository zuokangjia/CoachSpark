from typing import TypedDict, List, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from app.ai.llm import get_llm
from app.ai.prompts.review import REVIEW_SYSTEM_PROMPT, REVIEW_USER_PROMPT


class ReviewState(TypedDict):
    raw_notes: str
    company_name: str
    position: str
    round_num: int
    jd_key_points: List[str]
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
                "Extract all interview questions mentioned in these notes. Return a JSON array of objects with 'question' and 'your_answer_summary' fields.",
            ),
            ("human", "{raw_notes}"),
        ]
    )
    chain = prompt | llm | JsonOutputParser()
    result = chain.invoke({"raw_notes": state["raw_notes"]})
    questions = result if isinstance(result, list) else []
    questions = [q for q in questions if isinstance(q, dict)]
    return {"questions": questions}


def score_answers(state: ReviewState) -> dict:
    llm = get_llm()
    questions = state.get("questions", [])
    scored = []
    for q in questions:
        if not isinstance(q, dict):
            continue
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Score this interview answer from 1-10. Return JSON with 'score' (int) and 'assessment' (reason). Be specific about what was missing or done well.",
                ),
                (
                    "human",
                    "Question: {question}\nAnswer: {answer}\nJD Context: {jd_context}",
                ),
            ]
        )
        chain = prompt | llm | JsonOutputParser()
        try:
            result = chain.invoke(
                {
                    "question": q.get("question", ""),
                    "answer": q.get("your_answer_summary", ""),
                    "jd_context": ", ".join(state.get("jd_key_points", [])),
                }
            )
            scored.append(
                {
                    **q,
                    "score": result.get("score", 5),
                    "assessment": result.get("assessment", ""),
                    "improvement": result.get("improvement", ""),
                }
            )
        except Exception:
            scored.append(
                {**q, "score": 5, "assessment": "Unable to evaluate", "improvement": ""}
            )
    return {"questions": scored}


def generate_insights(state: ReviewState) -> dict:
    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", REVIEW_SYSTEM_PROMPT),
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
    return {}


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
    graph.add_node("score", score_answers)
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
