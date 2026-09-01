from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.db.crud import create_user, get_user_by_email
from app.schemas.auth import UserLogin, UserRegister
from app.services.jwt import create_access_token


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    """Hash a user's password before storing it."""
    return pwd_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """Verify a plaintext password against its stored hash."""
    return pwd_context.verify(
        plain_password,
        hashed_password,
    )


def register_user(
    db: Session,
    user_data: UserRegister,
):
    """Create a new user with a securely hashed password."""
    password_hash = hash_password(user_data.password)

    return create_user(
        db=db,
        name=user_data.name,
        email=user_data.email,
        password_hash=password_hash,
    )


def login_user(
    db: Session,
    user_data: UserLogin,
) -> str | None:
    """Authenticate a user and return a JWT access token."""

    user = get_user_by_email(
        db=db,
        email=user_data.email,
    )

    if user is None:
        return None

    password_valid = verify_password(
        user_data.password,
        user.password_hash,
    )

    if not password_valid:
        return None

    return create_access_token(user.id)