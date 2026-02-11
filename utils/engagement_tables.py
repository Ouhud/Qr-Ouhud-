from __future__ import annotations

from sqlalchemy.engine import Engine

from models.lead_capture import LeadCapture
from models.feedback_entry import FeedbackEntry
from models.coupon_redemption import CouponRedemption


def ensure_engagement_tables(engine: Engine) -> None:
    """Erstellt Tracking-Tabellen für Lead/Feedback/Coupon idempotent."""
    try:
        LeadCapture.__table__.create(bind=engine, checkfirst=True)
        FeedbackEntry.__table__.create(bind=engine, checkfirst=True)
        CouponRedemption.__table__.create(bind=engine, checkfirst=True)
        print("✅ Engagement-Tabellen geprüft/ergänzt.")
    except Exception as exc:
        print(f"⚠️ Konnte Engagement-Tabellen nicht automatisch erstellen: {exc}")
