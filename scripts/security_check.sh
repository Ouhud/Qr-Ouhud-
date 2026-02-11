#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[1/4] Check: unsafe fallback user_id (or 1)"
if rg -n 'request\.session\.get\("user_id"\) or 1' routes -g '*.py' >/tmp/security_check_or1.txt; then
  echo "FAIL: found unsafe fallback user_id:"
  cat /tmp/security_check_or1.txt
  exit 1
fi
echo "OK"

echo "[2/4] Check: edit/update routes require auth + permission"
critical_files=(
  "routes/qr/edit_qr.py"
  "routes/qr/url.py"
  "routes/qr/vcard.py"
  "routes/qr/pdf.py"
  "routes/qr_base.py"
)

for f in "${critical_files[@]}"; do
  if ! rg -q 'Depends\(get_current_user\)' "$f"; then
    echo "FAIL: missing get_current_user in $f"
    exit 1
  fi
  if ! rg -q 'can_edit_qr' "$f"; then
    echo "FAIL: missing can_edit_qr in $f"
    exit 1
  fi
done
echo "OK"

echo "[3/4] Check: syntax compile"
python3 -m py_compile main.py routes/*.py routes/qr/*.py utils/access_control.py
echo "OK"

echo "[4/4] Check: resolver tracks only non-test scans by default"
if ! rg -q '_should_track_scan' routes/qr_resolve.py; then
  echo "FAIL: missing _should_track_scan in routes/qr_resolve.py"
  exit 1
fi
if ! rg -q 'if _should_track_scan\(qr, request\):' routes/qr_resolve.py; then
  echo "FAIL: scan tracking guard not active in routes/qr_resolve.py"
  exit 1
fi
echo "OK"

echo "Security check passed."
