from fastapi.testclient import TestClient
import pytest
from app.main import app
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from app.models import User, Incident
from app.security import hash_password
from app.database import Base
from app import models
from app.main import get_db


client = TestClient(app)

# Separate database for automated tests
TEST_DATABASE_URL = "sqlite:///./spider_sense_test.db"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)


@event.listens_for(test_engine, "connect")
def enable_test_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(bind=test_engine)

# Create tables in the test database



def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()



@pytest.fixture
def test_client():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(bind=test_engine)
def test_incidents_requires_authentication():
    response = client.get("/incidents")

    assert response.status_code == 401

def test_citizen_cannot_claim_incident(test_client):
    # Setup: Register a Citizen
    register_response = test_client.post(
        "/auth/register",
        json={
            "email": "testcitizen@example.com",
            "password": "TestPassword123!"
        }
    )

    assert register_response.status_code in (200, 201)

    # Setup: Log in as the Citizen
    login_response = test_client.post(
        "/auth/login",
        json={
            "email": "testcitizen@example.com",
            "password": "TestPassword123!"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    # Action: Citizen attempts to claim an incident
    response = test_client.post(
        "/hero/incidents/1/claim",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    # Assertion: Citizens cannot claim incidents
    assert response.status_code == 403    

def test_citizen_cannot_read_another_citizens_incident(test_client):

    # SETUP: Register Citizen A
    test_client.post(
        "/auth/register",
        json={
            "email": "citizen_a@example.com",
            "password": "Password123!"
        }
    )

    # SETUP: Register Citizen B
    test_client.post(
        "/auth/register",
        json={
            "email": "citizen_b@example.com",
            "password": "Password123!"
        }
    )

    # Log in as Citizen A
    login_a = test_client.post(
        "/auth/login",
        json={
            "email": "citizen_a@example.com",
            "password": "Password123!"
        }
    )

    assert login_a.status_code == 200

    token_a = login_a.json()["access_token"]

    # Citizen A creates an incident
    create_response = test_client.post(
        "/incidents",
        headers={
            "Authorization": f"Bearer {token_a}"
        },
        json={
            "title": "Broken Streetlight",
            "description": "The streetlight near the main road is broken.",
            "category": "Infrastructure",
            "severity": 3,
            "latitude": 21.1458,
            "longitude": 79.0882
        }
    )

    assert create_response.status_code == 201

    incident_id = create_response.json()["id"]

    # Log in as Citizen B
    login_b = test_client.post(
        "/auth/login",
        json={
            "email": "citizen_b@example.com",
            "password": "Password123!"
        }
    )

    assert login_b.status_code == 200

    token_b = login_b.json()["access_token"]

    # ACTION: Citizen B tries to read Citizen A's incident
    response = test_client.get(
        f"/incidents/{incident_id}",
        headers={
            "Authorization": f"Bearer {token_b}"
        }
    )

    # ASSERTION: Access must be denied
    assert response.status_code == 404    


def test_hero_can_claim_reported_incident(test_client):

    # SETUP 1: Register a Citizen
    register_response = test_client.post(
        "/auth/register",
        json={
            "email": "citizen_claim@example.com",
            "password": "Password123!"
        }
    )

    assert register_response.status_code in (200, 201)

    # SETUP 2: Log in as Citizen
    login_response = test_client.post(
        "/auth/login",
        json={
            "email": "citizen_claim@example.com",
            "password": "Password123!"
        }
    )

    assert login_response.status_code == 200

    citizen_token = login_response.json()["access_token"]

    # SETUP 3: Citizen reports an incident
    create_response = test_client.post(
        "/incidents",
        headers={
            "Authorization": f"Bearer {citizen_token}"
        },
        json={
            "title": "Road Accident",
            "description": "A road accident has occurred near the main junction.",
            "category": "Emergency",
            "severity": 4,
            "latitude": 21.1458,
            "longitude": 79.0882
        }
    )

    assert create_response.status_code == 201

    incident_id = create_response.json()["id"]

    # Verify initial status
    assert create_response.json()["status"] == "reported"

    # SETUP 4: Create Hero 1 directly in the test database
    with TestingSessionLocal() as db:
        hero = User(
            email="hero_claim@example.com",
            password_hash=hash_password("HeroPassword123!"),
            role="hero"
        )

        db.add(hero)
        db.commit()
        db.refresh(hero)

        hero_id = hero.id

    # SETUP 5: Log in as Hero 1
    hero_login = test_client.post(
        "/auth/login",
        json={
            "email": "hero_claim@example.com",
            "password": "HeroPassword123!"
        }
    )

    assert hero_login.status_code == 200

    hero_token = hero_login.json()["access_token"]

    # ACTION: Hero 1 claims the incident
    claim_response = test_client.post(
        f"/hero/incidents/{incident_id}/claim",
        headers={
            "Authorization": f"Bearer {hero_token}"
        }
    )

    # ASSERTIONS
    assert claim_response.status_code == 200

    claimed_incident = claim_response.json()

    assert claimed_incident["status"] == "claimed"
    assert claimed_incident["hero_id"] == hero_id    


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


def test_hero_cannot_skip_status(test_client):

    # SETUP 1: Register and log in a Citizen
    test_client.post(
        "/auth/register",
        json={
            "email": "citizen_status@example.com",
            "password": "Password123!"
        }
    )

    citizen_login = test_client.post(
        "/auth/login",
        json={
            "email": "citizen_status@example.com",
            "password": "Password123!"
        }
    )

    assert citizen_login.status_code == 200

    citizen_token = citizen_login.json()["access_token"]

    # SETUP 2: Citizen creates an incident
    create_response = test_client.post(
        "/incidents",
        headers={
            "Authorization": f"Bearer {citizen_token}"
        },
        json={
            "title": "Road Accident",
            "description": "A serious road accident occurred near the junction.",
            "category": "Emergency",
            "severity": 4,
            "latitude": 21.1458,
            "longitude": 79.0882
        }
    )

    assert create_response.status_code == 201

    incident_id = create_response.json()["id"]

    # SETUP 3: Create a Hero
    with TestingSessionLocal() as db:
        hero = User(
            email="hero_status@example.com",
            password_hash=hash_password("HeroPassword123!"),
            role="hero"
        )

        db.add(hero)
        db.commit()

    # SETUP 4: Log in as Hero
    hero_login = test_client.post(
        "/auth/login",
        json={
            "email": "hero_status@example.com",
            "password": "HeroPassword123!"
        }
    )

    assert hero_login.status_code == 200

    hero_token = hero_login.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {hero_token}"
    }

    # SETUP 5: Hero claims the incident
    claim_response = test_client.post(
        f"/hero/incidents/{incident_id}/claim",
        headers=headers
    )

    assert claim_response.status_code == 200
    assert claim_response.json()["status"] == "claimed"

    # ACTION: Hero attempts to skip in_progress
    response = test_client.patch(
        f"/hero/incidents/{incident_id}/status",
        headers=headers,
        json={
            "status": "resolved",
            "note": "Trying to skip in_progress"
        }
    )

    # ASSERTION: Invalid transition must be rejected
    assert response.status_code == 409

    # ASSERTION: Incident status must remain unchanged
    with TestingSessionLocal() as db:
        incident = db.get(Incident, incident_id)

        assert incident.status == "claimed"


def test_valid_status_lifecycle_and_history(test_client):

    # SETUP 1: Register a Citizen
    register_response = test_client.post(
        "/auth/register",
        json={
            "email": "citizen_lifecycle@example.com",
            "password": "Password123!"
        }
    )

    assert register_response.status_code in (200, 201)

    # SETUP 2: Log in as Citizen
    citizen_login = test_client.post(
        "/auth/login",
        json={
            "email": "citizen_lifecycle@example.com",
            "password": "Password123!"
        }
    )

    assert citizen_login.status_code == 200

    citizen_token = citizen_login.json()["access_token"]

    # SETUP 3: Citizen creates an incident
    create_response = test_client.post(
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

    assert create_response.status_code == 201

    incident_id = create_response.json()["id"]

    assert create_response.json()["status"] == "reported"

    # SETUP 4: Create Hero
    with TestingSessionLocal() as db:
        hero = User(
            email="hero_lifecycle@example.com",
            password_hash=hash_password("HeroPassword123!"),
            role="hero"
        )

        db.add(hero)
        db.commit()
        db.refresh(hero)

        hero_id = hero.id

    # SETUP 5: Log in as Hero
    hero_login = test_client.post(
        "/auth/login",
        json={
            "email": "hero_lifecycle@example.com",
            "password": "HeroPassword123!"
        }
    )

    assert hero_login.status_code == 200

    hero_token = hero_login.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {hero_token}"
    }

    # ACTION 1: Hero claims incident
    claim_response = test_client.post(
        f"/hero/incidents/{incident_id}/claim",
        headers=headers
    )

    assert claim_response.status_code == 200
    assert claim_response.json()["status"] == "claimed"

    # ACTION 2: Hero starts working
    progress_response = test_client.patch(
        f"/hero/incidents/{incident_id}/status",
        headers=headers,
        json={
            "status": "in_progress",
            "note": "Hero has started working"
        }
    )

    assert progress_response.status_code == 200
    assert progress_response.json()["status"] == "in_progress"

    # ACTION 3: Hero resolves incident
    resolve_response = test_client.patch(
        f"/hero/incidents/{incident_id}/status",
        headers=headers,
        json={
            "status": "resolved",
            "note": "Incident successfully resolved"
        }
    )

    assert resolve_response.status_code == 200
    assert resolve_response.json()["status"] == "resolved"

    # ACTION 4: Retrieve incident history
    history_response = test_client.get(
        f"/hero/incidents/{incident_id}/history",
        headers=headers
    )

    assert history_response.status_code == 200

    history = history_response.json()

    # ASSERTION 1: The report and three hero transitions are recorded
    assert len(history) == 4

    # ASSERTION 2: Correct transition sequence
    assert [entry["next_status"] for entry in history] == [
        "reported",
        "claimed",
        "in_progress",
        "resolved"
    ]

    # ASSERTION 3: All actions performed by Hero
    assert all(
        entry["actor_id"] == hero_id
        for entry in history[1:]
    )

    # ASSERTION 4: Every event has a timestamp
    assert all(
        entry["created_at"] is not None
        for entry in history
    )

    # ASSERTION 5: Final database state
    with TestingSessionLocal() as db:
        incident = db.get(Incident, incident_id)

        assert incident.status == "resolved"
        assert incident.hero_id == hero_id        


def test_invalid_severity_returns_422(test_client):

    # SETUP 1: Register a Citizen
    register_response = test_client.post(
        "/auth/register",
        json={
            "email": "citizen_severity@example.com",
            "password": "Password123!"
        }
    )

    assert register_response.status_code in (200, 201)

    # SETUP 2: Log in as Citizen
    login_response = test_client.post(
        "/auth/login",
        json={
            "email": "citizen_severity@example.com",
            "password": "Password123!"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # ACTION 1: Submit severity greater than 5
    response_high = test_client.post(
        "/incidents",
        headers=headers,
        json={
            "title": "Road Accident",
            "description": "A serious accident occurred near the junction.",
            "category": "Emergency",
            "severity": 6,
            "latitude": 21.1458,
            "longitude": 79.0882
        }
    )

    # ASSERTION 1: Severity 6 must be rejected
    assert response_high.status_code == 422

    # ACTION 2: Submit severity below 1
    response_low = test_client.post(
        "/incidents",
        headers=headers,
        json={
            "title": "Road Accident",
            "description": "A serious accident occurred near the junction.",
            "category": "Emergency",
            "severity": 0,
            "latitude": 21.1458,
            "longitude": 79.0882
        }
    )

    # ASSERTION 2: Severity 0 must be rejected
    assert response_low.status_code == 422

    # ASSERTION 3: No incidents should have been created
    with TestingSessionLocal() as db:
        incidents = db.query(Incident).all()

        assert len(incidents) == 0        

def test_combined_filters_and_pagination(test_client):

    # SETUP 1: Register a Citizen
    test_client.post(
        "/auth/register",
        json={
            "email": "citizen_filters@example.com",
            "password": "Password123!"
        }
    )

    # Log in
    login_response = test_client.post(
        "/auth/login",
        json={
            "email": "citizen_filters@example.com",
            "password": "Password123!"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # SETUP 2: Create five incidents
    incident_data = [
        ("Fire Incident 1", "Fire", 5),
        ("Fire Incident 2", "Fire", 5),
        ("Fire Incident 3", "Fire", 3),
        ("Medical Incident", "Medical", 5),
        ("Fire Incident 4", "Fire", 5),
    ]

    for title, category, severity in incident_data:

        response = test_client.post(
            "/incidents",
            headers=headers,
            json={
                "title": title,
                "description": "An emergency incident requiring assistance.",
                "category": category,
                "severity": severity,
                "latitude": 21.1458,
                "longitude": 79.0882
            }
        )

        assert response.status_code == 201

    # ACTION: Apply combined filters and request page 2
    response = test_client.get(
        "/incidents",
        headers=headers,
        params={
            "status": "reported",
            "category": "Fire",
            "severity": 5,
            "page": 2,
            "page_size": 2
        }
    )

    # ASSERTIONS
    assert response.status_code == 200

    data = response.json()

    # Three incidents match the filters
    assert data["total"] == 3

    # We requested page 2
    assert data["page"] == 2

    # Page size should be 2
    assert data["page_size"] == 2

    # Three matching incidents require two pages
    assert data["total_pages"] == 2

    # Only one matching incident remains on page 2
    assert len(data["items"]) == 1

    # Verify the returned incident matches every filter
    incident = data["items"][0]

    assert incident["status"] == "reported"
    assert incident["category"] == "Fire"
    assert incident["severity"] == 5        


def test_citizen_data_isolation_with_filters(test_client):

    # SETUP 1: Register two Citizens
    for email in [
        "citizen_a_filter@example.com",
        "citizen_b_filter@example.com"
    ]:
        response = test_client.post(
            "/auth/register",
            json={
                "email": email,
                "password": "Password123!"
            }
        )

        assert response.status_code in (200, 201)

    # SETUP 2: Log in both Citizens
    login_a = test_client.post(
        "/auth/login",
        json={
            "email": "citizen_a_filter@example.com",
            "password": "Password123!"
        }
    )

    login_b = test_client.post(
        "/auth/login",
        json={
            "email": "citizen_b_filter@example.com",
            "password": "Password123!"
        }
    )

    assert login_a.status_code == 200
    assert login_b.status_code == 200

    headers_a = {
        "Authorization": f"Bearer {login_a.json()['access_token']}"
    }

    headers_b = {
        "Authorization": f"Bearer {login_b.json()['access_token']}"
    }

    # SETUP 3: Citizen A creates two Fire incidents
    for i in range(2):
        response = test_client.post(
            "/incidents",
            headers=headers_a,
            json={
                "title": f"Citizen A Fire {i + 1}",
                "description": "Fire emergency reported by Citizen A.",
                "category": "Fire",
                "severity": 5,
                "latitude": 21.1458,
                "longitude": 79.0882
            }
        )

        assert response.status_code == 201

    # SETUP 4: Citizen B creates one Fire incident
    response_b = test_client.post(
        "/incidents",
        headers=headers_b,
        json={
            "title": "Citizen B Fire",
            "description": "Fire emergency reported by Citizen B.",
            "category": "Fire",
            "severity": 5,
            "latitude": 21.1458,
            "longitude": 79.0882
        }
    )

    assert response_b.status_code == 201

    citizen_b_incident_id = response_b.json()["id"]

    # ACTION: Citizen A requests filtered incidents
    response = test_client.get(
        "/incidents",
        headers=headers_a,
        params={
            "category": "Fire",
            "page": 1,
            "page_size": 10
        }
    )

    # ASSERTION 1: Request succeeds
    assert response.status_code == 200

    data = response.json()

    # ASSERTION 2: Only Citizen A's incidents are counted
    assert data["total"] == 2

    # ASSERTION 3: Only Citizen A's incidents are returned
    assert len(data["items"]) == 2

    # ASSERTION 4: Citizen B's incident is not exposed
    returned_ids = [
        incident["id"]
        for incident in data["items"]
    ]

    assert citizen_b_incident_id not in returned_ids    

def test_frontend_history_and_hero_missions_are_scoped(test_client):
    """The added dashboard endpoints must enforce ownership and role boundaries."""
    for email in ('owner@example.com', 'other@example.com'):
        assert test_client.post('/auth/register', json={'email': email, 'password': 'Password123!'}).status_code == 201
    def login(email):
        r = test_client.post('/auth/login', json={'email': email, 'password': 'Password123!'})
        assert r.status_code == 200
        return {'Authorization': f"Bearer {r.json()['access_token']}"}
    owner, other = login('owner@example.com'), login('other@example.com')
    with TestingSessionLocal() as db:
        db.add_all([User(email='hero-a@example.com', password_hash=hash_password('Password123!'), role='hero'), User(email='hero-b@example.com', password_hash=hash_password('Password123!'), role='hero')])
        db.commit()
    hero, other_hero = login('hero-a@example.com'), login('hero-b@example.com')
    incident = test_client.post('/incidents', headers=owner, json={'title':'Test incident','description':'A detailed test report','category':'Test','severity':3,'latitude':21.1,'longitude':79.1})
    assert incident.status_code == 201
    incident_id = incident.json()['id']
    assert test_client.get(f'/incidents/{incident_id}/history', headers=owner).json()[0]['next_status'] == 'reported'
    assert test_client.get(f'/incidents/{incident_id}/history', headers=other).status_code == 404
    assert test_client.get(f'/incidents/{incident_id}/history', headers=hero).status_code == 403
    assert test_client.get('/hero/my-incidents', headers=owner).status_code == 403
    assert test_client.post(f'/hero/incidents/{incident_id}/claim', headers=hero).status_code == 200
    assert test_client.post(f'/hero/incidents/{incident_id}/claim', headers=other_hero).status_code == 409
    assert [item['id'] for item in test_client.get('/hero/my-incidents', headers=hero).json()] == [incident_id]
    assert test_client.get('/hero/my-incidents', headers=other_hero).json() == []
    for status in ('in_progress', 'resolved'):
        assert test_client.patch(f'/hero/incidents/{incident_id}/status', headers=hero, json={'status':status}).status_code == 200
    assert [h['next_status'] for h in test_client.get(f'/incidents/{incident_id}/history', headers=owner).json()] == ['reported','claimed','in_progress','resolved']
