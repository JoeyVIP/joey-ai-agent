import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.database import get_db
from src.database.models import User
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)


class GitHubUserCreate(BaseModel):
    github_id: str
    username: str
    email: Optional[str] = None
    avatar_url: Optional[str] = None


@router.post("/github-login")
async def github_login(user_data: GitHubUserCreate, db: Session = Depends(get_db)):
    """
    GitHub OAuth callback handler.
    Creates or updates user based on GitHub profile.
    """
    try:
        # Check if user exists
        user = db.query(User).filter(User.github_id == user_data.github_id).first()

        if user:
            # Update existing user
            user.username = user_data.username
            user.email = user_data.email
            user.avatar_url = user_data.avatar_url
            logger.info(f"Updated existing user: {user.username}")
        else:
            # Create new user
            user = User(
                github_id=user_data.github_id,
                username=user_data.username,
                email=user_data.email,
                avatar_url=user_data.avatar_url
            )
            db.add(user)
            logger.info(f"Created new user: {user.username}")

        db.commit()
        db.refresh(user)

        return {
            "id": user.id,
            "github_id": user.github_id,
            "username": user.username,
            "email": user.email,
            "avatar_url": user.avatar_url,
            "created_at": user.created_at.isoformat()
        }

    except Exception as e:
        db.rollback()
        logger.error(f"GitHub login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process GitHub login: {str(e)}"
        )


@router.get("/me")
async def get_current_user(user_id: int, db: Session = Depends(get_db)):
    """
    Get current user info.
    In production, user_id would come from JWT token.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user.id,
        "github_id": user.github_id,
        "username": user.username,
        "email": user.email,
        "avatar_url": user.avatar_url,
        "created_at": user.created_at.isoformat()
    }
