from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import (
    ProfileEvidence,
    UserProfileSnapshot,
    UserSkillState,
    generate_uuid,
)
from app.services.rag_retrieval_service import retrieve_similar_evidence


DEFAULT_USER_ID = "default-user"

"""
Design: Evidence-Driven Persona System
核心思想：每次面试复盘生成证据（weak/strong points），证据累积计算技能状态
(level/trend/confidence)，定期生成快照支持历史对比和RAG增强的解释。
"""


def ingest_review_evidence(
    db: Session,
    *,
    user_id: str = DEFAULT_USER_ID,
    interview_id: str,
    round_num: int,
    analysis: dict[str, Any],
    raw_notes: str,
) -> list[ProfileEvidence]:
    evidence_items: list[ProfileEvidence] = []
    event_time = datetime.now(timezone.utc).replace(tzinfo=None)

    for wp in analysis.get("weak_points", []) or []:
        evidence_items.append(
            ProfileEvidence(
                id=generate_uuid(),
                user_id=user_id,
                source_type="interview",
                source_id=interview_id,
                dimension=str(wp),
                signal_type="weakness",
                polarity=-1,
                score=_infer_weakness_score(analysis),
                confidence=75,
                round_no=round_num,
                quote_text=_safe_quote(raw_notes),
                metadata_json={"from": "weak_points"},
                event_time=event_time,
            )
        )

    for sp in analysis.get("strong_points", []) or []:
        evidence_items.append(
            ProfileEvidence(
                id=generate_uuid(),
                user_id=user_id,
                source_type="interview",
                source_id=interview_id,
                dimension=str(sp),
                signal_type="strength",
                polarity=1,
                score=_infer_strength_score(analysis),
                confidence=70,
                round_no=round_num,
                quote_text=_safe_quote(raw_notes),
                metadata_json={"from": "strong_points"},
                event_time=event_time,
            )
        )

    for item in evidence_items:
        db.add(item)

    if evidence_items:
        db.commit()

    return evidence_items


def rebuild_persona_snapshot(
    db: Session,
    *,
    user_id: str = DEFAULT_USER_ID,
    source_event_id: str | None = None,
) -> dict[str, Any]:
    evidences = (
        db.query(ProfileEvidence)
        .filter(ProfileEvidence.user_id == user_id)
        .order_by(ProfileEvidence.event_time.desc())
        .all()
    )

    grouped: dict[str, list[ProfileEvidence]] = {}
    for ev in evidences:
        grouped.setdefault(ev.dimension, []).append(ev)

    states: list[dict[str, Any]] = []
    for dimension, items in grouped.items():
        level = _calc_level(items)
        trend = _calc_trend(items)
        confidence = _calc_confidence(items)
        evidence_count = len(items)

        existing = (
            db.query(UserSkillState)
            .filter(
                UserSkillState.user_id == user_id,
                UserSkillState.dimension == dimension,
            )
            .first()
        )
        if existing:
            existing.level = level
            existing.trend = trend
            existing.confidence = confidence
            existing.evidence_count = evidence_count
        else:
            db.add(
                UserSkillState(
                    id=generate_uuid(),
                    user_id=user_id,
                    dimension=dimension,
                    level=level,
                    trend=trend,
                    confidence=confidence,
                    evidence_count=evidence_count,
                )
            )

        states.append(
            {
                "dimension": dimension,
                "level": level,
                "trend": trend,
                "confidence": confidence,
                "evidence_count": evidence_count,
            }
        )

    top_strengths = [
        s["dimension"]
        for s in sorted(states, key=lambda x: x["level"], reverse=True)[:3]
        if s["level"] >= 3
    ]
    top_weaknesses = [
        s["dimension"]
        for s in sorted(states, key=lambda x: x["level"])[:3]
        if s["level"] <= 3
    ]

    headline_parts: list[str] = []
    if states:
        headline_parts.append(
            f"已累计分析 {sum(s['evidence_count'] for s in states)} 条画像证据"
        )
    if top_strengths:
        headline_parts.append(f"优势倾向：{', '.join(top_strengths[:2])}")
    if top_weaknesses:
        headline_parts.append(f"短板倾向：{', '.join(top_weaknesses[:2])}")

    summary = {
        "headline": "；".join(headline_parts)
        if headline_parts
        else "暂无足够证据生成画像",
        "dimensions": sorted(
            states, key=lambda x: (-x["evidence_count"], -x["confidence"])
        ),
        "key_strengths": top_strengths,
        "key_weaknesses": top_weaknesses,
        "action_suggestions": _build_actions(top_weaknesses),
    }

    snapshot = UserProfileSnapshot(
        id=generate_uuid(),
        user_id=user_id,
        version="v2",
        headline=summary["headline"],
        summary=summary,
        generated_at=datetime.utcnow(),
        source_event_id=source_event_id,
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)

    return {
        "snapshot_id": snapshot.id,
        "version": snapshot.version,
        "generated_at": snapshot.generated_at.isoformat(),
        **summary,
    }


def get_latest_persona(
    db: Session, *, user_id: str = DEFAULT_USER_ID
) -> dict[str, Any]:
    latest = (
        db.query(UserProfileSnapshot)
        .filter(UserProfileSnapshot.user_id == user_id)
        .order_by(UserProfileSnapshot.generated_at.desc())
        .first()
    )
    if not latest:
        return rebuild_persona_snapshot(db, user_id=user_id)

    payload = latest.summary if isinstance(latest.summary, dict) else {}
    return {
        "snapshot_id": latest.id,
        "version": latest.version,
        "generated_at": latest.generated_at.isoformat(),
        **payload,
    }


def explain_dimension(
    db: Session,
    *,
    dimension: str,
    user_id: str = DEFAULT_USER_ID,
    limit: int = 10,
) -> dict[str, Any]:
    states = (
        db.query(UserSkillState)
        .filter(
            UserSkillState.user_id == user_id, UserSkillState.dimension == dimension
        )
        .first()
    )
    rag_results = retrieve_similar_evidence(
        db,
        query_text=dimension,
        user_id=user_id,
        dimension_filter=dimension,
        top_k=limit,
        min_score=0.1,
    )

    return {
        "dimension": dimension,
        "level": states.level if states else 0,
        "trend": states.trend if states else "new",
        "confidence": states.confidence if states else 0,
        "evidence": rag_results,
    }


def list_snapshots(
    db: Session,
    *,
    user_id: str = DEFAULT_USER_ID,
    limit: int = 20,
) -> dict[str, Any]:
    rows = (
        db.query(UserProfileSnapshot)
        .filter(UserProfileSnapshot.user_id == user_id)
        .order_by(UserProfileSnapshot.generated_at.desc())
        .limit(limit)
        .all()
    )
    return {
        "items": [
            {
                "snapshot_id": r.id,
                "version": r.version,
                "headline": r.headline,
                "generated_at": r.generated_at.isoformat() if r.generated_at else None,
                "source_event_id": r.source_event_id,
            }
            for r in rows
        ]
    }


def compare_snapshots(
    db: Session,
    *,
    base_snapshot_id: str,
    target_snapshot_id: str,
    user_id: str = DEFAULT_USER_ID,
) -> dict[str, Any]:
    base = (
        db.query(UserProfileSnapshot)
        .filter(
            UserProfileSnapshot.id == base_snapshot_id,
            UserProfileSnapshot.user_id == user_id,
        )
        .first()
    )
    target = (
        db.query(UserProfileSnapshot)
        .filter(
            UserProfileSnapshot.id == target_snapshot_id,
            UserProfileSnapshot.user_id == user_id,
        )
        .first()
    )

    if not base or not target:
        return {
            "base_snapshot_id": base_snapshot_id,
            "target_snapshot_id": target_snapshot_id,
            "changes": [],
            "summary": "快照不存在或不属于当前用户",
        }

    base_dimensions = _index_dimensions(base.summary)
    target_dimensions = _index_dimensions(target.summary)

    all_keys = sorted(set(base_dimensions.keys()) | set(target_dimensions.keys()))
    changes: list[dict[str, Any]] = []

    for key in all_keys:
        b = base_dimensions.get(key)
        t = target_dimensions.get(key)
        if not b and t:
            changes.append(
                {
                    "dimension": key,
                    "change_type": "added",
                    "base_level": None,
                    "target_level": t.get("level"),
                    "delta_level": None,
                    "base_confidence": None,
                    "target_confidence": t.get("confidence"),
                    "delta_confidence": None,
                }
            )
            continue
        if b and not t:
            changes.append(
                {
                    "dimension": key,
                    "change_type": "removed",
                    "base_level": b.get("level"),
                    "target_level": None,
                    "delta_level": None,
                    "base_confidence": b.get("confidence"),
                    "target_confidence": None,
                    "delta_confidence": None,
                }
            )
            continue

        delta_level = (t.get("level") or 0) - (b.get("level") or 0)
        delta_confidence = (t.get("confidence") or 0) - (b.get("confidence") or 0)
        if (
            delta_level != 0
            or delta_confidence != 0
            or t.get("trend") != b.get("trend")
        ):
            changes.append(
                {
                    "dimension": key,
                    "change_type": "updated",
                    "base_level": b.get("level"),
                    "target_level": t.get("level"),
                    "delta_level": delta_level,
                    "base_confidence": b.get("confidence"),
                    "target_confidence": t.get("confidence"),
                    "delta_confidence": delta_confidence,
                    "base_trend": b.get("trend"),
                    "target_trend": t.get("trend"),
                }
            )

    return {
        "base_snapshot_id": base.id,
        "target_snapshot_id": target.id,
        "base_generated_at": base.generated_at.isoformat()
        if base.generated_at
        else None,
        "target_generated_at": target.generated_at.isoformat()
        if target.generated_at
        else None,
        "base_headline": base.headline,
        "target_headline": target.headline,
        "changes": changes,
        "summary": f"共识别 {len(changes)} 项变化",
    }


def _index_dimensions(summary: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(summary, dict):
        return {}
    dimensions = summary.get("dimensions", [])
    if not isinstance(dimensions, list):
        return {}
    indexed: dict[str, dict[str, Any]] = {}
    for item in dimensions:
        if not isinstance(item, dict):
            continue
        key = str(item.get("dimension", "")).strip()
        if not key:
            continue
        indexed[key] = item
    return indexed


def _infer_weakness_score(analysis: dict[str, Any]) -> int:
    question_scores = [
        q.get("score")
        for q in analysis.get("questions", [])
        if isinstance(q, dict) and isinstance(q.get("score"), int)
    ]
    if not question_scores:
        return 4
    return max(1, min(10, int(round(sum(question_scores) / len(question_scores))) - 2))


def _infer_strength_score(analysis: dict[str, Any]) -> int:
    question_scores = [
        q.get("score")
        for q in analysis.get("questions", [])
        if isinstance(q, dict) and isinstance(q.get("score"), int)
    ]
    if not question_scores:
        return 7
    return max(1, min(10, int(round(sum(question_scores) / len(question_scores))) + 1))


def _safe_quote(raw_notes: str, max_len: int = 180) -> str:
    text = (raw_notes or "").strip()
    if not text:
        return "(无原始摘录)"
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


def _calc_level(items: list[ProfileEvidence]) -> int:
    if not items:
        return 1
    weighted_total = sum((ev.score or 0) * max(ev.confidence, 1) for ev in items)
    weight_sum = sum(max(ev.confidence, 1) for ev in items)
    base = weighted_total / weight_sum if weight_sum else 0
    level = int(round(base / 2))
    return max(1, min(5, level))


def _calc_trend(items: list[ProfileEvidence]) -> str:
    if len(items) < 2:
        return "new"
    recent = items[:2]
    historical = items[2:]
    recent_avg = sum(ev.score for ev in recent) / len(recent)
    historical_avg = (
        sum(ev.score for ev in historical) / len(historical)
        if historical
        else recent_avg
    )
    if recent_avg >= historical_avg + 1:
        return "up"
    if recent_avg <= historical_avg - 1:
        return "down"
    return "stable"


def _calc_confidence(items: list[ProfileEvidence]) -> int:
    if not items:
        return 0
    base = sum(ev.confidence for ev in items) / len(items)
    bonus = min(20, len(items) * 3)
    return int(max(0, min(100, base + bonus)))


def _build_actions(weaknesses: list[str]) -> list[str]:
    actions: list[str] = []
    if weaknesses:
        actions.append(f"针对「{weaknesses[0]}」准备三段式回答模板并录音复盘")
    if len(weaknesses) > 1:
        actions.append(f"把「{weaknesses[1]}」拆成 5 道高频追问逐条演练")
    if not actions:
        actions.append("继续积累面试复盘证据，提升画像稳定性")
    return actions
