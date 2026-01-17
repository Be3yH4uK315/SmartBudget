from contextvars import ContextVar
from uuid import uuid4

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="unknown")

def get_request_id() -> str:
    return request_id_ctx.get()

def set_request_id(req_id: str = None) -> str:
    if not req_id:
        req_id = str(uuid4())
    request_id_ctx.set(req_id)
    return req_id