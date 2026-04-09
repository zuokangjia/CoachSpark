from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.persona_v2_service import (
    get_latest_persona,
    rebuild_persona_snapshot,
    explain_dimension,
    list_snapshots,
    compare_snapshots,
)
from app.services.rag_retrieval_service import (
    retrieve_similar_evidence,
    embed_evidence_texts,
)

router = APIRouter(prefix="/persona", tags=["persona-v2"])


@router.get("/latest")
def latest(db: Session = Depends(get_db)):
    return get_latest_persona(db)


@router.post("/rebuild")
def rebuild(db: Session = Depends(get_db)):
    return rebuild_persona_snapshot(db)


@router.get("/explain")
def explain(
    dimension: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    return explain_dimension(db, dimension=dimension, limit=limit)


@router.get("/snapshots")
def snapshots(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return list_snapshots(db, limit=limit)


@router.get("/compare")
def compare(
    base_snapshot_id: str = Query(..., min_length=1),
    target_snapshot_id: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    return compare_snapshots(
        db,
        base_snapshot_id=base_snapshot_id,
        target_snapshot_id=target_snapshot_id,
    )


@router.get("/retrieve")
def retrieve(
    q: str = Query(..., min_length=1),
    dimension: str | None = None,
    top_k: int = Query(5, ge=1, le=20),
    min_score: float = Query(0.3, ge=0.0, le=1.0),
    db: Session = Depends(get_db),
):
    return {
        "results": retrieve_similar_evidence(
            db,
            query_text=q,
            dimension_filter=dimension,
            top_k=top_k,
            min_score=min_score,
        )
    }


@router.post("/embed-evidence")
def embed_evidence(db: Session = Depends(get_db)):
    count = embed_evidence_texts(db)
    return {"embedded": count}
