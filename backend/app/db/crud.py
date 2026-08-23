from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.db_models import User


def create_user(
    db: Session,
    name: str,
    email: str,
    password_hash: str | None = None,
) -> User:
    user = User(
        name=name,
        email=email,
        password_hash=password_hash,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def get_user_by_id(
    db: Session,
    user_id: int,
) -> User | None:
    statement = select(User).where(User.id == user_id)

    return db.execute(statement).scalar_one_or_none()


def get_user_by_email(
    db: Session,
    email: str,
) -> User | None:
    statement = select(User).where(User.email == email)

    return db.execute(statement).scalar_one_or_none()