SCHEMA_NEED_CATEGORY = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "transaction_id": {"type": "string", "format": "uuid"},
        "account_id": {"type": "string", "format": "uuid"},
        "merchant": {"type": "string"},
        "mcc": {"type": "integer"},
        "description": {"type": "string"}
    },
    "required": ["transaction_id", "merchant"]
}

SCHEMA_CLASSIFIED = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "transaction_id": {"type": "string", "format": "uuid"},
        "category_id": {"type": "string", "format": "uuid"},
        "category_name": {"type": "string"}
    },
    "required": ["transaction_id", "category_id"]
}

SCHEMA_UPDATED = {
    "$schema": "http://json-schema.org/draft-07/schema#", 
    "type": "object",
    "properties": {
        "transaction_id": {"type": "string", "format": "uuid"},
        "merchant": {"type": "string"},
        "mcc": {"type": "integer"},
        "description": {"type": "string"},
        "old_category": {"type": "string"},
        "new_category_id": {"type": "string", "format": "uuid"},
        "new_category_name": {"type": "string"}
    },
    "required": ["transaction_id", "new_category_id"]
}

SCHEMA_NEED_CATEGORY_DLQ = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "original_topic": {"type": "string"},
        "original_message": {"type": "string"},
        "error": {"type": "string"},
        "timestamp": {"type": "string", "format": "date-time"}
    },
    "required": ["original_topic", "original_message", "error", "timestamp"]
}

SCHEMAS_MAP = {
    "transaction.need_category": SCHEMA_NEED_CATEGORY,
    "transaction.classified": SCHEMA_CLASSIFIED,
    "budget.classification.events": SCHEMA_CLASSIFIED,
    "transaction.updated": SCHEMA_UPDATED
}