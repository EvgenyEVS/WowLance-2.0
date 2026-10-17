"""WowLance 2.0 API (FastAPI + PostgreSQL)."""

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth_stub import router as auth_stub_router
from app.api.entitlements import router as entitlements_router
from app.api.handoffs import router as handoffs_router
from app.api.leads import router as leads_router
from app.api.rooms import router as rooms_router
from app.api.roster import internal_router as roster_internal_router
from app.api.roster import router as roster_router
from app.api.slots import router as slots_router
from app.api.strategy_proposals import router as strategy_proposals_router
from app.api.strategy_publications import router as strategy_publications_router
from app.api.tasks import router as tasks_router
from app.auth.deps import require_user

app = FastAPI(
    title="WowLance 2.0",
    description="Room microservice — see /docs and repo contracts/",
    version="0.1.0",
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
# /health and /internal/v1/* stay open (service token later — do not protect them).
client_auth = [Depends(require_user)]

app.include_router(handoffs_router)
app.include_router(entitlements_router)
app.include_router(rooms_router, dependencies=client_auth)
app.include_router(slots_router, dependencies=client_auth)
app.include_router(strategy_publications_router)
app.include_router(strategy_proposals_router, dependencies=client_auth)
app.include_router(roster_internal_router)
<<<<<<< HEAD
app.include_router(roster_router, dependencies=client_auth)
app.include_router(tasks_router, dependencies=client_auth)
app.include_router(auth_stub_router)
=======
app.include_router(roster_router)
app.include_router(tasks_router)
app.include_router(leads_router)
>>>>>>> origin/feature/c9-hot-lead-crm


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "wowlance-2"}
