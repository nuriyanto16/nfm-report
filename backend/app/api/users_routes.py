"""Endpoint manajemen user, role, dan profil sendiri.

Semua di bawah /api dan terproteksi. Kelola user/role butuh menu 'users'
(require_admin); endpoint /me* cukup user terautentikasi.
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core import auth_store
from app.core.auth_store import AuthError
from app.security import create_token, current_user, require_admin, menus_of

router = APIRouter(prefix="/api")


# --------------------------------------------------------------------------- #
# Profil sendiri
# --------------------------------------------------------------------------- #
@router.get("/me")
def me(user=Depends(current_user)):
    return {
        "username": user.get("username"),
        "full_name": user.get("full_name", ""),
        "role": user.get("role", ""),
        "menus": menus_of(user),
        "is_admin": auth_store.MANAGE_MENU in menus_of(user),
    }


class SelfPasswordBody(BaseModel):
    old_password: str
    new_password: str


@router.post("/me/password")
def change_own_password(body: SelfPasswordBody, user=Depends(current_user)):
    username = user["username"]
    full = auth_store.get_user(username)
    if not full or not auth_store.verify_password(body.old_password, full):
        raise HTTPException(400, "Password lama salah")
    try:
        auth_store.set_password(username, body.new_password)
    except AuthError as e:
        raise HTTPException(400, str(e))
    # ver di-bump -> token lama tak valid; terbitkan token baru agar sesi lanjut.
    fresh = auth_store.get_user(username)
    return {"token": create_token(username, int(fresh.get("ver", 1)))}


# --------------------------------------------------------------------------- #
# Katalog menu & role
# --------------------------------------------------------------------------- #
@router.get("/menus")
def get_menus(_=Depends(current_user)):
    return {"menus": [{"key": k, "label": v} for k, v in auth_store.MENUS.items()]}


@router.get("/roles")
def get_roles(_=Depends(require_admin)):
    return {"roles": auth_store.list_roles()}


class RoleBody(BaseModel):
    name: str
    label: str = ""
    menus: List[str] = []


class RoleUpdateBody(BaseModel):
    label: str = ""
    menus: List[str] = []


@router.post("/roles")
def create_role(body: RoleBody, _=Depends(require_admin)):
    try:
        return auth_store.upsert_role(body.name, body.label, body.menus, creating=True)
    except AuthError as e:
        raise HTTPException(400, str(e))


@router.put("/roles/{name}")
def update_role(name: str, body: RoleUpdateBody, _=Depends(require_admin)):
    try:
        return auth_store.upsert_role(name, body.label, body.menus, creating=False)
    except AuthError as e:
        raise HTTPException(400, str(e))


@router.delete("/roles/{name}")
def remove_role(name: str, _=Depends(require_admin)):
    try:
        auth_store.delete_role(name)
    except AuthError as e:
        raise HTTPException(400, str(e))
    return {"status": "deleted", "name": name}


# --------------------------------------------------------------------------- #
# User
# --------------------------------------------------------------------------- #
@router.get("/users")
def get_users(_=Depends(require_admin)):
    return {"users": auth_store.list_users()}


class UserCreateBody(BaseModel):
    username: str
    password: str
    role: str
    full_name: str = ""
    description: str = ""
    active: bool = True


class UserUpdateBody(BaseModel):
    role: Optional[str] = None
    full_name: Optional[str] = None
    description: Optional[str] = None
    active: Optional[bool] = None


class PasswordBody(BaseModel):
    new_password: str


@router.post("/users")
def add_user(body: UserCreateBody, _=Depends(require_admin)):
    try:
        return auth_store.create_user(
            body.username, body.password, body.role,
            full_name=body.full_name, description=body.description,
            active=body.active,
        )
    except AuthError as e:
        raise HTTPException(400, str(e))


@router.put("/users/{username}")
def edit_user(username: str, body: UserUpdateBody, admin=Depends(require_admin)):
    # Cegah admin mengunci diri sendiri (nonaktif / cabut menu kelola).
    if username == admin["username"] and body.active is False:
        raise HTTPException(400, "Tidak bisa menonaktifkan akun sendiri")
    try:
        return auth_store.update_user(
            username, role=body.role, full_name=body.full_name,
            description=body.description, active=body.active,
        )
    except AuthError as e:
        raise HTTPException(400, str(e))


@router.post("/users/{username}/password")
def reset_user_password(username: str, body: PasswordBody, _=Depends(require_admin)):
    try:
        auth_store.set_password(username, body.new_password)
    except AuthError as e:
        raise HTTPException(400, str(e))
    return {"status": "ok", "username": username}


@router.delete("/users/{username}")
def remove_user(username: str, admin=Depends(require_admin)):
    if username == admin["username"]:
        raise HTTPException(400, "Tidak bisa menghapus akun sendiri")
    try:
        auth_store.delete_user(username)
    except AuthError as e:
        raise HTTPException(400, str(e))
    return {"status": "deleted", "username": username}
