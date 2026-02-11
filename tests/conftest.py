import sys, os, pytest_asyncio, httpx
from httpx import ASGITransport

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ⚙️ Hauptdatei importieren — anpassen, falls anders!
from main import app  # falls dein Hauptfile qr_app.py heißt, ändere zu: from qr_app import app

@pytest_asyncio.fixture
async def client():
    """Erstellt einen funktionierenden Testclient."""
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
