from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
from app.api.endpoints import stops, service_days, routes, trips, buses, auth
from app.data_source.gtfs.stcp.models import *
from app.services.bus_service import run_periodic_bus_updates
from app.api.utils.error_handler import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start background task for periodic bus updates
    import asyncio
    update_task = asyncio.create_task(run_periodic_bus_updates(interval_seconds=15))
    yield
    update_task.cancel()
    try:
        await update_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="Porto Transport API",
    description="Unofficial API for public transport data for the city of Porto",
    version="1.0.0",
    lifespan=lifespan,
)

cors_origins = ["*"] if settings.CORS_ORIGINS == "*" else [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(stops.router, prefix="/api/v1/stcp")
app.include_router(service_days.router, prefix="/api/v1/stcp")
app.include_router(routes.router, prefix="/api/v1/stcp")
app.include_router(trips.router, prefix="/api/v1/stcp")
app.include_router(buses.router, prefix="/api/v1/stcp")


@app.get("/")
async def root():
    return {"message": "Porto Transport API"}