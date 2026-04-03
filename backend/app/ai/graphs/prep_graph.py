from typing import TypedDict, List, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from app.ai.llm import get_llm
from app.ai.prompts.prep import PREP_SYSTEM_PROMPT, PREP_USER_PROMPT


class PrepState(TypedDict):
    company_id: str
    target_round: int
    days_available: int
    weak_points: List[str]
    jd_directions: List[str]
    interview_chain: List[dict]
    context: str
    daily_tasks: List[dict]


def prioritize_weak_points(state: PrepState) -> dict:
    weak_points = state.get("weak_points", [])
    if not isinstance(weak_points, list):
        weak_points = []
    return {"weak_points": weak_points}


def extract_jd_directions(state: PrepState) -> dict:
    return {}


def allocate_tasks_by_day(state: PrepState) -> dict:
    llm = get_llm()
    context = state.get("context", "")
    context_section = f"\n\n## 用户历史上下文\n{context}" if context else ""

    system_prompt = PREP_SYSTEM_PROMPT + context_section
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", PREP_USER_PROMPT),
        ]
    )
    chain = prompt | llm | JsonOutputParser()
    result = chain.invoke(
        {
            "target_round": state.get("target_round", 1),
            "days_available": state.get("days_available", 3),
            "weak_points": state.get("weak_points", []),
            "jd_directions": state.get("jd_directions", []),
            "interview_chain": state.get("interview_chain", []),
        }
    )
    daily_tasks = result.get("daily_tasks", []) if isinstance(result, dict) else []
    for i, task in enumerate(daily_tasks):
        if isinstance(task, dict):
            task.setdefault("day", i + 1)
            task.setdefault("completed", False)
    return {"daily_tasks": daily_tasks}


def generate_daily_details(state: PrepState) -> dict:
    return {}


def build_prep_graph():
    from langgraph.graph import StateGraph, END

    graph = StateGraph(PrepState)
    graph.add_node("prioritize", prioritize_weak_points)
    graph.add_node("extract_jd", extract_jd_directions)
    graph.add_node("allocate", allocate_tasks_by_day)
    graph.add_node("details", generate_daily_details)

    graph.set_entry_point("prioritize")
    graph.add_edge("prioritize", "extract_jd")
    graph.add_edge("extract_jd", "allocate")
    graph.add_edge("allocate", "details")
    graph.add_edge("details", END)

    return graph.compile()
