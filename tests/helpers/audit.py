# tests/helpers/audit.py
from __future__ import annotations
import re
import threading
from contextvars import ContextVar
from typing import Dict, List, Optional, Set

# Pro-Request Speicher
_request_id: ContextVar[str] = ContextVar("_request_id", default="-")
_lock = threading.Lock()

class AuditStore:
    def __init__(self) -> None:
        self.reset_all()

    def reset_all(self) -> None:
        with _lock:
            self.by_req: Dict[str, Dict[str, object]] = {}

    def _ensure(self, rid: str) -> Dict[str, object]:
        with _lock:
            if rid not in self.by_req:
                self.by_req[rid] = {
                    "templates": set(),
                    "db_tables_read": set(),
                    "db_tables_write": set(),
                    "qr_files": [],
                    "emails": [],
                    "status": None,
                    "redirect_to": None,
                    "auth_redirect": False,
                    "route_path": None,
                    "method": None,
                    "handler": None,
                }
            return self.by_req[rid]

    def set_request(self, rid: str, path: str, method: str, handler: str) -> None:
        _request_id.set(rid)
        d = self._ensure(rid)
        d["route_path"] = path
        d["method"] = method
        d["handler"] = handler

    def set_status(self, code: int, redirect_to: Optional[str]) -> None:
        d = self._ensure(_request_id.get())
        d["status"] = code
        d["redirect_to"] = redirect_to

    def add_template(self, name: str) -> None:
        d = self._ensure(_request_id.get())
        cast = d["templates"]
        if isinstance(cast, set):
            cast.add(name)

    def add_db_read(self, tbl: str) -> None:
        d = self._ensure(_request_id.get())
        cast = d["db_tables_read"]
        if isinstance(cast, set):
            cast.add(tbl)

    def add_db_write(self, tbl: str) -> None:
        d = self._ensure(_request_id.get())
        cast = d["db_tables_write"]
        if isinstance(cast, set):
            cast.add(tbl)

    def add_qr_file(self, path: str) -> None:
        d = self._ensure(_request_id.get())
        files = d["qr_files"]
        if isinstance(files, list):
            files.append(path)

    def add_email(self, to_addr: str, subject: str) -> None:
        d = self._ensure(_request_id.get())
        emails = d["emails"]
        if isinstance(emails, list):
            emails.append({"to": to_addr, "subject": subject})

    def set_auth_redirect(self, flag: bool) -> None:
        d = self._ensure(_request_id.get())
        d["auth_redirect"] = flag

    def all(self) -> List[Dict[str, object]]:
        with _lock:
            return list(self.by_req.values())

audit = AuditStore()

# --- SQL-Parsing (grob & robust genug für Report) ---
_tbl_re = re.compile(r"\bfrom\s+`?([a-zA-Z0-9_]+)`?|"
                     r"\bjoin\s+`?([a-zA-Z0-9_]+)`?|"
                     r"\bupdate\s+`?([a-zA-Z0-9_]+)`?|"
                     r"\binto\s+`?([a-zA-Z0-9_]+)`?", re.IGNORECASE)

def guess_tables(sql: str) -> Set[str]:
    hit: Set[str] = set()
    for m in _tbl_re.finditer(sql):
        for g in m.groups():
            if g:
                hit.add(g)
    return hit