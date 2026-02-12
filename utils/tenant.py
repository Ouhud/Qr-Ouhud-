from __future__ import annotations

import os
import re
from dataclasses import dataclass
from urllib.parse import urlparse


_TENANT_SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")


@dataclass(frozen=True)
class TenantContext:
    host: str
    tenant_slug: str | None
    subdomain: str | None
    is_main_portal: bool


def _normalize_host(raw_host: str | None) -> str:
    host = str(raw_host or "").strip().lower()
    if not host:
        return ""
    if "," in host:
        host = host.split(",", 1)[0].strip()
    if ":" in host:
        host = host.split(":", 1)[0].strip()
    return host.rstrip(".")


def _host_from_app_domain(app_domain: str | None) -> str:
    raw = str(app_domain or "").strip()
    if not raw:
        return ""
    if "://" not in raw:
        raw = f"https://{raw}"
    parsed = urlparse(raw)
    return _normalize_host(parsed.netloc)


def _derive_portal_host(app_domain: str | None) -> str:
    explicit = _normalize_host(os.getenv("TENANT_PORTAL_HOST", ""))
    if explicit:
        return explicit
    return _host_from_app_domain(app_domain)


def resolve_tenant_context(host: str | None, app_domain: str | None = None) -> TenantContext:
    normalized_host = _normalize_host(host)
    portal_host = _derive_portal_host(app_domain or os.getenv("APP_DOMAIN"))

    if not normalized_host:
        return TenantContext(host="", tenant_slug=None, subdomain=None, is_main_portal=True)

    if normalized_host in {"localhost", "127.0.0.1"}:
        return TenantContext(
            host=normalized_host,
            tenant_slug=None,
            subdomain=None,
            is_main_portal=True,
        )

    if normalized_host.startswith("www."):
        return TenantContext(
            host=normalized_host,
            tenant_slug=None,
            subdomain="www",
            is_main_portal=True,
        )

    if portal_host and normalized_host == portal_host:
        return TenantContext(
            host=normalized_host,
            tenant_slug=None,
            subdomain=portal_host.split(".")[0],
            is_main_portal=True,
        )

    if portal_host and normalized_host.endswith(f".{portal_host}"):
        left = normalized_host[: -(len(portal_host) + 1)]
        # only one tenant label is allowed: <tenant>.<portal_host>
        if left and "." not in left and _TENANT_SLUG_RE.match(left):
            return TenantContext(
                host=normalized_host,
                tenant_slug=left,
                subdomain=left,
                is_main_portal=False,
            )

    # fallback: no tenant isolation if host pattern is not trusted
    return TenantContext(
        host=normalized_host,
        tenant_slug=None,
        subdomain=normalized_host.split(".")[0] if "." in normalized_host else None,
        is_main_portal=True,
    )
