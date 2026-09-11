from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.config import get_backend_config
from src.features.health.router import health_router
from src.features.licenses.router import licenses_router

config = get_backend_config()

app = FastAPI()

app.include_router(health_router)
app.include_router(licenses_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in config.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)
