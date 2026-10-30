"""Opt-in bearer access for private fictional-data workspaces.

Only SHA-256 hashes of independently generated 256-bit tokens belong in config.
This is not a public account service or a replacement for enterprise identity.
"""

import json
import os
import re
import time
from contextvars import ContextVar
from dataclasses import dataclass
from hashlib import sha256
from hmac import compare_digest
from uuid import UUID

from fastapi import HTTPException, Request


@dataclass(frozen=True)
class Principal:
    subject: str
    workspace: str
    role: str


current_principal: ContextVar[Principal | None] = ContextVar("principal", default=None)
LOCAL = Principal("local", "local", "analyst")


def configuration():
    mode = os.getenv("AEGISRISK_ACCESS_MODE", "local")
    if mode == "local":
        return mode, []
    if mode != "token":
        raise HTTPException(503, "Access configuration unavailable")
    try:
        raw = os.environ["AEGISRISK_ACCESS_USERS"]
        if len(raw) > 32768:
            raise ValueError
        users = json.loads(raw)
        if not isinstance(users, list) or not 1 <= len(users) <= 64:
            raise ValueError
        subjects, hashes = set(), set()
        for user in users:
            if not isinstance(user, dict) or set(user) != {
                "subject", "workspace", "role", "token_sha256", "expires_at"
            }:
                raise ValueError
            for key in ("subject", "workspace"):
                if not isinstance(user[key], str) or str(UUID(user[key])) != user[key]:
                    raise ValueError
            digest = user["token_sha256"]
            if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                raise ValueError
            if user["role"] not in ("viewer", "analyst"):
                raise ValueError
            if type(user["expires_at"]) is not int or user["expires_at"] <= 0:
                raise ValueError
            if user["subject"] in subjects or digest in hashes:
                raise ValueError
            subjects.add(user["subject"])
            hashes.add(digest)
        return mode, users
    except (KeyError, ValueError, TypeError, AttributeError):
        # Never expose configuration values or parsing details to the client.
        raise HTTPException(503, "Access configuration unavailable") from None


def authenticate(request: Request) -> Principal:
    mode, users = configuration()
    if mode == "local":
        # Caller-supplied identity headers never alter local ownership.
        return LOCAL
    headers = request.headers.getlist("authorization")
    value = headers[0] if len(headers) == 1 else ""
    match = re.fullmatch(r"Bearer ([A-Za-z0-9_-]{43})", value)
    digest = sha256((match.group(1) if match else "").encode("ascii")).hexdigest()
    found = None
    now = time.time()
    for user in users:
        matches = compare_digest(digest, user["token_sha256"])
        if matches and match and now < user["expires_at"]:
            found = Principal(user["subject"], user["workspace"], user["role"])
    if found is None:
        raise HTTPException(401, "Valid access token required", headers={
            "WWW-Authenticate": "Bearer", "Cache-Control": "no-store"
        })
    return found


def workspace_id() -> str:
    principal = current_principal.get()
    if principal is None:
        raise HTTPException(401, "Valid access token required")
    return principal.workspace


def require_writer():
    principal = current_principal.get()
    if principal is None:
        raise HTTPException(401, "Valid access token required")
    if principal.role != "analyst":
        raise HTTPException(403, "Saving requires analyst access")
