# =============================================================================
# 💳 routes/billing.py – Stripe-Integration (Ouhud QR)
# =============================================================================
import os
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.plan import Plan
from routes.auth import get_current_user
import stripe  # pip install stripe

# ---------------------------------------------------------------------------
# 🔧 Router & Stripe-Konfiguration
# ---------------------------------------------------------------------------
router = APIRouter(prefix="/billing", tags=["Billing"])
templates = Jinja2Templates(directory="templates")

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_DOMAIN = os.getenv("STRIPE_DOMAIN", "http://127.0.0.1:8000")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")


# ---------------------------------------------------------------------------
# 💼 Übersicht aller Tarife & aktueller Plan
# ---------------------------------------------------------------------------
@router.get("/", response_class=HTMLResponse)
def billing_overview(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Zeigt die Übersicht aller Tarife und den aktuellen Benutzerplan an."""
    plans = db.query(Plan).all()

    return templates.TemplateResponse(
        "billing_overview.html",
        {
            "request": request,
            "user": user,
            "plans": plans
        }
    )


# ---------------------------------------------------------------------------
# 🧭 Upgrade auf ausgewählten Plan
# ---------------------------------------------------------------------------
@router.get("/upgrade/{plan_name}", response_class=HTMLResponse)
def billing_upgrade(
    plan_name: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Erstellt eine Stripe-Checkout-Session für den gewählten Plan."""
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Stripe API Key fehlt")

    plan: Optional[Plan] = db.query(Plan).filter(Plan.name == plan_name).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan nicht gefunden")

    try:
        plan_name_str = str(plan.name)
        plan_desc = str(plan.description or "Upgrade für Ouhud QR")
        price_value = float(getattr(plan, "price", 0.0))

        session = stripe.checkout.Session.create(
            customer_email=str(user.email),
            payment_method_types=["card"],
            mode="subscription",
            line_items=[{
                "price_data": {
                    "currency": "eur",
                    "product_data": {
                        "name": f"Ouhud QR – {plan_name_str}",
                        "description": plan_desc,
                    },
                    "unit_amount": int(price_value * 100),
                    "recurring": {"interval": "month"},
                },
                "quantity": 1,
            }],
            success_url=f"{STRIPE_DOMAIN}/billing?status=success",
            cancel_url=f"{STRIPE_DOMAIN}/billing?status=cancelled",
        )

        checkout_url = getattr(session, "url", None)
        if not isinstance(checkout_url, str):
            raise HTTPException(status_code=500, detail="Stripe-URL fehlt")

        return RedirectResponse(checkout_url, status_code=303)
    except Exception as e:
        print("[Stripe Error]", e)
        raise HTTPException(status_code=500, detail=f"Stripe-Fehler: {e}")


# ---------------------------------------------------------------------------
# 🧭 Kündigung (Subscription Cancel)
# ---------------------------------------------------------------------------
@router.get("/cancel", response_class=HTMLResponse)
def billing_cancel(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Setzt den Planstatus auf 'cancelled'."""
    user.plan_status = "cancelled"
    user.plan_expiry = datetime.now(timezone.utc)
    db.commit()
    print(f"[BILLING] {user.email} → Abo gekündigt.")
    return RedirectResponse("/billing?msg=cancelled", status_code=303)


# ---------------------------------------------------------------------------
# 🔔 Stripe Webhook (Subscription Events)
# ---------------------------------------------------------------------------
@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Empfängt Stripe-Webhooks und aktualisiert den Benutzerstatus."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except ValueError:
        return JSONResponse(status_code=400, content={"error": "Invalid payload"})
    except stripe.error.SignatureVerificationError:
        return JSONResponse(status_code=400, content={"error": "Invalid signature"})

    data = event.get("data", {}).get("object", {})
    event_type = event.get("type", "")

    # ✅ Subscription aktualisiert
    if event_type == "customer.subscription.updated":
        email = data.get("customer_email") or data.get("metadata", {}).get("email")
        if isinstance(email, str):
            user = db.query(User).filter(User.email == email).first()
            if user:
                user.plan_status = str(data.get("status", "active"))
                ts = data.get("current_period_end")
                user.plan_expiry = datetime.fromtimestamp(float(ts), tz=timezone.utc) if ts else None
                db.commit()
                print(f"[WEBHOOK] {email}: Status → {user.plan_status}")

    # 🚫 Subscription gelöscht
    elif event_type == "customer.subscription.deleted":
        email = data.get("customer_email") or data.get("metadata", {}).get("email")
        if isinstance(email, str):
            user = db.query(User).filter(User.email == email).first()
            if user:
                user.plan_status = "cancelled"
                user.plan_expiry = datetime.now(timezone.utc)
                db.commit()
                print(f"[WEBHOOK] {email}: Abo beendet")

    return JSONResponse(status_code=200, content={"status": "ok"})


# ---------------------------------------------------------------------------
# ✅ Testverbindung zu Stripe
# ---------------------------------------------------------------------------
@router.get("/test")
def test_billing_connection() -> dict[str, str]:
    """Prüft, ob die Verbindung zu Stripe funktioniert."""
    if not stripe.api_key:
        return {"status": "error", "message": "STRIPE_SECRET_KEY fehlt."}
    try:
        balance = stripe.Balance.retrieve()
        return {"status": "ok", "balance": str(balance)}
    except Exception as e:
        return {"status": "error", "message": str(e)}