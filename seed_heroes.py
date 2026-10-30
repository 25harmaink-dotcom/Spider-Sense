from sqlalchemy import select

from app.database import SessionLocal
from app.models import User
from app.security import hash_password


TEST_HEROES = [
    ("hero1@example.com", "HeroOne123!"),
    ("hero2@example.com", "HeroTwo123!")
]


with SessionLocal() as db:
    for email, password in TEST_HEROES:
        existing = db.scalar(
            select(User).where(User.email == email)
        )

        if existing:
            print(f"Account already exists: {email}")
            continue

        hero = User(
            email=email,
            password_hash=hash_password(password),
            role="hero"
        )

        db.add(hero)

    db.commit()

print("Hero seed completed.")