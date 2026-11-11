
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker


# Load the existing application credentials.
# This does not modify the .env file.
BACKEND_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

load_dotenv(os.path.join(BACKEND_DIR, ".env"))


# Use a fixed, dedicated database name for testing.
TEST_DATABASE_NAME = "medication_inventory_test"


def create_test_engine():
    database_url = URL.create(
        drivername="postgresql+psycopg",
        username=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        host=os.environ.get("DB_HOST", "localhost"),
        port=int(os.environ.get("DB_PORT", "5432")),
        database=TEST_DATABASE_NAME,
    )

    # Safety check before opening a connection.
    if database_url.database != "medication_inventory_test":
        raise RuntimeError(
            "Unsafe database configuration: "
            "integration tests must use medication_inventory_test."
        )

    engine = create_engine(
        database_url,
        pool_pre_ping=True,
    )

    # Verify the actual connected database.
    try:
        with engine.connect() as connection:
            actual_database = connection.execute(
                text("SELECT current_database()")
            ).scalar_one()

            if actual_database != TEST_DATABASE_NAME:
                raise RuntimeError(
                    "Unsafe database connection: "
                    f"connected to {actual_database!r}."
                )
    except Exception:
        engine.dispose()
        raise

    return engine


def get_test_session_factory():
    engine = create_test_engine()

    session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    return engine, session_factory
