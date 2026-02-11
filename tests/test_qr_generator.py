import pytest
from utils.qr_generator import generate_qr_png
from pathlib import Path
from _pytest.tmpdir import TempPathFactory

def test_qr_generator_creates_file(tmp_path: Path):
    result = generate_qr_png(payload="https://ouhud.com/test", size=300)
    assert isinstance(result, dict)
    assert "path" in result
    assert Path(result["path"]).exists(), f"Datei fehlt: {result['path']}"