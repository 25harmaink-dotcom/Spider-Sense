import os
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / 'spider_sense.db'

# Keep the original local SQLite default. The hosted version uses Neon Postgres.
DATABASE_URL = os.environ.get('DATABASE_URL') or f'sqlite:///{DATABASE_PATH.as_posix()}'
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = 'postgresql+psycopg://' + DATABASE_URL[len('postgres://'):]
elif DATABASE_URL.startswith('postgresql://'):
    DATABASE_URL = 'postgresql+psycopg://' + DATABASE_URL[len('postgresql://'):]

is_sqlite = DATABASE_URL.startswith('sqlite:')
engine = create_engine(
    DATABASE_URL,
    connect_args={'check_same_thread': False} if is_sqlite else {},
    pool_pre_ping=True,
)

if is_sqlite:
    @event.listens_for(engine, 'connect')
    def enable_foreign_keys(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute('PRAGMA foreign_keys=ON')
        finally:
            cursor.close()

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    pass
