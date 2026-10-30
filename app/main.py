import hmac

from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, update, func

from jwt.exceptions import InvalidTokenError

from app.database import SessionLocal
from app.models import User, Incident, StatusHistory
from app.crypto import generate_hash, generate_hmac, verify_hmac

from app.schemas import (
    UserRegister,
    UserLogin,
    UserResponse,
    TokenResponse,
    IncidentCreate,
    IncidentResponse,
    IncidentStatusUpdate,
    StatusHistoryResponse,
    PaginatedIncidents,
)

from app.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Spider-Sense Alert System",
    description="NYC incident reporting and Hero response system",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)

bearer_scheme = HTTPBearer(auto_error=False)


# ============================================================
# DATABASE DEPENDENCY
# ============================================================

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    return {"status": "ok"}


# ============================================================
# USER REGISTRATION
# ============================================================

@app.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    data: UserRegister,
    db: Session = Depends(get_db),
):
    email = data.email.lower()

    existing_user = db.scalar(
        select(User).where(User.email == email)
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email already registered",
        )

    user = User(
        email=email,
        password_hash=hash_password(data.password),
        role="citizen",
    )

    db.add(user)

    try:
        db.commit()

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Email already registered",
        )

    db.refresh(user)

    return user


# ============================================================
# USER LOGIN
# ============================================================

@app.post(
    "/auth/login",
    response_model=TokenResponse,
)
def login(
    data: UserLogin,
    db: Session = Depends(get_db),
):
    user = db.scalar(
        select(User).where(
            User.email == data.email.lower()
        )
    )

    if user is None or not verify_password(
        data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    token = create_access_token(user.id)

    return {
        "access_token": token,
        "token_type": "bearer",
    }


# ============================================================
# AUTHENTICATION DEPENDENCY
# ============================================================

def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
    db: Session = Depends(get_db),
):
    unauthorized = HTTPException(
        status_code=401,
        detail="Invalid or missing authentication token",
        headers={
            "WWW-Authenticate": "Bearer"
        },
    )

    if credentials is None:
        raise unauthorized

    try:
        payload = decode_access_token(
            credentials.credentials
        )

        user_id = int(payload["sub"])

    except (
        InvalidTokenError,
        ValueError,
        TypeError,
        KeyError,
    ):
        raise unauthorized

    user = db.get(User, user_id)

    if user is None:
        raise unauthorized

    return user


# ============================================================
# ROLE AUTHORIZATION
# ============================================================

def require_citizen(
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "citizen":
        raise HTTPException(
            status_code=403,
            detail="Only Citizens can access this endpoint",
        )

    return current_user


def require_hero(
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "hero":
        raise HTTPException(
            status_code=403,
            detail="Only Heroes can perform this action",
        )

    return current_user


def require_command(
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "command":
        raise HTTPException(
            status_code=403,
            detail="Only Command can access this endpoint",
        )

    return current_user


# ============================================================
# CURRENT USER
# ============================================================

@app.get(
    "/auth/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user


# ============================================================
# CRYPTOGRAPHIC AUDIT HISTORY
# ============================================================

def create_audit_history(
    db: Session,
    incident_id: int,
    actor_id: int,
    previous_status: str | None,
    next_status: str,
    note: str | None = None,
):
    """
    Create a SHA-256 hash-chained and HMAC-authenticated
    incident status-history record.

    This function adds the history record to the current
    database transaction but does not commit it.
    """

    previous_event = db.scalar(
        select(StatusHistory)
        .where(
            StatusHistory.incident_id == incident_id
        )
        .order_by(StatusHistory.id.desc())
        .limit(1)
    )

    if previous_event is not None:

        if (
            not previous_event.event_hash
            or not previous_event.event_hmac
        ):
            raise RuntimeError(
                "Existing incident history is not "
                "cryptographically protected. "
                "Legacy history migration is required."
            )

        previous_hash = previous_event.event_hash

    else:
        previous_hash = "GENESIS"

    event_data = {
        "incident_id": incident_id,
        "actor_id": actor_id,
        "previous_status": previous_status,
        "next_status": next_status,
        "note": note,
    }

    event_hash = generate_hash(
        event_data,
        previous_hash,
    )

    event_hmac = generate_hmac(event_hash)

    history = StatusHistory(
        incident_id=incident_id,
        actor_id=actor_id,
        previous_status=previous_status,
        next_status=next_status,
        note=note,
        previous_hash=previous_hash,
        event_hash=event_hash,
        event_hmac=event_hmac,
    )

    db.add(history)

    return history


# ============================================================
# CRYPTOGRAPHIC AUDIT VERIFICATION
# ============================================================

def verify_incident_audit(
    db: Session,
    incident_id: int,
):
    """
    Verify the integrity of an incident's audit history.

    Checks:
    1. Audit records exist.
    2. Records contain cryptographic fields.
    3. Previous hashes form a valid chain.
    4. SHA-256 hashes match the stored event data.
    5. HMAC signatures are valid.
    6. Status transitions are consistent.
    7. Final incident status matches the audit history.
    """

    incident = db.get(Incident, incident_id)

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found",
        )

    events = db.scalars(
        select(StatusHistory)
        .where(
            StatusHistory.incident_id == incident_id
        )
        .order_by(StatusHistory.id)
    ).all()

    if not events:
        return {
            "incident_id": incident_id,
            "verified": False,
            "reason": "No audit history exists",
        }

    previous_hash = "GENESIS"
    previous_status = None

    allowed_transitions = {
        None: "reported",
        "reported": "claimed",
        "claimed": "in_progress",
        "in_progress": "resolved",
    }

    for event in events:

        # Check whether cryptographic fields exist.

        if not all([
            event.previous_hash,
            event.event_hash,
            event.event_hmac,
        ]):
            return {
                "incident_id": incident_id,
                "verified": False,
                "reason": f"Unsigned legacy event: {event.id}",
            }

        # Verify the hash chain.

        if not hmac.compare_digest(
            event.previous_hash,
            previous_hash,
        ):
            return {
                "incident_id": incident_id,
                "verified": False,
                "reason": f"Broken hash chain at event {event.id}",
            }

        # Reconstruct the event data.

        event_data = {
            "incident_id": event.incident_id,
            "actor_id": event.actor_id,
            "previous_status": event.previous_status,
            "next_status": event.next_status,
            "note": event.note,
        }

        # Recalculate the SHA-256 hash.

        expected_hash = generate_hash(
            event_data,
            event.previous_hash,
        )

        if not hmac.compare_digest(
            expected_hash,
            event.event_hash,
        ):
            return {
                "incident_id": incident_id,
                "verified": False,
                "reason": f"Modified event data at event {event.id}",
            }

        # Verify the HMAC signature.

        if not verify_hmac(
            event.event_hash,
            event.event_hmac,
        ):
            return {
                "incident_id": incident_id,
                "verified": False,
                "reason": f"Invalid HMAC at event {event.id}",
            }

        # Verify status continuity.

        if event.previous_status != previous_status:
            return {
                "incident_id": incident_id,
                "verified": False,
                "reason": f"Inconsistent status at event {event.id}",
            }

        # Verify the permitted lifecycle.

        expected_next_status = allowed_transitions.get(
            previous_status
        )

        if event.next_status != expected_next_status:
            return {
                "incident_id": incident_id,
                "verified": False,
                "reason": f"Invalid status transition at event {event.id}",
            }

        previous_hash = event.event_hash
        previous_status = event.next_status

    # Compare final audit status with the incident.

    if incident.status != previous_status:
        return {
            "incident_id": incident_id,
            "verified": False,
            "reason": "Incident status does not match audit history",
        }

    return {
        "incident_id": incident_id,
        "verified": True,
        "events_verified": len(events),
        "latest_hash": previous_hash,
        "message": "Audit history integrity verified",
    }


# ============================================================
# CITIZEN: CREATE INCIDENT
# ============================================================

@app.post(
    "/incidents",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_incident(
    data: IncidentCreate,
    current_user: User = Depends(require_citizen),
    db: Session = Depends(get_db),
):
    incident = Incident(
        citizen_id=current_user.id,
        title=data.title,
        description=data.description,
        category=data.category,
        severity=data.severity,
        latitude=data.latitude,
        longitude=data.longitude,
        status="reported",
    )

    try:
        db.add(incident)

        # Obtain the incident ID before creating audit history.
        db.flush()

        create_audit_history(
            db=db,
            incident_id=incident.id,
            actor_id=current_user.id,
            previous_status=None,
            next_status="reported",
            note="Incident reported by Citizen",
        )

        db.commit()

    except Exception:
        db.rollback()
        raise

    db.refresh(incident)

    return incident


# ============================================================
# CITIZEN: LIST INCIDENTS
# ============================================================

@app.get(
    "/incidents",
    response_model=PaginatedIncidents,
)
def list_my_incidents(
    status: str | None = Query(default=None),
    category: str | None = Query(default=None),
    severity: int | None = Query(
        default=None,
        ge=1,
        le=5,
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(
        default=10,
        ge=1,
        le=100,
    ),
    current_user: User = Depends(require_citizen),
    db: Session = Depends(get_db),
):
    query = select(Incident).where(
        Incident.citizen_id == current_user.id
    )

    if status is not None:
        query = query.where(
            Incident.status == status
        )

    if category is not None:
        query = query.where(
            Incident.category == category
        )

    if severity is not None:
        query = query.where(
            Incident.severity == severity
        )

    total = db.scalar(
        select(func.count()).select_from(
            query.order_by(None).subquery()
        )
    ) or 0

    offset = (page - 1) * page_size

    incidents = db.scalars(
        query
        .order_by(
            Incident.created_at.desc(),
            Incident.id.desc(),
        )
        .offset(offset)
        .limit(page_size)
    ).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (
            total + page_size - 1
        ) // page_size,
        "items": incidents,
    }


# ============================================================
# CITIZEN: VIEW INCIDENT
# ============================================================

@app.get(
    "/incidents/{incident_id}",
    response_model=IncidentResponse,
)
def get_my_incident(
    incident_id: int,
    current_user: User = Depends(require_citizen),
    db: Session = Depends(get_db),
):
    incident = db.scalar(
        select(Incident).where(
            Incident.id == incident_id,
            Incident.citizen_id == current_user.id,
        )
    )

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found",
        )

    return incident


# ============================================================
# HERO: DISCOVER AVAILABLE INCIDENTS
# ============================================================

@app.get(
    "/hero/incidents",
    response_model=list[IncidentResponse],
)
def hero_list_incidents(
    current_user: User = Depends(require_hero),
    db: Session = Depends(get_db),
):
    incidents = db.scalars(
        select(Incident)
        .where(
            Incident.status == "reported",
            Incident.hero_id.is_(None),
        )
        .order_by(
            Incident.created_at.desc(),
            Incident.id.desc(),
        )
    ).all()

    return incidents


# ============================================================
# HERO: CLAIM INCIDENT
# ============================================================

@app.post(
    "/hero/incidents/{incident_id}/claim",
    response_model=IncidentResponse,
)
def claim_incident(
    incident_id: int,
    current_user: User = Depends(require_hero),
    db: Session = Depends(get_db),
):
    try:
        result = db.execute(
            update(Incident)
            .where(
                Incident.id == incident_id,
                Incident.hero_id.is_(None),
                Incident.status == "reported",
            )
            .values(
                hero_id=current_user.id,
                status="claimed",
            )
        )

        if result.rowcount != 1:
            db.rollback()

            existing = db.get(
                Incident,
                incident_id,
            )

            if existing is None:
                raise HTTPException(
                    status_code=404,
                    detail="Incident not found",
                )

            raise HTTPException(
                status_code=409,
                detail=(
                    "Incident is already claimed "
                    "or unavailable"
                ),
            )

        create_audit_history(
            db=db,
            incident_id=incident_id,
            actor_id=current_user.id,
            previous_status="reported",
            next_status="claimed",
            note="Incident claimed by Hero",
        )

        # Commit the incident update and history together.
        db.commit()

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise

    db.expire_all()

    return db.get(
        Incident,
        incident_id,
    )


# ============================================================
# HERO: UPDATE INCIDENT STATUS
# ============================================================

@app.patch(
    "/hero/incidents/{incident_id}/status",
    response_model=IncidentResponse,
)
def update_incident_status(
    incident_id: int,
    data: IncidentStatusUpdate,
    current_user: User = Depends(require_hero),
    db: Session = Depends(get_db),
):
    allowed_transitions = {
        "claimed": "in_progress",
        "in_progress": "resolved",
    }

    try:
        incident = db.get(
            Incident,
            incident_id,
        )

        if incident is None:
            raise HTTPException(
                status_code=404,
                detail="Incident not found",
            )

        if incident.hero_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail=(
                    "Only the claiming Hero "
                    "can update this incident"
                ),
            )

        previous_status = incident.status

        expected_next_status = (
            allowed_transitions.get(
                previous_status
            )
        )

        if data.status != expected_next_status:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Invalid transition from "
                    f"{previous_status} "
                    f"to {data.status}"
                ),
            )

        result = db.execute(
            update(Incident)
            .where(
                Incident.id == incident_id,
                Incident.hero_id == current_user.id,
                Incident.status == previous_status,
            )
            .values(
                status=data.status
            )
        )

        if result.rowcount != 1:
            db.rollback()

            raise HTTPException(
                status_code=409,
                detail=(
                    "Incident status changed "
                    "during this request"
                ),
            )

        create_audit_history(
            db=db,
            incident_id=incident_id,
            actor_id=current_user.id,
            previous_status=previous_status,
            next_status=data.status,
            note=data.note,
        )

        db.commit()

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise

    db.expire_all()

    return db.get(
        Incident,
        incident_id,
    )


# ============================================================
# HERO: VIEW INCIDENT HISTORY
# ============================================================

@app.get(
    "/hero/incidents/{incident_id}/history",
    response_model=list[StatusHistoryResponse],
)
def get_incident_history(
    incident_id: int,
    current_user: User = Depends(require_hero),
    db: Session = Depends(get_db),
):
    incident = db.get(
        Incident,
        incident_id,
    )

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found",
        )

    if incident.hero_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail=(
                "Only the claiming Hero "
                "can view this history"
            ),
        )

    history = db.scalars(
        select(StatusHistory)
        .where(
            StatusHistory.incident_id == incident_id
        )
        .order_by(
            StatusHistory.created_at,
            StatusHistory.id,
        )
    ).all()

    return history


# ============================================================
# COMMAND: VIEW ALL INCIDENTS
# ============================================================

@app.get(
    "/command/incidents",
    response_model=PaginatedIncidents,
)
def command_list_incidents(
    incident_status: str | None = Query(
        default=None,
        alias="status",
    ),
    category: str | None = Query(default=None),
    severity: int | None = Query(
        default=None,
        ge=1,
        le=5,
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(
        default=10,
        ge=1,
        le=100,
    ),
    current_user: User = Depends(require_command),
    db: Session = Depends(get_db),
):
    query = select(Incident)

    if incident_status is not None:
        query = query.where(
            Incident.status == incident_status
        )

    if category is not None:
        query = query.where(
            Incident.category == category
        )

    if severity is not None:
        query = query.where(
            Incident.severity == severity
        )

    total = db.scalar(
        select(func.count()).select_from(
            query.order_by(None).subquery()
        )
    ) or 0

    offset = (page - 1) * page_size

    incidents = db.scalars(
        query
        .order_by(
            Incident.created_at.desc(),
            Incident.id.desc(),
        )
        .offset(offset)
        .limit(page_size)
    ).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (
            total + page_size - 1
        ) // page_size,
        "items": incidents,
    }


# ============================================================
# COMMAND: VIEW INCIDENT HISTORY
# ============================================================

@app.get(
    "/command/incidents/{incident_id}/history",
    response_model=list[StatusHistoryResponse],
)
def command_view_incident_history(
    incident_id: int,
    current_user: User = Depends(require_command),
    db: Session = Depends(get_db),
):
    incident = db.get(
        Incident,
        incident_id,
    )

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found",
        )

    history = db.scalars(
        select(StatusHistory)
        .where(
            StatusHistory.incident_id == incident_id
        )
        .order_by(
            StatusHistory.created_at,
            StatusHistory.id,
        )
    ).all()

    return history


# ============================================================
# COMMAND: VERIFY INCIDENT AUDIT
# ============================================================

@app.get("/command/incidents/{incident_id}/verify")
def command_verify_incident(
    incident_id: int,
    current_user: User = Depends(require_command),
    db: Session = Depends(get_db),
):
    return verify_incident_audit(
        db,
        incident_id,
    )

@app.get('/incidents/{incident_id}/history', response_model=list[StatusHistoryResponse])
def citizen_incident_history(incident_id: int, current_user: User = Depends(require_citizen), db: Session = Depends(get_db)):
    """Return history only to the citizen who created the incident."""
    incident = db.scalar(select(Incident).where(Incident.id == incident_id, Incident.citizen_id == current_user.id))
    if incident is None:
        raise HTTPException(status_code=404, detail='Incident not found')
    return db.scalars(select(StatusHistory).where(StatusHistory.incident_id == incident_id).order_by(StatusHistory.created_at, StatusHistory.id)).all()


@app.get('/hero/my-incidents', response_model=list[IncidentResponse])
def hero_my_incidents(current_user: User = Depends(require_hero), db: Session = Depends(get_db)):
    """Return only incidents claimed by this hero, including resolved ones."""
    return db.scalars(select(Incident).where(Incident.hero_id == current_user.id).order_by(Incident.created_at.desc(), Incident.id.desc())).all()
