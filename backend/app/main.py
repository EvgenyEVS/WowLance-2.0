"""WowLance 2.0 API (FastAPI + PostgreSQL)."""

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.auth_stub import router as auth_stub_router
from app.api.entitlements import router as entitlements_router
from app.api.handoffs import router as handoffs_router
from app.api.earnings import router as earnings_router
from app.api.leads import router as leads_router
from app.api.meet import router as meet_router
from app.api.rooms import router as rooms_router
from app.api.room_health import internal_router as room_health_internal_router
from app.api.room_health import router as room_health_router
from app.api.roster import internal_router as roster_internal_router
from app.api.roster import router as roster_router
from app.api.slots import router as slots_router
from app.api.strategy_proposals import router as strategy_proposals_router
from app.api.strategy_publications import router as strategy_publications_router
from app.api.tasks import router as tasks_router
from app.api.termination import router as termination_router
from app.auth.deps import require_user
from app.config import settings

app = FastAPI(
    title="WowLance 2.0",
    description="Room microservice — see /docs and repo contracts/",
    version="0.1.0",
)

# C21 fail-fast: strict internal auth requires a non-empty service token.
if not settings.internal_auth_disabled and not settings.internal_service_token:
    raise RuntimeError(
        "INTERNAL_SERVICE_TOKEN must be set when INTERNAL_AUTH_DISABLED=false"
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# C8: client routes require a valid Keycloak JWT when AUTH_DISABLED=false.
# /health and /internal/v1/* stay open (C21 guards /internal/v1/* separately).
client_auth = [Depends(require_user)]


@app.middleware("http")
async def internal_service_token_guard(request: Request, call_next):
    """C21: require X-Service-Token on /internal/v1/* when strict mode is on."""
    if settings.internal_auth_disabled:
        return await call_next(request)
    if request.url.path.startswith("/internal/v1/"):
        token = request.headers.get("x-service-token")
        if not token or token != settings.internal_service_token:
            return JSONResponse(
                status_code=401,
                content={"detail": "Internal service token required"},
            )
    return await call_next(request)


app.include_router(handoffs_router)
app.include_router(entitlements_router)
app.include_router(rooms_router, dependencies=client_auth)
app.include_router(slots_router, dependencies=client_auth)
app.include_router(strategy_publications_router)
app.include_router(strategy_proposals_router, dependencies=client_auth)
app.include_router(roster_internal_router)
app.include_router(roster_router, dependencies=client_auth)
app.include_router(tasks_router, dependencies=client_auth)
app.include_router(leads_router, dependencies=client_auth)
app.include_router(meet_router, dependencies=client_auth)
app.include_router(room_health_router, dependencies=client_auth)
app.include_router(earnings_router, dependencies=client_auth)
app.include_router(room_health_internal_router)
app.include_router(termination_router, dependencies=client_auth)
app.include_router(auth_stub_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "wowlance-2"}
