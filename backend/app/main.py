from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import auth_router, users_router, customers_router, devices_router, solutions_router, device_solutions_router, customer_solutions_router
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
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["authentication"])
app.include_router(users_router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(customers_router, prefix=f"{settings.API_V1_STR}/customers", tags=["customers"])
app.include_router(devices_router, prefix=f"{settings.API_V1_STR}/devices", tags=["devices"])
app.include_router(solutions_router, prefix=f"{settings.API_V1_STR}/solutions", tags=["solutions"])
app.include_router(device_solutions_router, prefix=f"{settings.API_V1_STR}/device-solutions", tags=["device-solutions"])
app.include_router(customer_solutions_router, prefix=f"{settings.API_V1_STR}/customer-solutions", tags=["customer-solutions"])


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