AUTH_EVENTS_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Auth Events Schema",
    "type": "object",
    "properties": {
        "event": {"type": "string", "enum": ["user.registered", "user.login", "user.logout", "user.password_changed", "user.password_reset", "user.token_invalid"]},
        "user_id": {"type": "string", "format": "uuid"},
        "email": {"type": "string"},
        "ip": {"type": "string"},
        "location": {"type": "string"}
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
        "user_id": {"type": "string", "format": "uuid"},
        "email": {"type": "string"},
        "name": {"type": "string"},
        "country": {"type": "string"},
        "role": {"type": "integer"},
        "is_active": {"type": "boolean"}
    },
    "required": ["user_id", "email"]
}

SCHEMAS = {
    "AUTH_EVENTS_SCHEMA": AUTH_EVENTS_SCHEMA,
    "USERS_ACTIVE_SCHEMA": USERS_ACTIVE_SCHEMA
}