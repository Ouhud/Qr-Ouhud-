from __future__ import annotations

from utils.tenant import resolve_tenant_context


def test_main_portal_host_without_tenant():
    ctx = resolve_tenant_context("qr.ouhud.com", app_domain="https://qr.ouhud.com")
    assert ctx.tenant_slug is None
    assert ctx.is_main_portal is True


def test_customer_subdomain_maps_to_tenant():
    ctx = resolve_tenant_context("tesla.qr.ouhud.com", app_domain="https://qr.ouhud.com")
    assert ctx.tenant_slug == "tesla"
    assert ctx.subdomain == "tesla"
    assert ctx.is_main_portal is False


def test_localhost_is_main_portal():
    ctx = resolve_tenant_context("localhost:8000", app_domain="https://qr.ouhud.com")
    assert ctx.tenant_slug is None
    assert ctx.is_main_portal is True


def test_invalid_multi_label_left_part_does_not_become_tenant():
    ctx = resolve_tenant_context("a.b.qr.ouhud.com", app_domain="https://qr.ouhud.com")
    assert ctx.tenant_slug is None
    assert ctx.is_main_portal is True
