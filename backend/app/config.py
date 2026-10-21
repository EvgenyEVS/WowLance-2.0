from pathlib import Path
from decimal import Decimal

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    app_env: str = "local"
    database_url: str = (
        "postgresql+psycopg://wowlance:wowlance@127.0.0.1:5433/wowlance"
    )
    # Pytest only. Empty → same host/user as database_url, db name wowlance_test.
    test_database_url: str = ""

    # C8 auth. Dev/test default: open /api/v1/* without JWT.
    # Prod/demo with Keycloak: AUTH_DISABLED=false (strict Bearer).
    auth_disabled: bool = True
    auth_stub_jwks: bool = False  # dev-only: /auth/stub-jwks + /auth/stub-token
    keycloak_issuer: str = "http://127.0.0.1:8080/realms/wowlance"
    keycloak_audience: str = "wowlance-api"  # empty -> skip aud check
    keycloak_jwks_url: str = ""  # empty -> derive from issuer

    @property
    def jwks_url(self) -> str:
        if self.keycloak_jwks_url:
            return self.keycloak_jwks_url
        return self.keycloak_issuer.rstrip("/") + "/protocol/openid-connect/certs"

    @property
    def verify_audience(self) -> str | None:
        return self.keycloak_audience or None

    # C16: stub earnings amount per accepted task (Decimal, as string in API).
    earnings_task_amount: Decimal = Decimal("10.00")
    earnings_currency: str = "USD"

    # C21: internal service-token guard on /internal/v1/* (stub, без Keycloak).
    # Default open (localhost/pytest). Strict mode: INTERNAL_AUTH_DISABLED=false.
    internal_auth_disabled: bool = True
    internal_service_token: str = ""

    @property
    def internal_guard_required(self) -> bool:
        """False when internal routes are open (default/dev/tests)."""
        return not self.internal_auth_disabled


settings = Settings()
