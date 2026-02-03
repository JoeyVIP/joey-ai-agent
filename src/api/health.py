from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Joey's AI Agent is running"}


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
