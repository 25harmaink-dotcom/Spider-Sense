"""Same-origin deployment: serve the existing API at /api and the built UI at /.

This wrapper is deliberately separate from app.main, so the existing local API
and development proxy keep working unchanged.
"""
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.main import app as api
import app.models  # register models before create_all


@asynccontextmanager
async def lifespan(app):
    if not os.environ.get('DATABASE_URL'):
        raise RuntimeError('DATABASE_URL is required for the hosted version')
    if not os.environ.get('SPIDER_SENSE_AUDIT_SECRET'):
        raise RuntimeError('SPIDER_SENSE_AUDIT_SECRET is required')
    # Creates missing tables on a new database; this is not a schema migration.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title='Spider-Sense hosted application', lifespan=lifespan)

@app.get('/health')
def health():
    return {'status': 'ok'}

app.mount('/api', api)
app.mount('/', StaticFiles(directory=Path(__file__).resolve().parent.parent / 'frontend' / 'dist', html=True), name='frontend')
