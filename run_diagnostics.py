import os
import sys
import pytest

print("🔍 Starte Systemdiagnose für Ouhud QR...\n")

# 1️⃣ Alle Tests mit ausführlichem Output und HTML-Bericht
exit_code = pytest.main([
    "-v",
    "--html=report.html",
    "--self-contained-html"
])

if exit_code == 0:
    print("\n✅ Alle Tests bestanden – System vollständig funktionsfähig!")
else:
    print(f"\n❌ {exit_code} Test(s) fehlgeschlagen. Siehe 'report.html' für Details.")

sys.exit(exit_code)
