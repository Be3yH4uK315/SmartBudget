from datetime import datetime, timezone

def utc_now() -> datetime:
    """Возвращает текущее время в UTC с time zone info."""
    return datetime.now(timezone.utc)

def utc_timestamp() -> float:
    """Возвращает текущий timestamp."""
    return utc_now().timestamp()
