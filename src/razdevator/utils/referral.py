from __future__ import annotations

import secrets


def generate_referral_tag() -> str:
    return secrets.token_urlsafe(6).replace("-", "A").replace("_", "B")
