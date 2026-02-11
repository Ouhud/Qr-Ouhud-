#!/bin/zsh
source venv/bin/activate
echo "🚀 Starte Ouhud QR lokal auf http://127.0.0.1:8000 ..."
python3 -m uvicorn main:app --reload
