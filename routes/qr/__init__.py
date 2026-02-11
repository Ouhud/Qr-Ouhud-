# routes/qr/__init__.py
# =============================================================================
# 🚀 QR Routes Package (Ouhud QR)
# =============================================================================

from routes.qr.url import router as url_router
from routes.qr.vcard import router as vcard_router
from routes.qr.pdf import router as pdf_router
from routes.qr.wifi import router as wifi_router
from routes.qr.email import router as email_router
from routes.qr.sms import router as sms_router
from routes.qr.tel import router as tel_router
from routes.qr.social import router as social_router
from routes.qr.event import router as event_router
from routes.qr.geo import router as geo_router
from routes.qr.multilink import router as multilink_router
from routes.qr.product import router as product_router
from routes.qr.payment import router as payment_router
from routes.qr.wallet import router as wallet_router
from routes.qr.gs1 import router as gs1_router
from routes.qr.app_deeplink import router as app_router
from routes.qr.review import router as review_router
from routes.qr.booking import router as booking_router
from routes.qr.lead import router as lead_router
from routes.qr.feedback import router as feedback_router
from routes.qr.coupon import router as coupon_router

__all__ = [
    "url_router",
    "vcard_router",
    "pdf_router",
    "wifi_router",
    "email_router",
    "sms_router",
    "tel_router",
    "social_router",
    "event_router",
    "geo_router",
    "multilink_router",
    "product_router",
    "payment_router",
    "wallet_router",
    "gs1_router",
    "app_router",
    "review_router",
    "booking_router",
    "lead_router",
    "feedback_router",
    "coupon_router",
]
