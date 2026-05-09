from contextvars import ContextVar
from uuid import uuid4

request_id_ctx: ContextVar[str] = ContextVar(
    "request_id",
    default="unknown",
)


def get_request_id() -> str:
    """Возвращает текущий request_id из контекста."""
    return request_id_ctx.get()


def set_request_id(request_id: str | None = None) -> str:
    """Устанавливает request_id в контекст или генерирует новый."""
    resolved_request_id = request_id or str(uuid4())
    request_id_ctx.set(resolved_request_id)

    return resolved_request_id
