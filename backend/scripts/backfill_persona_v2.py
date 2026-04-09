from app.db.session import SessionLocal
from app.db.models import Interview
from app.services.persona_v2_service import (
    ingest_review_evidence,
    rebuild_persona_snapshot,
)


def main() -> None:
    db = SessionLocal()
    try:
        interviews = db.query(Interview).order_by(Interview.created_at.asc()).all()
        for iv in interviews:
            analysis = iv.ai_analysis if isinstance(iv.ai_analysis, dict) else {}
            if not analysis:
                continue
            ingest_review_evidence(
                db,
                interview_id=iv.id,
                round_num=iv.round,
                analysis=analysis,
                raw_notes=iv.raw_notes or "",
            )

        snapshot = rebuild_persona_snapshot(db)
        print("persona v2 backfill completed")
        print(snapshot)
    finally:
        db.close()


if __name__ == "__main__":
    main()
