from app.ai.graphs.prep_graph import build_prep_graph

_prep_graph = None


def get_prep_graph():
    global _prep_graph
    if _prep_graph is None:
        _prep_graph = build_prep_graph()
    return _prep_graph


def generate_prep_plan(
    company_id: str,
    target_round: int,
    days_available: int,
    weak_points: list = None,
    jd_directions: list = None,
    interview_chain: list = None,
) -> dict:
    graph = get_prep_graph()
    result = graph.invoke(
        {
            "company_id": company_id,
            "target_round": target_round,
            "days_available": days_available,
            "weak_points": weak_points or [],
            "jd_directions": jd_directions or [],
            "interview_chain": interview_chain or [],
            "daily_tasks": [],
        }
    )
    return {
        "daily_tasks": result.get("daily_tasks", []),
    }
