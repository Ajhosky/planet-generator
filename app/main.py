from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes_planet import router as planet_router

app = FastAPI(title="Planet Genesis API", version="0.1.0")

app.mount("/generated", StaticFiles(directory="generated"), name="generated")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(planet_router, prefix="/api/planet", tags=["planet"])


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "Planet Genesis API",
        "status": "running",
    }