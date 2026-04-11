from __future__ import annotations

import json
import logging
import math
import time
from typing import Any

from sqlalchemy.orm import Session

from app.ai.llm import get_embedder
from app.config import settings
from app.db.models import ProfileEvidence


DEFAULT_USER_ID = "default-user"
TOP_K_DEFAULT = 5
EMBED_BATCH_SIZE = 32  # 批量嵌入每批大小
EMBED_RETRY_TIMES = 3  # 嵌入重试次数
EMBED_RETRY_DELAY = 1.0  # 重试间隔（秒）
VECTOR_DIMENSION = 2048  # embedding-3 向量维度，校验用

logger = logging.getLogger(__name__)

"""
Design: Vector Similarity Search for Profile Evidence
核心思想：利用 embeddings 对 ProfileEvidence 进行向量化存储和检索。
retrieve_similar_evidence 通过余弦相似度找到与查询最相关的证据。
当 embedding 不可用时，降级为基于关键词重叠的文本相似度 heuristic。
embed_evidence_texts 批量为已有证据生成并存储向量。

向量存储抽象层：
- use_pgvector=False（默认，SQLite）：向量存于 metadata_json["embedding_{id}"]，兼容性最佳
- use_pgvector=True（PostgreSQL+pgvector）：向量存于 ProfileEvidence.vector 列，
  可利用 HNSW/IVF 索引加速检索，检索时优先使用 SQL 向量操作符（<=>）
"""


# ============================================================================
# 向量存储抽象层
# ============================================================================

def _store_vector(record: ProfileEvidence, vec: list[float]) -> None:
    """
    将向量存储到记录中。
    use_pgvector=True 时写入 vector 列（pgvector 迁移后使用），
    当前统一使用 metadata_json 存储。
    """
    if settings.use_pgvector:
        record.vector = vec
    else:
        metadata = dict(record.metadata_json or {})
        metadata[f"embedding_{record.id}"] = vec
        record.metadata_json = metadata


def _get_vector(record: ProfileEvidence) -> list[float] | None:
    """
    从记录中读取向量。
    use_pgvector=True 时读取 vector 列，当前读取 metadata_json。
    """
    if settings.use_pgvector:
        return _to_embedding(record.vector)
    else:
        emb_key = f"embedding_{record.id}"
        return _to_embedding((record.metadata_json or {}).get(emb_key))


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


def _validate_vector(vec: list[float], expected_dim: int = VECTOR_DIMENSION) -> bool:
    """校验向量维度是否与预期一致，不一致则记录警告并返回 False。"""
    if len(vec) != expected_dim:
        logger.warning(
            f"向量维度不匹配: 期望 {expected_dim}, 实际 {len(vec)}"
        )
        return False
    return True


def _cosine_sim(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        logger.warning(f"向量长度不一致: {len(a)} vs {len(b)}，返回 0")
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _embed_with_retry(texts: list[str], embedder, max_retries: int = EMBED_RETRY_TIMES) -> list[list[float] | None]:
    """
    批量调用 embed_documents，带重试逻辑。
    返回与输入顺序对应的向量列表，失败项为 None。
    """
    for attempt in range(max_retries):
        try:
            return embedder.embed_documents(texts)
        except Exception as e:
            logger.warning(f"批量嵌入失败（第 {attempt + 1}/{max_retries} 次）: {e}")
            if attempt < max_retries - 1:
                time.sleep(EMBED_RETRY_DELAY * (attempt + 1))
            else:
                logger.error(f"批量嵌入最终失败，已达最大重试次数 {max_retries}")
                return [None] * len(texts)
    return [None] * len(texts)


def embed_evidence_texts(db: Session, *, user_id: str = DEFAULT_USER_ID) -> int:
    """
    批量为尚未嵌入的 ProfileEvidence 记录生成并存储向量。
    使用 embed_documents 批量 API 减少 HTTP 开销，失败项带重试。
    Returns the count of records processed.
    """
    embedder = get_embedder()

    records = (
        db.query(ProfileEvidence)
        .filter(ProfileEvidence.user_id == user_id)
        .order_by(ProfileEvidence.event_time.desc())
        .all()
    )

    # 收集需要嵌入的记录
    to_embed: list[tuple[ProfileEvidence, str]] = []
    for record in records:
        # 检查向量是否已存在（根据存储后端选择正确的列）
        if settings.use_pgvector:
            if record.vector is not None:
                continue
        else:
            key = f"embedding_{record.id}"
            if key in (record.metadata_json or {}):
                continue
        text = record.quote_text or ""
        if not text.strip():
            continue
        to_embed.append((record, text))

    if not to_embed:
        return 0

    # 批量嵌入，分批处理避免单次请求过大
    count = 0
    for i in range(0, len(to_embed), EMBED_BATCH_SIZE):
        batch = to_embed[i:i + EMBED_BATCH_SIZE]
        texts = [t for _, t in batch]

        vectors = _embed_with_retry(texts, embedder)

        for (record, _), vec in zip(batch, vectors):
            if vec is None:
                continue
            if not _validate_vector(vec):
                continue
            _store_vector(record, vec)
            count += 1

    if count > 0:
        db.commit()
        logger.info(f"成功嵌入 {count} 条 ProfileEvidence 记录（user={user_id}）")

    return count


def _embed_query_with_retry(query_text: str, embedder, max_retries: int = EMBED_RETRY_TIMES) -> list[float] | None:
    """Query 向量生成，带重试。"""
    for attempt in range(max_retries):
        try:
            return embedder.embed_query(query_text)
        except Exception as e:
            logger.warning(f"Query 嵌入失败（第 {attempt + 1}/{max_retries} 次）: {e}")
            if attempt < max_retries - 1:
                time.sleep(EMBED_RETRY_DELAY * (attempt + 1))
            else:
                logger.error(f"Query 嵌入最终失败: {e}")
                return None
    return None


def _rerank_candidates(
    candidates: list[tuple[float, ProfileEvidence]],
    query_text: str,
    embedder,
    top_k: int,
    min_score: float = 0.3,
) -> list[dict[str, Any]]:
    """
    ReRank 步骤：对粗筛结果进行二次精排。
    综合余弦相似度、文本相关性和置信度进行打分。
    """
    if not candidates:
        return []

    # 取 2 倍 top_k 做重排（留足余量）
    rerank_pool = candidates[:top_k * 2]

    # 计算每个候选的综合得分
    scored: list[tuple[float, ProfileEvidence]] = []
    for sim_score, record in rerank_pool:
        # 文本相似度（词重叠）
        text_sim = _text_similarity_heuristic(query_text, record.quote_text)
        # 置信度归一化（0-1）
        conf_norm = record.confidence / 100.0
        # 综合得分：余弦相似度为主，文本相关性为辅，置信度加权
        # 权重分配：sim=0.7, text_sim=0.2, confidence=0.1
        final_score = 0.7 * sim_score + 0.2 * text_sim + 0.1 * conf_norm
        scored.append((final_score, record))

    scored.sort(key=lambda item: item[0], reverse=True)

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
            "similarity_score": round(sim, 4),
        }
        for sim, r in scored[:top_k]
    ]


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
    向量相似度检索，支持：
    - SQL 层面 dimension 过滤（利用索引）
    - Query 向量生成重试
    - 无向量时降级到词重叠 heuristic
    - ReRank 精排提升相关性
    """
    embedder = get_embedder()

    query_vec = _embed_query_with_retry(query_text, embedder)
    if query_vec is None:
        return _fallback_retrieve(
            db, user_id=user_id, dimension_filter=dimension_filter, top_k=top_k
        )

    if not _validate_vector(query_vec):
        return _fallback_retrieve(
            db, user_id=user_id, dimension_filter=dimension_filter, top_k=top_k
        )

    # SQL 层面先按 dimension 过滤，减少加载数据量（利用 ix_profile_evidence_user_dimension 索引）
    query = db.query(ProfileEvidence).filter(ProfileEvidence.user_id == user_id)
    if dimension_filter:
        query = query.filter(ProfileEvidence.dimension == dimension_filter)
    records = query.order_by(ProfileEvidence.event_time.desc()).all()

    candidates: list[tuple[float, ProfileEvidence]] = []
    for record in records:
        stored_vec = _get_vector(record)
        if stored_vec is None:
            text_sim = _text_similarity_heuristic(query_text, record.quote_text)
            if text_sim >= min_score:
                candidates.append((text_sim, record))
            continue

        score = _cosine_sim(query_vec, stored_vec)
        if score >= min_score:
            candidates.append((score, record))

    candidates.sort(key=lambda item: item[0], reverse=True)

    # 粗筛结果超过 top_k 时进行 ReRank 精排
    if len(candidates) > top_k:
        return _rerank_candidates(candidates, query_text, embedder, top_k, min_score)

    # 候选不足 top_k，直接返回（但仍附加 similarity_score）
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
            "similarity_score": round(sim, 4),
        }
        for sim, r in candidates[:top_k]
    ]


def _fallback_retrieve(
    db: Session,
    *,
    user_id: str,
    dimension_filter: str | None,
    top_k: int,
) -> list[dict[str, Any]]:
    """降级检索：SQL 层面过滤，无向量参与，返回词重叠分数作为相似度。"""
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
            "similarity_score": None,  # 无向量，无法计算余弦相似度
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
