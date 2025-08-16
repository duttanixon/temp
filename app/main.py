from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import (
    auth_router,
    users_router,
    customers_router,
    devices_router,
    solutions_router,
    device_solutions_router,
    customer_solutions_router,
    device_metrics_router,
    city_eye_analytics_router,
    device_commands_router,
    sse_router,
    audit_logs_router,
    jobs_router,
    ai_models_router,
    solution_packages_router,
)
from app.core.config import settings
from app.api import deps
from app.api.middleware import RequestLoggingMiddleware
from app.utils.logger import get_logger

# Initialize logger
logger = get_logger("app")

app = FastAPI(
    title="Edge Device Management API",
    description="API for managing IoT edge devices and AI solutions",
    version="0.1.0",
)

# Set up CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Include API routes
app.include_router(
    auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["authentication"]
)
app.include_router(users_router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(
    customers_router, prefix=f"{settings.API_V1_STR}/customers", tags=["customers"]
)
app.include_router(
    devices_router, prefix=f"{settings.API_V1_STR}/devices", tags=["devices"]
)
app.include_router(
    solutions_router, prefix=f"{settings.API_V1_STR}/solutions", tags=["solutions"]
)
app.include_router(
    device_solutions_router,
    prefix=f"{settings.API_V1_STR}/device-solutions",
    tags=["device-solutions"],
)
app.include_router(
    customer_solutions_router,
    prefix=f"{settings.API_V1_STR}/customer-solutions",
    tags=["customer-solutions"],
)
app.include_router(
    device_metrics_router,
    prefix=f"{settings.API_V1_STR}/device-metrics",
    tags=["device-metrics"],
)

app.include_router(
    city_eye_analytics_router,
    prefix=f"{settings.API_V1_STR}/analytics/city-eye",
    tags=["analytics-city-eye"],
)

app.include_router(
    device_commands_router,
    prefix=f"{settings.API_V1_STR}/device-commands",
    tags=["device-commands"],
)

app.include_router(
    sse_router,
    prefix=f"{settings.API_V1_STR}/sse",
    tags=["sse"],
)

app.include_router(
    audit_logs_router,
    prefix=f"{settings.API_V1_STR}/audit-logs",
    tags=["audit-logs"],
)

app.include_router(
    jobs_router,
    prefix=f"{settings.API_V1_STR}/jobs",
    tags=["jobs"],
)

app.include_router(
    ai_models_router,
    prefix=f"{settings.API_V1_STR}/ai-models",
    tags=["ai-models"],
)

app.include_router(
    solution_packages_router,
    prefix=f"{settings.API_V1_STR}/solution-packages",
    tags=["solution-packages"],
)

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting Edge Device Management API")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Edge Device Management API")


@app.get("/")
def read_root():
    return {"message": "Welcome to Edge Device Management API"}


@app.get("/health")
def health_check():
    return {"status": "ok"}
