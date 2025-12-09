import pytest
from jsonschema import FormatChecker, validate
from jsonschema.exceptions import ValidationError
from app.kafka import SCHEMAS

def test_auth_events_schema_valid_required():
    data = {"event": "user.registered", "user_id": "123e4567-e89b-12d3-a456-426614174000"}
    validate(instance=data, schema=SCHEMAS["AUTH_EVENTS_SCHEMA"])

def test_auth_events_schema_valid_with_optional():
    data = {"event": "user.login", "user_id": "uuid", "email": "test@example.com", "ip": "127.0.0.1", "location": "Local"}
    validate(instance=data, schema=SCHEMAS["AUTH_EVENTS_SCHEMA"])

def test_auth_events_schema_invalid_event():
    data = {"event": "invalid", "user_id": "uuid"}
    with pytest.raises(ValidationError):
        validate(instance=data, schema=SCHEMAS["AUTH_EVENTS_SCHEMA"])

def test_auth_events_schema_missing_user_id():
    data = {"event": "user.registered"}
    with pytest.raises(ValidationError):
        validate(instance=data, schema=SCHEMAS["AUTH_EVENTS_SCHEMA"])

def test_auth_events_schema_token_invalid_no_user_id():
    data = {"event": "user.token_invalid", "token": "anonymized"}
    validate(instance=data, schema=SCHEMAS["AUTH_EVENTS_SCHEMA"])

def test_users_active_schema_valid():
    data = {"user_id": "123e4567-e89b-12d3-a456-426614174000", "email": "test@example.com", "name": "User", "country": "US", "role": 0, "is_active": True}
    validate(instance=data, schema=SCHEMAS["USERS_ACTIVE_SCHEMA"])

def test_users_active_schema_missing_required():
    data = {"email": "test@example.com"}
    with pytest.raises(ValidationError):
        validate(instance=data, schema=SCHEMAS["USERS_ACTIVE_SCHEMA"])

def test_users_active_schema_invalid_uuid():
    data = {"user_id": "invalid_uuid", "email": "test@example.com"}
    with pytest.raises(ValidationError):
        validate(
            instance=data,
            schema=SCHEMAS["USERS_ACTIVE_SCHEMA"],
            format_checker=FormatChecker()
        )