"""Gmail drafts.create in the worker. drafts.send only on dashboard click."""

from __future__ import annotations

import base64
import os
from email.message import EmailMessage
from pathlib import Path
from typing import Optional

from alice_core.db import ROOT

SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]


def credentials_path() -> Path:
    return Path(os.environ.get("GMAIL_CREDENTIALS_PATH", ROOT / "credentials.json"))


def token_path() -> Path:
    return Path(os.environ.get("GMAIL_TOKEN_PATH", ROOT / "token.json"))


def gmail_connected() -> bool:
    return token_path().exists()


def _service():
    if not gmail_connected():
        return None
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    creds = Credentials.from_authorized_user_file(str(token_path()), SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_path().write_text(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def create_draft(
    to_addr: str,
    subject: str,
    body: str,
    pdf_path: Optional[str] = None,
    from_addr: Optional[str] = None,
) -> Optional[str]:
    """Worker path. Never send."""
    svc = _service()
    if svc is None:
        return None
    msg = EmailMessage()
    if to_addr:
        msg["To"] = to_addr
    msg["Subject"] = subject
    if from_addr:
        msg["From"] = from_addr
    msg.set_content(body)
    if pdf_path and Path(pdf_path).exists():
        data = Path(pdf_path).read_bytes()
        msg.add_attachment(
            data,
            maintype="application",
            subtype="pdf",
            filename=Path(pdf_path).name,
        )
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    created = svc.users().drafts().create(userId="me", body={"message": {"raw": raw}}).execute()
    return created.get("id")


def send_draft(gmail_draft_id: str) -> dict:
    """Dashboard Send only. Pipeline must never call this."""
    svc = _service()
    if svc is None:
        raise RuntimeError("connect Gmail")
    return svc.users().drafts().send(userId="me", body={"id": gmail_draft_id}).execute()
