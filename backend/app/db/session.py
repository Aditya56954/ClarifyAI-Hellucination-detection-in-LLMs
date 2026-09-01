from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings


# Read the database connection string from the application's
# environment-backed configuration instead of hardcoding
# PostgreSQL credentials or connection details in source code.
engine = create_engine(
    settings.database_url,
    echo=False,
)


# Create a reusable SQLAlchemy session factory.
# Individual requests obtain their own database session
# through the dependency defined in app/api/deps.py.
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)