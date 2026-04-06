from typing import TypedDict, List, Optional
import logging

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from app.ai.llm import get_llm
from app.ai.prompts.match import MATCH_SYSTEM_PROMPT, MATCH_USER_PROMPT

logger = logging.getLogger("coachspark")


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
                "从以下岗位描述中提取核心技术要求和资格条件。返回 JSON 字符串数组，每条是一个具体的技术要求或条件。使用中文。",
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
                "从以下简历中提取候选人的核心技能、经验和资质。返回 JSON 字符串数组，每条是一个具体的技能或经历。使用中文。",
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
    gaps = state.get("gaps", [])
    strengths = state.get("strengths", [])
    existing_suggestions = state.get("suggestions", [])

    if not gaps:
        return (
            {"suggestions": existing_suggestions}
            if existing_suggestions
            else {"suggestions": ["你的背景与岗位高度匹配，可以直接投递"]}
        )

    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是资深技术招聘官。基于候选人的简历与岗位描述的差距分析，生成具体的投递建议。区分短期可执行（1-2 周内）和长期提升两类建议。返回 JSON 字符串数组。使用中文。",
            ),
            (
                "human",
                "优势：\n{strengths}\n\n差距：\n{gaps}\n\n已有建议：\n{existing}",
            ),
        ]
    )
    chain = prompt | llm | JsonOutputParser()
    try:
        result = chain.invoke(
            {
                "strengths": "\n".join(f"- {s}" for s in strengths),
                "gaps": "\n".join(f"- {g}" for g in gaps),
                "existing": "\n".join(f"- {s}" for s in existing_suggestions),
            }
        )
        suggestions = result if isinstance(result, list) else existing_suggestions
    except Exception as exc:
        logger.warning("generate_suggestions LLM call failed: %s", exc)
        suggestions = existing_suggestions

    return {"suggestions": suggestions}


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
