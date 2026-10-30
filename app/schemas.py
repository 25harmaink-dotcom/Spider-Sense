from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import Literal
class IncidentStatusUpdate(BaseModel):

    model_config = ConfigDict(extra="forbid")

    status: Literal["in_progress", "resolved"]

    note: str | None = Field(default=None, max_length=500)
# Data required when registering
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


# Data required when logging in
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# Information returned about a user
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: str

    model_config = ConfigDict(from_attributes=True)


# Response returned after successful login
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
# ---------------- INCIDENT SCHEMAS ----------------

class IncidentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10)
    category: str = Field(min_length=2, max_length=50)

    severity: int = Field(ge=1, le=5, strict=True)

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class IncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    citizen_id: int
    hero_id: int | None
    title: str
    description: str
    category: str
    severity: int

    latitude: float
    longitude: float

    status: str
    created_at: datetime
    updated_at: datetime    
# ---------------- STATUS UPDATE SCHEMA ----------------

class IncidentStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["in_progress", "resolved"]
    note: str | None = Field(default=None, max_length=500)


# ---------------- STATUS HISTORY RESPONSE ----------------

class StatusHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    incident_id: int
    actor_id: int

    previous_status: str | None
    next_status: str

    note: str | None
    created_at: datetime        

class StatusHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    incident_id: int
    actor_id: int

    previous_status: str | None
    next_status: str

    note: str | None
    created_at: datetime    


class PaginatedIncidents(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: list[IncidentResponse]    

def test_second_hero_cannot_claim_same_incident(test_client):

    # SETUP 1: Register a Citizen
    test_client.post(
        "/auth/register",
        json={
            "email": "citizen_double@example.com",
            "password": "Password123!"
        }
    )

    # Log in as Citizen
    citizen_login = test_client.post(
        "/auth/login",
        json={
            "email": "citizen_double@example.com",
            "password": "Password123!"
        }
    )

    assert citizen_login.status_code == 200

    citizen_token = citizen_login.json()["access_token"]

    # SETUP 2: Citizen creates an incident
    incident_response = test_client.post(
        "/incidents",
        headers={
            "Authorization": f"Bearer {citizen_token}"
        },
        json={
            "title": "Building Fire",
            "description": "A fire has started inside a residential building.",
            "category": "Fire",
            "severity": 5,
            "latitude": 21.1458,
            "longitude": 79.0882
        }
    )

    assert incident_response.status_code == 201

    incident_id = incident_response.json()["id"]

    # SETUP 3: Create two Heroes
    with TestingSessionLocal() as db:

        hero1 = User(
            email="hero1_double@example.com",
            password_hash=hash_password("HeroPassword123!"),
            role="hero"
        )

        hero2 = User(
            email="hero2_double@example.com",
            password_hash=hash_password("HeroPassword123!"),
            role="hero"
        )

        db.add_all([hero1, hero2])
        db.commit()

        db.refresh(hero1)
        db.refresh(hero2)

        hero1_id = hero1.id

    # SETUP 4: Log in as both Heroes
    login1 = test_client.post(
        "/auth/login",
        json={
            "email": "hero1_double@example.com",
            "password": "HeroPassword123!"
        }
    )

    login2 = test_client.post(
        "/auth/login",
        json={
            "email": "hero2_double@example.com",
            "password": "HeroPassword123!"
        }
    )

    assert login1.status_code == 200
    assert login2.status_code == 200

    token1 = login1.json()["access_token"]
    token2 = login2.json()["access_token"]

    # ACTION 1: Hero 1 claims the incident
    claim1 = test_client.post(
        f"/hero/incidents/{incident_id}/claim",
        headers={
            "Authorization": f"Bearer {token1}"
        }
    )

    assert claim1.status_code == 200

    # ACTION 2: Hero 2 attempts to claim the same incident
    claim2 = test_client.post(
        f"/hero/incidents/{incident_id}/claim",
        headers={
            "Authorization": f"Bearer {token2}"
        }
    )

    # ASSERTION 1: Second claim must fail
    assert claim2.status_code == 409

    # ASSERTION 2: Hero 1 must remain the owner
    with TestingSessionLocal() as db:
        incident = db.get(Incident, incident_id)

        assert incident.hero_id == hero1_id
        assert incident.status == "claimed"    