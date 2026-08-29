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
    return pwd_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    return pwd_context.verify(
        plain_password,
        hashed_password,
    )


def register_user(
    db: Session,
    user_data: UserRegister,
):
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

    user = get_user_by_email(
        db=db,
        email=user_data.email,
    )

    print("LOGIN EMAIL:", user_data.email)
    print("USER FOUND:", user is not None)

    if user is None:
        return None

    print("STORED HASH:", user.password_hash)

    password_valid = verify_password(
        user_data.password,
        user.password_hash,
    )

    print("PASSWORD VALID:", password_valid)

    if not password_valid:
        return None

    return create_access_token(user.id)