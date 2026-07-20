"""Autentikasi berbasis token (login form) + otorisasi per-menu.

Alur:
  POST /api/login {username,password}  -> {token}
  Endpoint lain butuh header  Authorization: Bearer <token>.

Token = HMAC-signed (stdlib), berisi subjek, versi sesi (ver), dan waktu
kedaluwarsa. Kredensial diverifikasi terhadap store user (app.core.auth_store);
`.env` hanya dipakai untuk seed admin pertama (lihat auth_store.bootstrap).
Secret & TTL dari env: APP_SECRET, TOKEN_TTL_HOURS (default 12).
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Callable, Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core import auth_store

_bearer = HTTPBearer(auto_error=False)


def _secret() -> bytes:
    # Bila tak di-set, pakai secret acak per-proses (token tidak persisten
    # antar-restart — cukup untuk dev). Di produksi APP_SECRET wajib di-set.
    s = os.environ.get("APP_SECRET")
    if not s:
        s = getattr(_secret, "_ephemeral", None)
        if not s:
            s = secrets.token_hex(32)
            _secret._ephemeral = s  # type: ignore[attr-defined]
    return s.encode()


def _ttl_seconds() -> int:
    return int(float(os.environ.get("TOKEN_TTL_HOURS", "12")) * 3600)


def auth_enabled() -> bool:
    # Escape hatch untuk dev/test lokal.
    return os.environ.get("AUTH_DISABLED", "").lower() not in ("1", "true", "yes")


def _b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _b64d(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def create_token(username: str, ver: int) -> str:
    payload = {"sub": username, "ver": int(ver), "exp": int(time.time()) + _ttl_seconds()}
    body = _b64e(json.dumps(payload, separators=(",", ":")).encode())
    sig = _b64e(hmac.new(_secret(), body.encode(), hashlib.sha256).digest())
    return f"{body}.{sig}"


def verify_token(token: str) -> Dict:
    """Kembalikan payload {sub, ver, exp} bila valid, else 401."""
    try:
        body, sig = token.split(".", 1)
        expected = _b64e(hmac.new(_secret(), body.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(sig, expected):
            raise ValueError("bad signature")
        payload = json.loads(_b64d(body))
        if int(payload.get("exp", 0)) < int(time.time()):
            raise ValueError("expired")
        return payload
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesi tidak valid atau kedaluwarsa",
            headers={"WWW-Authenticate": "Bearer"},
        )


def login(username: str, password: str) -> Dict:
    user = auth_store.get_user(username)
    ok = bool(user) and user.get("active", True) and auth_store.verify_password(
        password, user
    )
    if not ok:
        # Pesan sengaja tidak membedakan user nonaktif vs salah password.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username atau password salah, atau akun nonaktif",
        )
    token = create_token(user["username"], int(user.get("ver", 1)))
    return {
        "token": token,
        "username": user["username"],
        "full_name": user.get("full_name", ""),
        "role": user.get("role", ""),
        "menus": auth_store.menus_for(user),
    }


def current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> Dict:
    """Dependency: kembalikan record user store yang valid & aktif."""
    if not auth_enabled():
        # Mode dev: kembalikan pseudo-admin dengan semua menu.
        return {
            "username": "dev", "role": "admin", "active": True, "ver": 1,
            "full_name": "Dev", "_menus": list(auth_store.MENUS.keys()),
        }
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Butuh login",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = verify_token(creds.credentials)
    user = auth_store.get_user(payload.get("sub", ""))
    if not user or not user.get("active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Akun tidak aktif atau tidak ditemukan",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if int(payload.get("ver", -1)) != int(user.get("ver", 1)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesi kedaluwarsa, silakan login ulang",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def menus_of(user: Dict) -> list:
    if "_menus" in user:  # mode dev
        return user["_menus"]
    return auth_store.menus_for(user)


def require_menu(menu: str) -> Callable[[Dict], Dict]:
    """Factory dependency: pastikan user punya akses ke `menu`, else 403."""

    def _dep(user: Dict = Depends(current_user)) -> Dict:
        if menu not in menus_of(user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Anda tidak punya akses ke menu ini",
            )
        return user

    return _dep


# Dependency siap-pakai untuk endpoint kelola user/role.
require_admin = require_menu(auth_store.MANAGE_MENU)


# Kompat mundur: sebagian kode lama memakai require_auth (mengembalikan
# username string). Tetap sediakan sebagai tipis di atas current_user.
def require_auth(user: Dict = Depends(current_user)) -> str:
    return user.get("username", "")
