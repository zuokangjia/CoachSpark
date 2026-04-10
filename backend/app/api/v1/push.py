"""
Design: Push Notification API
提供推送通知的管理接口：
- POST 手动触发面试提醒（生成备战简报）
- POST 扫描并创建过期投递提醒
- POST 立即发送所有到期通知
- GET 查询通知历史和待发送队列
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import Notification
from app.services.push_service import (
    schedule_interview_reminder,
    create_stale_alerts,
    dispatch_due_notifications,
    get_pending_notifications,
    get_notification_history,
    generate_interview_briefing,
)


router = APIRouter(prefix="/push", tags=["push"])


class ScheduleReminderRequest:
    def __init__(
        self,
        interview_id: str,
        remind_before_hours: int = 2,
        webhook_url: Optional[str] = None,
    ):
        self.interview_id = interview_id
        self.remind_before_hours = remind_before_hours
        self.webhook_url = webhook_url


@router.post("/remind/{interview_id}")
def schedule_reminder(
    interview_id: str,
    remind_before_hours: int = Query(2, ge=1, le=72),
    webhook_url: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """为指定面试安排考前提醒（默认考前2小时）。"""
    try:
        notif = schedule_interview_reminder(
            db,
            interview_id=interview_id,
            remind_before_hours=remind_before_hours,
            webhook_url=webhook_url,
        )
        return {
            "notification_id": notif.id,
            "status": notif.status,
            "scheduled_at": notif.scheduled_at.isoformat() if notif.scheduled_at else None,
            "title": notif.title,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/scan-stale")
def scan_stale(
    webhook_url: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """扫描所有逾期未更新的投递，创建 stale_alert 提醒。"""
    alerts = create_stale_alerts(db, webhook_url=webhook_url)
    return {
        "created": len(alerts),
        "notifications": [
            {
                "id": n.id,
                "title": n.title,
                "target_id": n.target_id,
                "scheduled_at": n.scheduled_at.isoformat() if n.scheduled_at else None,
            }
            for n in alerts
        ],
    }


@router.post("/dispatch")
def dispatch_notifications(db: Session = Depends(get_db)):
    """
    立即发送所有到期的通知（scheduled_at <= now 且 status=pending）。
    可由 CRON 定时触发。
    """
    result = dispatch_due_notifications(db)
    return result


@router.get("/pending")
def list_pending(db: Session = Depends(get_db)):
    """查看当前待发送的通知队列。"""
    items = get_pending_notifications(db)
    return {
        "total": len(items),
        "items": [
            {
                "id": n.id,
                "type": n.notif_type,
                "channel": n.channel,
                "title": n.title,
                "scheduled_at": n.scheduled_at.isoformat() if n.scheduled_at else None,
                "target_id": n.target_id,
            }
            for n in items
        ],
    }


@router.get("/history")
def list_history(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """查询通知发送历史。"""
    items = get_notification_history(db, limit=limit, offset=offset)
    return {
        "total": len(items),
        "items": [
            {
                "id": n.id,
                "type": n.notif_type,
                "channel": n.channel,
                "status": n.status,
                "title": n.title,
                "sent_at": n.sent_at.isoformat() if n.sent_at else None,
                "error_msg": n.error_msg if n.status == "failed" else None,
                "created_at": n.created_at.isoformat(),
            }
            for n in items
        ],
    }


@router.get("/briefing/{interview_id}")
def preview_briefing(interview_id: str, db: Session = Depends(get_db)):
    """预览面试备战简报内容（不创建通知）。"""
    briefing = generate_interview_briefing(db, interview_id)
    if not briefing["title"]:
        raise HTTPException(status_code=404, detail="interview not found")
    return briefing
