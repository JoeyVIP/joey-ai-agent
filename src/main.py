import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.config import settings
from src.api.health import router as health_router
from src.api.line_webhook import router as line_router
from src.api.auth import router as auth_router
from src.api.projects import router as projects_router
from src.api.uploads import router as uploads_router
from src.database import engine, Base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info(f"Starting Joey's AI Agent in {settings.app_env} mode")
    logger.info(f"Server: {settings.host}:{settings.port}")

    # Create database tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")

    yield
    logger.info("Shutting down Joey's AI Agent")


app = FastAPI(
    title="Joey's AI Agent",
    description="LINE → Claude → Notion AI Assistant + Web Frontend API",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
cors_origins = settings.cors_origins.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(line_router)
app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(uploads_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.app_env == "development"
    )
