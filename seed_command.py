import getpass

from sqlalchemy import select

from app.database import SessionLocal
from app.models import User
from app.security import hash_password


email = input("Enter Command email: ").strip().lower()
password = getpass.getpass("Enter Command password: ")

if len(password) < 8:
    raise ValueError("Password must contain at least 8 characters")

with SessionLocal() as db:
    existing = db.scalar(
        select(User).where(User.email == email)
    )

    if existing:
        raise ValueError(
            "This email is already registered"
        )

    command = User(
        email=email,
        password_hash=hash_password(password),
        role="command"
    )

    db.add(command)
    db.commit()

print("Command account created successfully!")