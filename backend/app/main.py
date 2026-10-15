"""WowLance 2.0 API (FastAPI + PostgreSQL)."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.handoffs import router as handoffs_router
from app.api.rooms import router as rooms_router

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

app.include_router(handoffs_router)
app.include_router(rooms_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "wowlance-2"}
