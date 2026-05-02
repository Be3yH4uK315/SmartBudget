from contextvars import ContextVar
from uuid import uuid4


request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def set_request_id(request_id: str | None = None) -> str:
    final_id = request_id or str(uuid4())
    request_id_var.set(final_id)
    return final_id


def get_request_id() -> str:
    return request_id_var.get()
