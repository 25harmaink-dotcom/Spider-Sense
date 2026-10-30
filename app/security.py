import os
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash


SECRET_KEY = os.environ["SPIDER_SENSE_JWT_SECRET"]

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

password_hasher = PasswordHash.recommended()


# Convert a password into a secure hash
def hash_password(password: str) -> str:
    return password_hasher.hash(password)


# Check whether a password matches its stored hash
def verify_password(password: str, password_hash: str) -> bool:
    return password_hasher.verify(password, password_hash)


# Create a signed JWT
def create_access_token(user_id: int) -> str:
    expiration = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "exp": expiration
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


# Decode and verify a JWT
def decode_access_token(token: str) -> dict:
    return jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM],
        options={"require": ["sub", "exp"]}
    )