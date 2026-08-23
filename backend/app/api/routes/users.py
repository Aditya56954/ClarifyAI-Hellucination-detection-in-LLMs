from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.crud import create_user, get_user_by_id

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/")
def create_test_user(
    name: str,
    email: str,
    db: Session = Depends(get_db),
):
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
):
    user = get_user_by_id(db, user_id)

    if user is None:
        return {"error": "User not found"}

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
    }