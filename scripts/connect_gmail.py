#!/usr/bin/env python3
"""One-time Gmail OAuth. Reads credentials.json, opens the Google consent page, writes token.json.

Scope is gmail.compose: ALICE can create drafts and send the one you click Send on. Nothing else.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from alice_core.mailer import SCOPES, credentials_path, token_path


def main() -> None:
    creds_file = credentials_path()
    if not creds_file.exists():
        print(f"FAIL no OAuth client at {creds_file}")
        print("     Google Cloud console > APIs & Services > Credentials > OAuth client ID (Desktop app),")
        print("     enable the Gmail API, download the JSON and save it as credentials.json")
        sys.exit(1)
    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_secrets_file(str(creds_file), SCOPES)
    creds = flow.run_local_server(host="127.0.0.1", port=0, open_browser=True)
    token_path().write_text(creds.to_json())
    print(f"ok   Gmail connected, token saved to {token_path()}")


if __name__ == "__main__":
    main()
