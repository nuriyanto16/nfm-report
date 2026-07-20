"""Entry point FastAPI aplikasi penarik laporan SIMPEL NEXTGEN."""
from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.project_routes import router as project_router
from app.api.routes import auth_router, router
from app.api.users_routes import router as users_router
from app.core import auth_store

app = FastAPI(title="FAST REPORT — Multi-Source Report Puller", version="0.1.0")

# Seed roles + admin pertama bila store kosong (idempotent).
auth_store.bootstrap()

_origins = os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(router)
app.include_router(users_router)
app.include_router(project_router)


@app.get("/health")
def health():
    return {"status": "ok"}
