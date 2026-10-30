import hashlib
import hmac
import json
import os


def get_audit_secret():
    secret = os.environ.get("SPIDER_SENSE_AUDIT_SECRET")

    if not secret:
        raise RuntimeError(
            "SPIDER_SENSE_AUDIT_SECRET environment variable is missing"
        )

    return secret.encode("utf-8")


def generate_hash(event_data, previous_hash="GENESIS"):
    """
    Generate a deterministic SHA-256 hash for an audit event.
    """

    payload = {
        "event": event_data,
        "previous_hash": previous_hash,
    }

    serialized = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    return hashlib.sha256(
        serialized.encode("utf-8")
    ).hexdigest()


def generate_hmac(event_hash):
    """
    Authenticate an event hash using a secret key.
    """

    secret = get_audit_secret()

    return hmac.new(
        secret,
        event_hash.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_hmac(event_hash, stored_hmac):
    """
    Verify the event's HMAC using constant-time comparison.
    """

    expected_hmac = generate_hmac(event_hash)

    return hmac.compare_digest(
        expected_hmac,
        stored_hmac,
    )