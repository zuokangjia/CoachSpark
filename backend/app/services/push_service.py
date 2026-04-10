"""
Design: Smart Push Notification System
核心思想：
- 面试前自动生成备战简报并推送，解决"考前不知道复习什么"的问题
- 投递过期自动检测并提醒，避免简历石沉大海
- 支持 Webhook 通道（钉钉/企业微信/飞书），配置灵活
- 通知记录持久化，支持重试和状态追踪
"""
from datetime import date, datetime, timedelta, timezone
from typing import Optional
import httpx

from sqlalchemy.orm import Session

from app.db.models import Notification, Company, Interview, PrepPlan, generate_uuid
from app.config import settings


# ---------------------------------------------------------------------------
# Channel: Webhook Sender
# ---------------------------------------------------------------------------

def send_webhook(url: str, title: str, content: str) -> tuple[bool, str]:
    """发送 Webhook 消息，返回 (success, error_msg)。"""
    if not url:
        return False, "webhook url is empty"
    try:
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "content": f"**{title}**\n\n{content}",
            },
        }
        with httpx.Client(timeout=10) as client:
            resp = client.post(url, json=payload)
            if resp.status_code < 400:
                return True, ""
            return False, f"http {resp.status_code}: {resp.text[:200]}"
    except Exception as e:
        return False, str(e)


# ---------------------------------------------------------------------------
# Briefing Generation
# ---------------------------------------------------------------------------

def generate_interview_briefing(db: Session, interview_id: str) -> dict:
    """生成面试备战简报内容。"""
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        return {"title": "", "content": ""}

    company = db.query(Company).filter(Company.id == interview.company_id).first()
    company_name = company.name if company else "未知公司"
    position = company.position if company else "未知岗位"

    # 获取最新备战计划
    prep_plan = (
        db.query(PrepPlan)
        .filter(PrepPlan.company_id == interview.company_id)
        .order_by(PrepPlan.created_at.desc())
        .first()
    )

    brief_lines = [f"📋 公司：{company_name} | 岗位：{position} | 第 {interview.round} 轮"]
    if interview.interview_date:
        brief_lines.append(f"📅 时间：{interview.interview_date}（{position}）")
    if interview.format:
        brief_lines.append(f"🖥 形式：{interview.format}")
    if interview.interviewer:
        brief_lines.append(f"👤 面试官：{interview.interviewer}")

    brief_lines.append("")
    brief_lines.append("## 🎯 本轮备战重点")

    analysis = interview.ai_analysis if isinstance(interview.ai_analysis, dict) else {}
    weak_points = analysis.get("weak_points", [])
    if weak_points:
        for wp in weak_points[:3]:
            brief_lines.append(f"- 【薄弱】{wp}")
    else:
        brief_lines.append("- 暂无复盘数据，建议回顾 JD 关键词")

    strong_points = analysis.get("strong_points", [])
    if strong_points:
        brief_lines.append("")
        brief_lines.append("## 💪 保持优势")
        for sp in strong_points[:2]:
            brief_lines.append(f"- {sp}")

    # 从备战计划提取当日任务
    if prep_plan and isinstance(prep_plan.daily_tasks, list):
        brief_lines.append("")
        brief_lines.append("## 📝 备战任务")
        for day in prep_plan.daily_tasks[:2]:
            if isinstance(day, dict):
                focus = day.get("focus", "第 {} 天".format(day.get("day", "?")))
                brief_lines.append(f"**{focus}**")
                for task in (day.get("tasks", [])[:2] or []):
                    brief_lines.append(f"- {task}")
                brief_lines.append("")

    next_round = analysis.get("next_round_prediction", [])
    if next_round:
        brief_lines.append("## 🔮 可能的追问方向")
        for pred in next_round[:3]:
            brief_lines.append(f"- {pred}")

    return {
        "title": f"面试提醒 | {company_name} 第 {interview.round} 轮",
        "content": "\n".join(brief_lines),
    }


# ---------------------------------------------------------------------------
# Notification Scheduling
# ---------------------------------------------------------------------------

def schedule_interview_reminder(
    db: Session,
    interview_id: str,
    remind_before_hours: int = 2,
    webhook_url: Optional[str] = None,
) -> Notification:
    """为面试创建提醒通知（默认考前2小时）。"""
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview or not interview.interview_date:
        raise ValueError("interview not found or has no date")

    briefing = generate_interview_briefing(db, interview_id)
    # 面试前 remind_before_hours 发送
    scheduled = datetime.combine(
        interview.interview_date, datetime.min.time()
    ) - timedelta(hours=remind_before_hours)

    notif = Notification(
        id=generate_uuid(),
        notif_type="interview_reminder",
        channel="webhook" if webhook_url else "email",
        status="pending",
        title=briefing["title"],
        content=briefing["content"],
        target_id=interview_id,
        scheduled_at=scheduled,
        webhook_url=webhook_url,
        metadata_json={"remind_before_hours": remind_before_hours},
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif


def create_stale_alerts(db: Session, webhook_url: Optional[str] = None) -> list[Notification]:
    """
    检测所有 next_event_date 已过但仍处于 applied 状态的投递，
    为每个创建 stale_alert 通知。
    """
    today = date.today()
    stale_companies = (
        db.query(Company)
        .filter(
            Company.status == "applied",
            Company.next_event_date.isnot(None),
            Company.next_event_date < today,
        )
        .all()
    )

    notifications = []
    for company in stale_companies:
        days_overdue = (today - company.next_event_date).days
        content_lines = [
            f"**投递提醒 | {company.name}**",
            f"",
            f"📋 岗位：{company.position}",
            f"⏰ 原定跟进日期：{company.next_event_date}（已逾期 **{days_overdue} 天**）",
            f"",
            f"建议：",
            f"1. 更新进度或标记结果",
            f"2. 补充面试反馈到系统中",
            f"3. 若已拒绝，可将状态更新为 rejected",
        ]
        notif = Notification(
            id=generate_uuid(),
            notif_type="stale_alert",
            channel="webhook" if webhook_url else "email",
            status="pending",
            title=f"投递逾期提醒 | {company.name}",
            content="\n".join(content_lines),
            target_id=company.id,
            scheduled_at=datetime.utcnow(),
            webhook_url=webhook_url,
            metadata_json={"days_overdue": days_overdue},
        )
        db.add(notif)
        notifications.append(notif)

    if notifications:
        db.commit()
    return notifications


# ---------------------------------------------------------------------------
# Notification Dispatcher（可由 CRON 定时调用）
# ---------------------------------------------------------------------------

def dispatch_due_notifications(db: Session) -> dict:
    """
    扫描所有 scheduled_at <= now 且 status=pending 的通知，逐一发送。
    返回发送结果统计。
    """
    now = datetime.utcnow()
    due = (
        db.query(Notification)
        .filter(
            Notification.status == "pending",
            Notification.scheduled_at.isnot(None),
            Notification.scheduled_at <= now,
        )
        .all()
    )

    sent, failed = 0, 0
    for notif in due:
        if not notif.webhook_url:
            notif.status = "failed"
            notif.error_msg = "no webhook url configured"
            failed += 1
            continue

        ok, err = send_webhook(notif.webhook_url, notif.title, notif.content)
        if ok:
            notif.status = "sent"
            notif.sent_at = datetime.utcnow()
            sent += 1
        else:
            notif.status = "failed"
            notif.error_msg = err[:500]
            failed += 1

    db.commit()
    return {"total": len(due), "sent": sent, "failed": failed}


# ---------------------------------------------------------------------------
# Query Helpers
# ---------------------------------------------------------------------------

def get_pending_notifications(db: Session, limit: int = 50) -> list[Notification]:
    return (
        db.query(Notification)
        .filter(Notification.status == "pending")
        .order_by(Notification.scheduled_at.asc())
        .limit(limit)
        .all()
    )


def get_notification_history(
    db: Session, limit: int = 50, offset: int = 0
) -> list[Notification]:
    return (
        db.query(Notification)
        .order_by(Notification.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
