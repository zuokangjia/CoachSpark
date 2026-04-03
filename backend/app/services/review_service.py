from app.ai.graphs.review_graph import build_review_graph

_review_graph = None


def get_review_graph():
    global _review_graph
    if _review_graph is None:
        _review_graph = build_review_graph()
    return _review_graph


def analyze_review(
    raw_notes: str,
    company_name: str = "",
    position: str = "",
    round_num: int = 1,
    jd_key_points: list = None,
) -> dict:
    graph = get_review_graph()
    result = graph.invoke(
        {
            "raw_notes": raw_notes,
            "company_name": company_name,
            "position": position,
            "round_num": round_num,
            "jd_key_points": jd_key_points or [],
            "questions": [],
            "weak_points": [],
            "strong_points": [],
            "next_round_prediction": [],
            "interviewer_signals": [],
            "analysis_complete": False,
        }
    )
    return {
        "questions": result.get("questions", []),
        "weak_points": result.get("weak_points", []),
        "strong_points": result.get("strong_points", []),
        "next_round_prediction": result.get("next_round_prediction", []),
        "interviewer_signals": result.get("interviewer_signals", []),
    }
