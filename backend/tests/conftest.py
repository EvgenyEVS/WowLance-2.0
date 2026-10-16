"""Pytest fixtures — real PostgreSQL (docker compose). Tables truncated per test."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app

from app.db import models  # noqa: F401

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_SALE = (
    REPO_ROOT / "contracts" / "wowlance" / "examples" / "FounderHandoff.sale.json"
)


@pytest.fixture(scope="session", autouse=True)
def _auth_disabled_for_tests():
    """C8: pytest runs without Keycloak — strict JWT is opt-in per test."""
    settings.auth_disabled = True
    yield
    settings.auth_disabled = True


@pytest.fixture(scope="session")
def engine():
    eng = create_engine(settings.database_url, pool_pre_ping=True)
    try:
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        pytest.exit(
            f"PostgreSQL unavailable at {settings.database_url!r}. "
            f"Run `docker compose up -d db` from repo root. ({exc})",
            returncode=1,
        )
    Base.metadata.drop_all(bind=eng)
    Base.metadata.create_all(bind=eng)
    yield eng
    Base.metadata.drop_all(bind=eng)
    eng.dispose()


@pytest.fixture()
def db_session(engine):
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = Session()
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def sale_payload() -> dict:
    return json.loads(EXAMPLE_SALE.read_text(encoding="utf-8"))
