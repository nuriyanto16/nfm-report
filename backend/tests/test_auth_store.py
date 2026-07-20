"""Unit test untuk auth_store: hashing, CRUD user/role, guard admin, bootstrap."""
from __future__ import annotations

import importlib

import pytest


@pytest.fixture()
def store(tmp_path, monkeypatch):
    """auth_store dengan file store terisolasi per-test."""
    monkeypatch.setenv("AUTH_STORE", str(tmp_path / "auth.json"))
    monkeypatch.delenv("APP_PASS", raising=False)
    monkeypatch.setenv("APP_USER", "admin")
    import app.core.auth_store as auth_store
    importlib.reload(auth_store)
    auth_store.bootstrap()
    return auth_store


def test_bootstrap_seeds_roles_and_admin(store):
    roles = {r["name"] for r in store.list_roles()}
    assert {"admin", "operator", "viewer"} <= roles
    users = store.list_users()
    assert len(users) == 1 and users[0]["role"] == "admin"
    # public_user tidak membocorkan hash/salt.
    assert "hash" not in users[0] and "salt" not in users[0]


def test_password_hash_roundtrip(store):
    h = store.hash_password("rahasia")
    assert "salt" in h and "hash" in h
    assert store.verify_password("rahasia", h)
    assert not store.verify_password("salah", h)
    assert not store.verify_password("rahasia", {})  # tanpa salt/hash -> False


def test_create_and_menus_for(store):
    store.upsert_role("viewer2", "Viewer 2", ["harian"], creating=True)
    store.create_user("budi", "pw123", "viewer2", full_name="Budi")
    u = store.get_user("budi")
    assert store.menus_for(u) == ["harian"]
    assert not store.is_manager(u)


def test_create_duplicate_and_unknown_role(store):
    store.create_user("budi", "pw", "viewer")
    with pytest.raises(store.AuthError):
        store.create_user("budi", "pw", "viewer")  # duplikat
    with pytest.raises(store.AuthError):
        store.create_user("siti", "pw", "peran-hantu")  # role tak ada


def test_set_password_bumps_ver(store):
    store.create_user("budi", "pw", "viewer")
    v0 = store.get_user("budi")["ver"]
    store.set_password("budi", "baru")
    u = store.get_user("budi")
    assert u["ver"] == v0 + 1
    assert store.verify_password("baru", u)


def test_last_admin_guard_on_update(store):
    # Menonaktifkan satu-satunya admin harus ditolak.
    with pytest.raises(store.AuthError):
        store.update_user("admin", active=False)
    # Memindah admin ke role tanpa menu 'users' juga ditolak.
    with pytest.raises(store.AuthError):
        store.update_user("admin", role="viewer")


def test_last_admin_guard_on_delete(store):
    with pytest.raises(store.AuthError):
        store.delete_user("admin")
    # Tambah admin kedua -> boleh hapus yang pertama.
    store.create_user("admin2", "pw", "admin")
    store.delete_user("admin")
    assert store.get_user("admin") is None


def test_role_in_use_cannot_delete(store):
    store.create_user("budi", "pw", "viewer")
    with pytest.raises(store.AuthError):
        store.delete_role("viewer")


def test_role_edit_menus_filtered(store):
    # Menu tak dikenal dibuang.
    r = store.upsert_role("x", "X", ["harian", "menu-ngawur"], creating=True)
    assert r["menus"] == ["harian"]


def test_update_role_cannot_strip_last_admin_access(store):
    # Mengubah role admin agar tak punya menu 'users' -> ditolak.
    with pytest.raises(store.AuthError):
        store.upsert_role("admin", "Administrator", ["harian"], creating=False)
