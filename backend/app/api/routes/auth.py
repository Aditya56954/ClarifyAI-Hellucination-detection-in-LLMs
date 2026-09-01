from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.db.crud import get_user_by_email
from app.schemas.auth import UserLogin, UserRegister, TokenResponse
from app.services.auth import login_user, register_user


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post("/register")
def register(
    user_data: UserRegister,
    db: Session = Depends(get_db),
):
    """Register a new ClarifyAI user."""

    # Check whether the email is already registered.
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

    except Exception:
        # Roll back the transaction so the current database
        # session is left in a usable state.
        db.rollback()

        # Do not expose the underlying exception to the client
        # or print it to application output. Database exceptions
        # can contain SQL, table names, connection information,
        # or other internal implementation details.
        raise HTTPException(
            status_code=500,
            detail="Could not register user.",
        )


@router.post("/login", response_model=TokenResponse)
def login(
    user_data: UserLogin,
    db: Session = Depends(get_db),
):
    """Authenticate a user and return an access token."""

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
    """Return the authenticated user's public profile."""

    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
    }