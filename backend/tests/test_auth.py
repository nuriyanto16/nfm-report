"""Test login token-based & proteksi endpoint."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def auth_client(synthetic_xlsx, tmp_path, monkeypatch):
    import yaml
    cfg = {"sources": [{
        "id": "test-src", "name": "Test", "type": "google_sheet",
        "local_path": synthetic_xlsx, "sheet_pattern": r"^\d{2}\. .+ \d{4}$",
        "layout": {"data_start_row": 4, "columns": {
            "no": 0, "issue": 1, "path_menu": 2, "tgl_request": 3,
            "tgl_mulai": 4, "tgl_estimasi": 5, "tgl_selesai": 6,
            "request_by": 7, "pic": 8, "kategori": 9, "status": 10,
            "priority": 11, "status_deploy": 12, "last_update": 13,
            "keterangan": 15},
            "section_markers": {"1. Pengujian": "Pengujian (SIMPEL)"},
            "stop_markers": ["CHANGE REQUEST (CR)/FEEDBACK USER"]}}]}
    p = tmp_path / "sources.yaml"
    p.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    monkeypatch.setenv("SOURCES_CONFIG", str(p))
    monkeypatch.setenv("APP_USER", "admin")
    monkeypatch.setenv("APP_PASS", "rahasia123")
    monkeypatch.setenv("APP_SECRET", "unit-test-secret")

    from app.core import config, repository
    config.reset_config_cache()
    repository.clear_cache()
    # Seed store (admin/rahasia123) di file AUTH_STORE terisolasi test ini;
    # bootstrap import-time app hanya jalan sekali/sesi, jadi seed eksplisit.
    from app.core import auth_store
    auth_store.bootstrap()
    from app.main import app
    return TestClient(app)


def test_protected_without_token_401(auth_client):
    r = auth_client.get("/api/sources")
    assert r.status_code == 401


def test_login_wrong_password(auth_client):
    r = auth_client.post("/api/login", json={"username": "admin", "password": "salah"})
    assert r.status_code == 401


def test_login_and_access(auth_client):
    r = auth_client.post("/api/login", json={"username": "admin", "password": "rahasia123"})
    assert r.status_code == 200
    token = r.json()["token"]
    h = {"Authorization": f"Bearer {token}"}
    assert auth_client.get("/api/sources", headers=h).status_code == 200
    me = auth_client.get("/api/me", headers=h)
    assert me.json()["username"] == "admin"


def test_tampered_token_rejected(auth_client):
    token = auth_client.post(
        "/api/login", json={"username": "admin", "password": "rahasia123"}
    ).json()["token"]
    bad = token[:-2] + ("aa" if not token.endswith("aa") else "bb")
    r = auth_client.get("/api/sources", headers={"Authorization": f"Bearer {bad}"})
    assert r.status_code == 401
