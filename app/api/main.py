from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.fleet import router as fleet_router
from app.api.routes.storm import router as storm_router
from app.api.maintenance_router import router as maintenance_router

app = FastAPI(
    title="Base Fleet Orchestrator API",
    version="0.1.0",
    description="Read-only API for visualizing the battery fleet.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[ "http://localhost:5173","https://base-orchestrator.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(fleet_router)
app.include_router(storm_router)
app.include_router(maintenance_router)

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
