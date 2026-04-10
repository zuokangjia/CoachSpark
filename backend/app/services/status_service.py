from datetime import date
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.db.models import Company, Offer, generate_uuid

"""
Design: Company Status State Machine
核心思想：公司的状态流转是严格受限的，只能沿着 applied -> interviewing -> passed/rejected
的路径单向移动。passed 状态自动触发 Offer 创建。拒绝状态不可逆。
通过 VALID_TRANSITIONS 字典声明所有合法转换，防止脏数据。
"""

VALID_TRANSITIONS = {
    "applied": ["interviewing"],
    "interviewing": ["passed", "rejected"],
    "passed": [],
    "rejected": [],
}


def transition_company_status(
    db: Session,
    company_id: str,
    new_status: str,
    offer_data: dict = None,
) -> Company:
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    current = company.status
    allowed = VALID_TRANSITIONS.get(current, [])
    if new_status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from '{current}' to '{new_status}'. Allowed: {allowed}",
        )

    company.status = new_status

    if new_status == "passed":
        offer = Offer(
            id=generate_uuid(),
            company_id=company_id,
            salary=offer_data.get("salary", "") if offer_data else "",
            benefits=offer_data.get("benefits", "") if offer_data else "",
            offer_date=offer_data.get("offer_date") or date.today(),
            deadline=offer_data.get("deadline")
            if offer_data and offer_data.get("deadline")
            else None,
            notes=offer_data.get("notes", "") if offer_data else "",
            status="pending",
        )
        db.add(offer)

    db.commit()
    db.refresh(company)
    return company
