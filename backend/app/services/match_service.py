from app.ai.graphs.match_graph import build_match_graph

_match_graph = None


def get_match_graph():
    global _match_graph
    if _match_graph is None:
        _match_graph = build_match_graph()
    return _match_graph


def analyze_match(jd_text: str, resume_text: str) -> dict:
    graph = get_match_graph()
    result = graph.invoke(
        {
            "jd_text": jd_text,
            "resume_text": resume_text,
            "jd_requirements": [],
            "resume_info": [],
            "match_percentage": 0,
            "strengths": [],
            "gaps": [],
            "suggestions": [],
        }
    )
    return {
        "match_percentage": result.get("match_percentage", 0),
        "strengths": result.get("strengths", []),
        "gaps": result.get("gaps", []),
        "suggestions": result.get("suggestions", []),
    }
