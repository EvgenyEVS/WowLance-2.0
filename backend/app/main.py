"""WowLance 2.0 API skeleton (FastAPI + PostgreSQL)."""

from fastapi import FastAPI

app = FastAPI(
    title="WowLance 2.0",
    description="Room microservice — see /docs and repo contracts/",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "wowlance-2"}
