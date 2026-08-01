import os
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import PlainTextResponse, RedirectResponse

COOKIE_NAME = "cv_access"


class TokenGateMiddleware(BaseHTTPMiddleware):
    """Blocks all requests unless they carry the correct secret token,
    either as ?token=... on the URL or as a cookie set on a previous visit."""

    async def dispatch(self, request: Request, call_next):
        secret = os.environ.get("ACCESS_TOKEN")
        print(f"[TokenGate] secret={secret!r} path={request.url.path} cookie={request.cookies.get(COOKIE_NAME)!r}")

        if not secret:
            # No token configured -> app is intentionally open, don't block.
            return await call_next(request)

        # Already unlocked in this browser?
        if request.cookies.get(COOKIE_NAME) == secret:
            return await call_next(request)

        # First visit via the secret link?
        token_param = request.query_params.get("token")
        if token_param == secret:
            clean_path = request.url.path
            response = RedirectResponse(url=clean_path)
            response.set_cookie(
                COOKIE_NAME,
                secret,
                httponly=True,
                samesite="lax",
                max_age=60 * 60 * 24 * 30,  # 30 days
            )
            return response

        return PlainTextResponse(
            "This certificate register is private. Please use the link you were given.",
            status_code=403,
        )