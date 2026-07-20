"""Penyimpanan user & role berbasis file JSON (tanpa dependency tambahan).

Semua akun (termasuk admin) disimpan di sini. File ditulis atomik dan dilindungi
lock proses. Password di-hash PBKDF2-HMAC-SHA256 (stdlib). Lokasi file diambil
dari env AUTH_STORE (default <backend>/data/auth.json) sehingga bisa dipetakan ke
volume agar persisten antar-redeploy.

Struktur file:
{
  "roles": {
    "<name>": {"label": "...", "menus": ["harian", ...]}
  },
  "users": {
    "<username>": {
      "username": "...", "full_name": "...", "description": "...",
      "role": "<name>", "active": true, "ver": 1,
      "salt": "<hex>", "hash": "<hex>",
      "created_at": "<iso>", "updated_at": "<iso>"
    }
  }
}
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

# --- Katalog menu (satu-satunya sumber kebenaran, dikirim ke frontend) ---
# key -> label tampilan
MENUS: Dict[str, str] = {
    "dashboard": "Dashboard Executive",
    "harian": "Laporan Harian",
    "mingguan": "Laporan Mingguan",
    "bulanan": "Laporan Bulanan",
    "monitoring": "Monitoring Progress",
    "project_mgmt": "Project Management",
    "evaluasi_tw": "Evaluasi Triwulan",
    "sources": "Sumber Data",
    "users": "Manajemen User",
}
MANAGE_MENU = "users"  # menu yang memberi hak kelola user & role

# Menu yang dikhususkan untuk role superadmin. Tidak ikut diberikan otomatis ke
# role 'admin' (lihat self-heal di bootstrap) sehingga benar-benar eksklusif.
SUPERADMIN_ONLY = {"project_mgmt", "evaluasi_tw"}
SUPER_ROLE = "superadmin"


def _admin_menus() -> List[str]:
    """Semua menu kecuali yang dikhususkan superadmin, urut sesuai katalog."""
    return [k for k in MENUS if k not in SUPERADMIN_ONLY]


# Role bawaan saat store pertama kali dibuat.
DEFAULT_ROLES: Dict[str, Dict] = {
    "superadmin": {"label": "Super Admin", "menus": list(MENUS.keys())},
    "admin": {"label": "Administrator", "menus": _admin_menus()},
    "operator": {
        "label": "Operator",
        "menus": ["dashboard", "harian", "mingguan", "bulanan", "monitoring"],
    },
    "viewer": {"label": "Viewer", "menus": ["dashboard", "harian", "mingguan", "bulanan"]},
}

_PBKDF2_ROUNDS = 200_000
_lock = threading.RLock()


class AuthError(Exception):
    """Kesalahan operasi store yang aman ditampilkan ke user (mis. duplikat)."""


# --------------------------------------------------------------------------- #
# Lokasi & I/O file
# --------------------------------------------------------------------------- #
def _store_path() -> Path:
    env = os.environ.get("AUTH_STORE")
    if env:
        return Path(env)
    return Path(__file__).resolve().parent.parent / "data" / "auth.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read() -> Dict:
    path = _store_path()
    if not path.exists():
        return {"roles": {}, "users": {}}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f) or {}
    data.setdefault("roles", {})
    data.setdefault("users", {})
    return data


def _write(data: Dict) -> None:
    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    # Tulis ke file sementara di folder yang sama lalu replace (atomik).
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


# --------------------------------------------------------------------------- #
# Hashing password (PBKDF2, stdlib)
# --------------------------------------------------------------------------- #
def hash_password(password: str, salt: Optional[str] = None) -> Dict[str, str]:
    salt = salt or secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt), _PBKDF2_ROUNDS
    )
    return {"salt": salt, "hash": dk.hex()}


def verify_password(password: str, user: Dict) -> bool:
    salt = user.get("salt") or ""
    expected = user.get("hash") or ""
    if not salt or not expected:
        return False
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt), _PBKDF2_ROUNDS
    )
    return hmac.compare_digest(dk.hex(), expected)


# --------------------------------------------------------------------------- #
# Serialisasi user aman (tanpa salt/hash) untuk dikirim ke API
# --------------------------------------------------------------------------- #
def public_user(user: Dict) -> Dict:
    return {
        "username": user["username"],
        "full_name": user.get("full_name", ""),
        "description": user.get("description", ""),
        "role": user.get("role", ""),
        "active": bool(user.get("active", True)),
        "created_at": user.get("created_at"),
        "updated_at": user.get("updated_at"),
    }


def menus_for(user: Dict, data: Optional[Dict] = None) -> List[str]:
    data = data or _read()
    role = data["roles"].get(user.get("role", ""))
    if not role:
        return []
    # Hanya kembalikan menu yang masih ada di katalog, urut sesuai katalog.
    allowed = set(role.get("menus", []))
    return [k for k in MENUS if k in allowed]


def is_manager(user: Dict, data: Optional[Dict] = None) -> bool:
    return MANAGE_MENU in menus_for(user, data)


# --------------------------------------------------------------------------- #
# Query
# --------------------------------------------------------------------------- #
def get_user(username: str) -> Optional[Dict]:
    with _lock:
        return _read()["users"].get(username)


def list_users() -> List[Dict]:
    with _lock:
        data = _read()
    return [public_user(u) for u in data["users"].values()]


def list_roles() -> List[Dict]:
    with _lock:
        data = _read()
    return [
        {"name": name, "label": r.get("label", name), "menus": r.get("menus", [])}
        for name, r in data["roles"].items()
    ]


def get_role(name: str) -> Optional[Dict]:
    with _lock:
        r = _read()["roles"].get(name)
    if r is None:
        return None
    return {"name": name, "label": r.get("label", name), "menus": r.get("menus", [])}


def _count_active_admins(data: Dict, *, exclude: Optional[str] = None) -> int:
    n = 0
    for uname, u in data["users"].items():
        if uname == exclude:
            continue
        if u.get("active", True) and is_manager(u, data):
            n += 1
    return n


# --------------------------------------------------------------------------- #
# Mutasi user
# --------------------------------------------------------------------------- #
def create_user(
    username: str, password: str, role: str, *,
    full_name: str = "", description: str = "", active: bool = True,
) -> Dict:
    username = username.strip()
    if not username:
        raise AuthError("Username wajib diisi")
    if not password:
        raise AuthError("Password wajib diisi")
    with _lock:
        data = _read()
        if username in data["users"]:
            raise AuthError(f"Username '{username}' sudah ada")
        if role not in data["roles"]:
            raise AuthError(f"Role '{role}' tidak dikenal")
        rec = {
            "username": username,
            "full_name": full_name.strip(),
            "description": description.strip(),
            "role": role,
            "active": bool(active),
            "ver": 1,
            "created_at": _now(),
            "updated_at": _now(),
            **hash_password(password),
        }
        data["users"][username] = rec
        _write(data)
        return public_user(rec)


def update_user(
    username: str, *,
    full_name: Optional[str] = None, description: Optional[str] = None,
    role: Optional[str] = None, active: Optional[bool] = None,
) -> Dict:
    with _lock:
        data = _read()
        u = data["users"].get(username)
        if not u:
            raise AuthError("User tidak ditemukan")
        if role is not None:
            if role not in data["roles"]:
                raise AuthError(f"Role '{role}' tidak dikenal")
            u["role"] = role
        if full_name is not None:
            u["full_name"] = full_name.strip()
        if description is not None:
            u["description"] = description.strip()
        if active is not None:
            u["active"] = bool(active)
        # Jaga: minimal satu admin aktif tersisa.
        if _count_active_admins(data) == 0:
            raise AuthError("Harus ada minimal satu admin aktif")
        u["updated_at"] = _now()
        _write(data)
        return public_user(u)


def set_password(username: str, new_password: str) -> None:
    if not new_password:
        raise AuthError("Password baru wajib diisi")
    with _lock:
        data = _read()
        u = data["users"].get(username)
        if not u:
            raise AuthError("User tidak ditemukan")
        u.update(hash_password(new_password))
        u["ver"] = int(u.get("ver", 1)) + 1  # invalidasi sesi lama
        u["updated_at"] = _now()
        _write(data)


def delete_user(username: str) -> None:
    with _lock:
        data = _read()
        if username not in data["users"]:
            raise AuthError("User tidak ditemukan")
        if _count_active_admins(data, exclude=username) == 0 and is_manager(
            data["users"][username], data
        ):
            raise AuthError("Tidak bisa menghapus admin terakhir")
        del data["users"][username]
        _write(data)


# --------------------------------------------------------------------------- #
# Mutasi role
# --------------------------------------------------------------------------- #
def upsert_role(name: str, label: str, menus: List[str], *, creating: bool) -> Dict:
    name = name.strip()
    if not name:
        raise AuthError("Nama role wajib diisi")
    menus = [m for m in menus if m in MENUS]
    with _lock:
        data = _read()
        exists = name in data["roles"]
        if creating and exists:
            raise AuthError(f"Role '{name}' sudah ada")
        if not creating and not exists:
            raise AuthError("Role tidak ditemukan")
        data["roles"][name] = {"label": label.strip() or name, "menus": menus}
        # Jaga: jangan sampai role edit menghapus admin manajemen terakhir.
        if _count_active_admins(data) == 0:
            raise AuthError(
                "Perubahan ini menghapus akses kelola dari semua admin aktif"
            )
        _write(data)
        return {"name": name, "label": data["roles"][name]["label"], "menus": menus}


def delete_role(name: str) -> None:
    with _lock:
        data = _read()
        if name not in data["roles"]:
            raise AuthError("Role tidak ditemukan")
        used = [u["username"] for u in data["users"].values() if u.get("role") == name]
        if used:
            raise AuthError(f"Role dipakai oleh: {', '.join(used)}")
        del data["roles"][name]
        _write(data)


# --------------------------------------------------------------------------- #
# Bootstrap (seed pertama kali)
# --------------------------------------------------------------------------- #
def bootstrap() -> None:
    """Seed roles + admin pertama bila store kosong. Idempotent."""
    with _lock:
        data = _read()
        changed = False
        if not data.get("roles"):
            data["roles"] = {k: dict(v) for k, v in DEFAULT_ROLES.items()}
            changed = True
        # Self-heal: role superadmin selalu ada dan selalu punya SEMUA menu
        # (termasuk menu baru & menu eksklusif superadmin).
        superadmin = data.get("roles", {}).get(SUPER_ROLE)
        if superadmin is None:
            data.setdefault("roles", {})[SUPER_ROLE] = dict(DEFAULT_ROLES[SUPER_ROLE])
            changed = True
        elif set(superadmin.get("menus", [])) != set(MENUS):
            superadmin["menus"] = list(MENUS)
            changed = True
        # Self-heal: admin punya semua menu KECUALI yang dikhususkan superadmin
        # (mis. saat ada menu umum baru ditambahkan). Role lain tidak diubah.
        admin = data.get("roles", {}).get("admin")
        if admin is not None and set(admin.get("menus", [])) != set(_admin_menus()):
            admin["menus"] = _admin_menus()
            changed = True
        if not data.get("users"):
            uname = os.environ.get("APP_USER", "admin").strip() or "admin"
            pwd = os.environ.get("APP_PASS", "").strip()
            generated = False
            if not pwd:
                pwd = secrets.token_urlsafe(12)
                generated = True
            data["users"][uname] = {
                "username": uname,
                "full_name": "Administrator",
                "description": "Akun admin awal (seed)",
                "role": "admin",
                "active": True,
                "ver": 1,
                "created_at": _now(),
                "updated_at": _now(),
                **hash_password(pwd),
            }
            changed = True
            if generated:
                print(
                    f"[auth] admin awal dibuat: user='{uname}' password='{pwd}' "
                    "(ganti segera lewat menu Profil)"
                )
        if changed:
            _write(data)
