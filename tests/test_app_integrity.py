import pytest
import httpx
from httpx import ASGITransport
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from main import app


@pytest.mark.asyncio
async def test_all_routes_status_codes():
    """
    Überprüft, ob alle Routen erreichbar sind.
    - GET-Routen werden mit GET getestet
    - POST-Routen mit Dummy-Daten getestet
    - Static-/Mount-Routen werden übersprungen
    """
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        failed = []

        for route in app.routes:
            # ➜ 1. StaticFiles oder Mounts überspringen
            if hasattr(route, "app"):  
                continue
            if "{" in route.path:
                continue  # ➜ 2. dynamische Parameter überspringen

            try:
                # ➜ 3. HTTP-Methode erkennen
                methods = getattr(route, "methods", {"GET"})
                if "POST" in methods:
                    response = await client.post(route.path, data={"test": "ok"})
                else:
                    response = await client.get(route.path)

                # ➜ 4. Fehlerhafte Statuscodes aufzeichnen
                if response.status_code >= 400:
                    failed.append((route.path, response.status_code))
            except Exception as e:
                failed.append((route.path, str(e)))

        # ➜ 5. Ergebnis anzeigen
        print("\n=== ROUTEN-TEST ===")
        if failed:
            for path, code in failed:
                print(f"❌ {path} -> {code}")
        else:
            print("✅ Alle Routen funktionieren fehlerfrei!")

        assert not failed, f"Fehlerhafte Routen: {failed}"



def test_database_connection():
    """
    Prüft, ob die Datenbankverbindung hergestellt werden kann.
    """
    DATABASE_URL = "sqlite:///./qr_ouhud.db"  # ggf. Pfad anpassen

    engine = create_engine(DATABASE_URL)
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
            print("✅ Datenbankverbindung erfolgreich.")
    except OperationalError as e:
        pytest.fail(f"❌ Datenbankverbindung fehlgeschlagen: {e}")
