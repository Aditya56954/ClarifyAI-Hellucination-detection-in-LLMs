from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.db.crud import create_user, get_user_by_id
from app.models.db_models import User


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.post("/")
def create_test_user(
    name: str,
    email: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a user through the development-oriented users endpoint.

    This endpoint is protected by JWT authentication.
    """

    user = create_user(
        db=db,
        name=name,
        email=email,
    )

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
    }


@router.get("/{user_id}")
def get_test_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve a user by ID.

    Access requires a valid JWT.
    """

    user = get_user_by_id(
        db,
        user_id,
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
    }