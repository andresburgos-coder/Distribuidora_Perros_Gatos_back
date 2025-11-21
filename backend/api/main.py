"""
FastAPI main entry point
Distribuidora Perros y Gatos Backend
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.config import settings
from app.database import init_db, close_db
from app.middleware.error_handler import setup_error_handlers
from app.routers import (
    auth_router,
    categories_router,
    products_router,
    inventory_router,
    carousel_router,
    orders_router,
    admin_users_router,
    home_products_router
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager para startup/shutdown events
    Handles database initialization and cleanup
    """
    # Startup
    print("Starting Distribuidora Perros y Gatos Backend API")
    try:
        init_db()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Warning: Could not initialize database: {str(e)}")
        print("Application will continue without database connection")
        # Don't raise - allow app to start for development
    
    yield
    
    # Shutdown
    print("Shutting down API")
    try:
        close_db()
        print("Database connections closed")
    except Exception as e:
        print(f"Error closing database: {str(e)}")


# Crear aplicación FastAPI
app = FastAPI(
    title="Distribuidora Perros y Gatos API",
    description="Backend API para tienda de productos para mascotas",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware para hosts de confianza
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Setup error handlers
setup_error_handlers(app)


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "success",
        "message": "API is healthy",
        "version": "1.0.0"
    }


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "status": "success",
        "message": "Bienvenido a Distribuidora Perros y Gatos API",
        "docs": "/docs"
    }


# Importar y incluir routers
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(categories_router, tags=["Categories"])
app.include_router(products_router, tags=["Products"])
app.include_router(inventory_router, tags=["Inventory"])
app.include_router(carousel_router, tags=["Carousel"])
app.include_router(orders_router, tags=["Orders"])
app.include_router(admin_users_router, tags=["Admin Users"])
app.include_router(home_products_router, tags=["Home Products"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
