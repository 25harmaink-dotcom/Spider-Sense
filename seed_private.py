"""Create one privileged user in the configured database, interactively.

Never run the fixed-password seed_heroes.py on a public deployment.
Run this locally with DATABASE_URL set to your hosted database URL.
"""
import getpass
from sqlalchemy import select
from app.database import SessionLocal
from app.models import User
from app.security import hash_password

role = input('Role (hero or command): ').strip().lower()
if role not in {'hero', 'command'}:
    raise SystemExit('Role must be hero or command.')
email = input('Email: ').strip().lower()
if not email or '@' not in email:
    raise SystemExit('Enter a valid email address.')
password = getpass.getpass('Password (not displayed): ')
if len(password) < 12:
    raise SystemExit('Use at least 12 characters.')
if password != getpass.getpass('Confirm password: '):
    raise SystemExit('Passwords did not match.')
with SessionLocal() as db:
    if db.scalar(select(User).where(User.email == email)):
        raise SystemExit('An account with that email already exists; no changes made.')
    db.add(User(email=email, role=role, password_hash=hash_password(password)))
    db.commit()
print(f'{role.capitalize()} account created.')
