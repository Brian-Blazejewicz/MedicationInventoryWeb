
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

# Load environment variables from backend/.env
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Build the database URL safely, including passwords
# containing special characters.
DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    host=os.environ.get("DB_HOST", "localhost"),
    port=int(os.environ.get("DB_PORT", "5432")),
    database=os.environ["DB_NAME"],
)

# Create the SQLAlchemy database engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Create database sessions for future API requests
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def test_connection():
    """Verify that PostgreSQL accepts our connection."""
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT current_database(), current_user")
        )
        database_name, username = result.one()

        print("PostgreSQL connection successful!")
        print(f"Database: {database_name}")
        print(f"User: {username}")


if __name__ == "__main__":
    test_connection()
