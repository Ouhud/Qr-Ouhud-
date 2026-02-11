# =============================================================================
# 📦 models/__init__.py
# -----------------------------------------------------------------------------
# Minimal & korrekt für Alembic
# =============================================================================

from .user import User
from .plan import Plan
from .qrcode import QRCode
from .qr_scan import QRScan
from .qr_history import QRHistory
from .qr_content_versions import QRContentVersion
from .login_device import LoginDevice
from .lead_capture import LeadCapture
from .feedback_entry import FeedbackEntry
from .coupon_redemption import CouponRedemption
from .link_health_check import LinkHealthCheck
from .qr_conversion import QRConversion
from .qr_share import QRShare
from .workspace_qr import WorkspaceQR
from .workspace_member import WorkspaceMember
from .workspace import Workspace
from .api_key import APIKey

__all__ = [
    "User",
    "Plan",
    "QRCode",
    "QRScan",
    "QRHistory",
    "QRContentVersion",
    "LoginDevice",
    "LeadCapture",
    "FeedbackEntry",
    "CouponRedemption",
    "LinkHealthCheck",
    "QRConversion",
    "QRShare",
    "WorkspaceQR",
    "WorkspaceMember",
    "Workspace",
    "APIKey",
]
