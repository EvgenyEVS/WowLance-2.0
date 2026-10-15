"""WowLance 2.0 API (FastAPI + PostgreSQL)."""

from fastapi import FastAPI

from app.api.entitlements import router as entitlements_router
from app.api.handoffs import router as handoffs_router

app = FastAPI(
    title="WowLance 2.0",
    description="Room microservice — see /docs and repo contracts/",
    version="0.1.0",
)

app.include_router(handoffs_router)
app.include_router(entitlements_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "wowlance-2"}
