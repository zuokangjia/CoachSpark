from typing import TypedDict, List, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from app.ai.llm import get_llm
from app.ai.prompts.match import MATCH_SYSTEM_PROMPT, MATCH_USER_PROMPT


class MatchState(TypedDict):
    jd_text: str
    resume_text: str
    jd_requirements: List[str]
    resume_info: List[str]
    match_percentage: int
    strengths: List[str]
    gaps: List[str]
    suggestions: List[str]


def extract_jd_requirements(state: MatchState) -> dict:
    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Extract the key technical requirements and qualifications from this job description. Return a JSON array of strings.",
            ),
            ("human", "{jd_text}"),
        ]
    )
    chain = prompt | llm | JsonOutputParser()
    jd_requirements = chain.invoke({"jd_text": state["jd_text"]})
    if isinstance(jd_requirements, str):
        jd_requirements = [jd_requirements]
    return {"jd_requirements": jd_requirements}


def extract_resume_info(state: MatchState) -> dict:
    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Extract the key skills, experiences, and qualifications from this resume. Return a JSON array of strings.",
            ),
            ("human", "{resume_text}"),
        ]
    )
    chain = prompt | llm | JsonOutputParser()
    resume_info = chain.invoke({"resume_text": state["resume_text"]})
    if isinstance(resume_info, str):
        resume_info = [resume_info]
    return {"resume_info": resume_info}


def compare_and_score(state: MatchState) -> dict:
    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", MATCH_SYSTEM_PROMPT),
            ("human", MATCH_USER_PROMPT),
        ]
    )
    chain = prompt | llm | JsonOutputParser()
    result = chain.invoke(
        {
            "jd_text": state["jd_text"],
            "resume_text": state["resume_text"],
        }
    )
    if not isinstance(result, dict):
        return {
            "match_percentage": 0,
            "strengths": [],
            "gaps": [],
            "suggestions": [],
        }
    return {
        "match_percentage": result.get("match_percentage", 0),
        "strengths": result.get("strengths", []),
        "gaps": result.get("gaps", []),
        "suggestions": result.get("suggestions", []),
    }


def generate_suggestions(state: MatchState) -> dict:
    return {}


def build_match_graph():
    from langgraph.graph import StateGraph, END

    graph = StateGraph(MatchState)
    graph.add_node("extract_jd", extract_jd_requirements)
    graph.add_node("extract_resume", extract_resume_info)
    graph.add_node("compare", compare_and_score)
    graph.add_node("suggest", generate_suggestions)

    graph.set_entry_point("extract_jd")
    graph.add_edge("extract_jd", "extract_resume")
    graph.add_edge("extract_resume", "compare")
    graph.add_edge("compare", "suggest")
    graph.add_edge("suggest", END)

    return graph.compile()
