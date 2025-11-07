AUTH_EVENTS_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Auth Events Schema",
    "type": "object",
    "properties": {
        "event": {
            "type": "string",
            "enum": [
                "user.registered", "user.login", "user.logout", "user.session_mismatch_detected",
                "user.password_reset", "user.token_invalid", "user.verification_started",
                "user.verification_validated", "user.token_refreshed", "user.password_changed"
            ],
            "description": "Type of authentication event"
        },
        "user_id": {"type": "string", "format": "uuid", "description": "User UUID"},
        "email": {"type": "string", "description": "User email"},
        "ip": {"type": "string", "description": "IP address"},
        "location": {"type": "string", "description": "Geolocation"}
    },
    "required": ["event"],
    "if": {
        "properties": { "event": { "not": { "const": "user.token_invalid" } } }
    },
    "then": {
        "required": ["user_id"]
    }
}

USERS_ACTIVE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "user_id": {"type": "string", "format": "uuid", "description": "User UUID"},
        "email": {"type": "string", "description": "User email"},
        "name": {"type": "string", "description": "User name"},
        "country": {"type": "string", "description": "User country"},
        "role": {"type": "integer", "description": "User role"},
        "is_active": {"type": "boolean", "description": "Active status"}
    },
    "required": ["user_id", "email"]
}

SCHEMAS = {
    "AUTH_EVENTS_SCHEMA": AUTH_EVENTS_SCHEMA,
    "USERS_ACTIVE_SCHEMA": USERS_ACTIVE_SCHEMA
}