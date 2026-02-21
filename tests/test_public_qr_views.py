from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import get_db
from main import app
from models.plan import Plan
from models.qrcode import QRCode
from models.user import User


@pytest.fixture
def public_views_env():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Plan.__table__.create(bind=engine, checkfirst=True)
    User.__table__.create(bind=engine, checkfirst=True)
    QRCode.__table__.create(bind=engine, checkfirst=True)

    def override_get_db():
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client, testing_session_local

    app.dependency_overrides.pop(get_db, None)
    engine.dispose()


def _seed_qr(session_local, qr_type: str, slug: str) -> None:
    with session_local() as db:
        user = User(
            username=f"user_{slug}",
            email=f"{slug}@example.com",
            password_hash="hash",
        )
        db.add(user)
        db.flush()

        qr = QRCode(
            user_id=user.id,
            slug=slug,
            type=qr_type,
            title=f"{qr_type} test",
            dynamic_url=f"/d/{slug}",
            image_path=f"static/generated_qr/{slug}.png",
        )
        if qr_type == "vcard":
            qr.set_data(
                {
                    "first_name": "Max",
                    "last_name": "Mustermann",
                    "email": "max@example.com",
                }
            )
        elif qr_type == "wifi":
            qr.set_data(
                {
                    "ssid": "TestNet",
                    "password": "secret",
                    "encryption": "WPA",
                    "hidden": False,
                }
            )
        else:
            qr.set_data({})
        db.add(qr)
        db.commit()


def test_public_vcard_view_hides_edit_link(public_views_env):
    client, session_local = public_views_env
    slug = "pub-vcard-1"
    _seed_qr(session_local, "vcard", slug)

    response = client.get(f"/qr/vcard/v/{slug}")

    assert response.status_code == 200
    assert f"/qr/vcard/edit/{slug}" not in response.text


def test_public_wifi_view_hides_edit_link(public_views_env):
    client, session_local = public_views_env
    slug = "pub-wifi-1"
    _seed_qr(session_local, "wifi", slug)

    response = client.get(f"/qr/wifi/v/{slug}")

    assert response.status_code == 200
    assert f"/qr/edit/{slug}" not in response.text
