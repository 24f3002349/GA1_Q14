
import hashlib
import os
from contextvars import ContextVar

import uvicorn
from starlette.middleware.base import BaseHTTPMiddleware
from mcp.server.fastmcp import FastMCP, Context

# Holds headers for the current HTTP request.
# ContextVar keeps simultaneous calls isolated.
exam_challenge = ContextVar("exam_challenge", default=None)

mcp = FastMCP(
    "Exam Challenge Server",
    stateless_http=True,
    json_response=True,
    host="0.0.0.0",
    port=int(os.environ.get("PORT", "8000")),
)


@mcp.tool()
def solve_challenge(ctx: Context) -> str:
    """Solve the current exam challenge using its HTTP request header."""
    challenge = exam_challenge.get()

    if not challenge:
        raise ValueError("Missing X-Exam-Challenge HTTP header")

    email = "24f3002349@ds.study.iitm.ac.in".strip().lower()
    message = f"{challenge}:{email}"
    return hashlib.sha256(message.encode("utf-8")).hexdigest()[:16]


class ExamHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Each request gets its own challenge context.
        token = exam_challenge.set(
            request.headers.get("x-exam-challenge")
        )
        try:
            return await call_next(request)
        finally:
            exam_challenge.reset(token)


app = mcp.streamable_http_app()
app.add_middleware(ExamHeaderMiddleware)


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8000")),
    )
