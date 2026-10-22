"""Pytest fixtures — real PostgreSQL (docker compose).

Uses dedicated DB `wowlance_test` so drop_all never wipes uvicorn/Swagger/UI
data on `wowlance`. AUTH_DISABLED stays true for the suite (C8).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app

from app.db import models  # noqa: F401

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_SALE = (
    REPO_ROOT / "contracts" / "strategy" / "examples" / "FounderHandoff.sale.json"
)
TEST_DB_NAME = "wowlance_test"


def _test_database_url() -> str:
    """Always resolve to `wowlance_test` — never drop_all on app DB `wowlance`.

    Priority: TEST_DATABASE_URL / settings.test_database_url, else DATABASE_URL
    with database name forced to wowlance_test. If the resolved name is still
    `wowlance` (misconfigured env), rewrite to wowlance_test.
    """
    raw = getattr(settings, "test_database_url", "").strip()
    url = make_url(raw) if raw else make_url(settings.database_url).set(
        database=TEST_DB_NAME
    )
    if (url.database or "").lower() == "wowlance":
        url = url.set(database=TEST_DB_NAME)
    return url.render_as_string(hide_password=False)


def _ensure_test_database(test_url: str) -> None:
    """CREATE DATABASE wowlance_test if missing (existing docker volumes)."""
    url = make_url(test_url)
    admin = url.set(database="wowlance")
    admin_eng = create_engine(
        admin.render_as_string(hide_password=False),
        isolation_level="AUTOCOMMIT",
        pool_pre_ping=True,
    )
    try:
        with admin_eng.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": url.database},
            ).scalar()
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{url.database}"'))
    finally:
        admin_eng.dispose()


@pytest.fixture(scope="session", autouse=True)
def _auth_disabled_for_tests():
    """C8: pytest runs without Keycloak — strict JWT is opt-in per test."""
    settings.auth_disabled = True
    yield
    settings.auth_disabled = True


@pytest.fixture(scope="session", autouse=True)
def _rbac_disabled_for_tests():
    """C27: pytest default is ROOM_RBAC_DISABLED=true (demo / G1–G10)."""
    settings.room_rbac_disabled = True
    yield
    settings.room_rbac_disabled = True


@pytest.fixture(scope="session", autouse=True)
def _internal_auth_disabled_for_tests():
    """C21: pytest runs with internal service-token guard disabled by default."""
    settings.internal_auth_disabled = True
    settings.internal_service_token = ""
    yield
    settings.internal_auth_disabled = True
    settings.internal_service_token = ""


@pytest.fixture(scope="session")
def engine():
    test_url = _test_database_url()
    try:
        _ensure_test_database(test_url)
    except Exception as exc:  # noqa: BLE001
        pytest.exit(
            f"Cannot prepare test database {test_url!r}. "
            f"Run `docker compose up -d db` from repo root. ({exc})",
            returncode=1,
        )

    resolved_db = make_url(test_url).database
    if (resolved_db or "").lower() == "wowlance":
        pytest.exit(
            f"Refusing to run pytest against app DB {test_url!r}. "
            f"Use {TEST_DB_NAME} (TEST_DATABASE_URL or default remap in conftest).",
            returncode=1,
        )

    eng = create_engine(test_url, pool_pre_ping=True)
    try:
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        pytest.exit(
            f"PostgreSQL test DB unavailable at {test_url!r}. "
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
