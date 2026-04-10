from __future__ import annotations

import json
import math
from typing import Any

from sqlalchemy.orm import Session

from app.ai.llm import get_embedder
from app.db.models import ProfileEvidence, generate_uuid


DEFAULT_USER_ID = "default-user"
TOP_K_DEFAULT = 5

"""
Design: Vector Similarity Search for Profile Evidence
核心思想：利用 embeddings 对 ProfileEvidence 进行向量化存储和检索。
retrieve_similar_evidence 通过余弦相似度找到与查询最相关的证据。
当 embedding 不可用时，降级为基于关键词重叠的文本相似度 heuristic。
embed_evidence_texts 批量为已有证据生成并存储向量。
"""


def _to_embedding(value: Any) -> list[float] | None:
    if value is None:
        return None
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass
    if isinstance(value, list):
        return value
    return None


def _cosine_sim(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def embed_evidence_texts(db: Session, *, user_id: str = DEFAULT_USER_ID) -> int:
    """
    Generate and store embeddings for all evidence records that don't yet have one.
    Returns the count of records processed.
    """
    embedder = get_embedder()

    records = (
        db.query(ProfileEvidence)
        .filter(ProfileEvidence.user_id == user_id)
        .order_by(ProfileEvidence.event_time.desc())
        .all()
    )

    count = 0
    for record in records:
        key = f"embedding_{record.id}"
        if key in (record.metadata_json or {}):
            continue

        text = record.quote_text or ""
        if not text.strip():
            continue

        try:
            vec = embedder.embed_query(text)
        except Exception:
            continue

        metadata = dict(record.metadata_json or {})
        metadata[key] = vec
        record.metadata_json = metadata
        count += 1

    if count > 0:
        db.commit()

    return count


def retrieve_similar_evidence(
    db: Session,
    *,
    query_text: str,
    user_id: str = DEFAULT_USER_ID,
    dimension_filter: str | None = None,
    top_k: int = TOP_K_DEFAULT,
    min_score: float = 0.3,
) -> list[dict[str, Any]]:
    """
    Vector similarity search over profile evidence.
    Falls back to dimension-filtered retrieval when query embedding is unavailable.
    """
    embedder = get_embedder()

    try:
        query_vec = embedder.embed_query(query_text)
    except Exception:
        return _fallback_retrieve(
            db, user_id=user_id, dimension_filter=dimension_filter, top_k=top_k
        )

    records = (
        db.query(ProfileEvidence)
        .filter(ProfileEvidence.user_id == user_id)
        .order_by(ProfileEvidence.event_time.desc())
        .all()
    )

    candidates: list[tuple[float, ProfileEvidence]] = []
    for record in records:
        if dimension_filter and record.dimension != dimension_filter:
            continue

        emb_key = f"embedding_{record.id}"
        stored_vec = (record.metadata_json or {}).get(emb_key)
        if stored_vec is None:
            text_sim = _text_similarity_heuristic(query_text, record.quote_text)
            if text_sim >= min_score:
                candidates.append((text_sim, record))
            continue

        vec = _to_embedding(stored_vec)
        if vec is None:
            continue

        score = _cosine_sim(query_vec, vec)
        if score >= min_score:
            candidates.append((score, record))

    candidates.sort(key=lambda item: item[0], reverse=True)
    return [
        {
            "id": r.id,
            "dimension": r.dimension,
            "signal_type": r.signal_type,
            "score": r.score,
            "confidence": r.confidence,
            "quote_text": r.quote_text,
            "event_time": r.event_time.isoformat() if r.event_time else None,
            "source_type": r.source_type,
        }
        for _, r in candidates[:top_k]
    ]


def _fallback_retrieve(
    db: Session,
    *,
    user_id: str,
    dimension_filter: str | None,
    top_k: int,
) -> list[dict[str, Any]]:
    query = db.query(ProfileEvidence).filter(ProfileEvidence.user_id == user_id)
    if dimension_filter:
        query = query.filter(ProfileEvidence.dimension == dimension_filter)
    rows = query.order_by(ProfileEvidence.event_time.desc()).limit(top_k).all()
    return [
        {
            "id": r.id,
            "dimension": r.dimension,
            "signal_type": r.signal_type,
            "score": r.score,
            "confidence": r.confidence,
            "quote_text": r.quote_text,
            "event_time": r.event_time.isoformat() if r.event_time else None,
            "source_type": r.source_type,
        }
        for r in rows
    ]


def _text_similarity_heuristic(query: str, text: str) -> float:
    if not query or not text:
        return 0.0
    q_words = set(query.lower().split())
    t_words = set(text.lower().split())
    if not q_words:
        return 0.0
    overlap = len(q_words & t_words)
    return overlap / len(q_words)
