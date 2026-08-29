from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.schemas.auth import UserLogin, UserRegister, TokenResponse
from app.services.auth import login_user, register_user
from app.db.crud import get_user_by_email


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post("/register")
def register(
    user_data: UserRegister,
    db: Session = Depends(get_db),
):
    # Check whether email already exists
    existing_user = get_user_by_email(
        db=db,
        email=user_data.email,
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="An account with this email already exists.",
        )

    try:
        user = register_user(
            db=db,
            user_data=user_data,
        )

        return {
            "message": "User registered successfully",
            "user_id": user.id,
            "name": user.name,
            "email": user.email,
        }

    except Exception as error:
        db.rollback()

        print("REGISTER ERROR:", repr(error))

        raise HTTPException(
            status_code=500,
            detail="Could not register user.",
        )


@router.post("/login", response_model=TokenResponse)
def login(
    user_data: UserLogin,
    db: Session = Depends(get_db),
):
    token = login_user(
        db=db,
        user_data=user_data,
    )

    if token is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    return TokenResponse(
        access_token=token,
    )


@router.get("/me")
def get_me(
    current_user=Depends(get_current_user),
):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
    }