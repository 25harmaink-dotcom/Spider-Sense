from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker


# ---------------- DATABASE CONFIGURATION ----------------

# Absolute path to the project root
BASE_DIR = Path(__file__).resolve().parent.parent

# SQLite database location
DATABASE_PATH = BASE_DIR / "spider_sense.db"

DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"


# ---------------- DATABASE ENGINE ----------------

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
)


# ---------------- ENABLE FOREIGN KEYS ----------------

@event.listens_for(engine, "connect")
def enable_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
    finally:
        cursor.close()


# ---------------- DATABASE SESSION ----------------

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


# ---------------- BASE MODEL ----------------

class Base(DeclarativeBase):
    pass