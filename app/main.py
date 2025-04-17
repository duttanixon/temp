from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import auth_router, users_router, customers_router
from app.core.config import settings
from app.api import deps

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
# Include API routes
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["authentication"])
app.include_router(users_router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(customers_router, prefix=f"{settings.API_V1_STR}/customers", tags=["customers"])    


@app.get("/")
def read_root():
    return {"message": "Welcome to Edge Device Management API"}


@app.get("/health")
def health_check():
    return {"status": "ok"}