"""JWT Authentication + Role-Based Access Control.

Roles: admin, analyst, reviewer, viewer
All existing endpoints remain open by default (backward compatible).
New protected endpoints require auth via X-API-Key header or Bearer token.
"""

import os
import hashlib
import hmac
import time
import json
import base64
import logging
from dataclasses import dataclass, asdict
from functools import wraps

logger = logging.getLogger("truthlens.auth")

# Secret key for JWT-like tokens (HMAC-SHA256)
SECRET_KEY = os.getenv("TL_SECRET_KEY", "truthlens-dev-secret-change-in-production")
TOKEN_EXPIRY = int(os.getenv("TL_TOKEN_EXPIRY", "86400"))  # 24 hours

# Role hierarchy
ROLES = {
    "admin": {"level": 4, "permissions": ["read", "write", "delete", "admin", "research", "review"]},
    "analyst": {"level": 3, "permissions": ["read", "write", "research", "review"]},
    "reviewer": {"level": 2, "permissions": ["read", "review"]},
    "viewer": {"level": 1, "permissions": ["read"]},
}


@dataclass
class User:
    user_id: str
    role: str
    org_id: str | None = None
    permissions: list[str] = None

    def __post_init__(self):
        if self.permissions is None:
            self.permissions = ROLES.get(self.role, {}).get("permissions", ["read"])

    def has_permission(self, perm: str) -> bool:
        return perm in self.permissions

    def to_dict(self):
        return asdict(self)


@dataclass
class TokenPayload:
    user_id: str
    role: str
    org_id: str | None = None
    iat: float = 0
    exp: float = 0

    def __post_init__(self):
        now = time.time()
        if self.iat == 0:
            self.iat = now
        if self.exp == 0:
            self.exp = now + TOKEN_EXPIRY

    def is_expired(self) -> bool:
        return time.time() > self.exp

    def to_dict(self):
        return {"user_id": self.user_id, "role": self.role, "org_id": self.org_id, "iat": self.iat, "exp": self.exp}


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    s += "=" * (4 - len(s) % 4)
    return base64.urlsafe_b64decode(s)


def _sign(payload: str) -> str:
    return _b64url_encode(hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).digest())


def create_token(user_id: str, role: str = "viewer", org_id: str | None = None) -> str:
    """Create a signed token (HMAC-SHA256 JWT-like)."""
    payload = TokenPayload(user_id=user_id, role=role, org_id=org_id)
    header = _b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    body = _b64url_encode(json.dumps(payload.to_dict()).encode())
    sig = _sign(f"{header}.{body}")
    return f"{header}.{body}.{sig}"


def verify_token(token: str) -> TokenPayload | None:
    """Verify and decode a token. Returns None if invalid."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64, body_b64, sig = parts
        expected_sig = _sign(f"{header_b64}.{body_b64}")
        if not hmac.compare_digest(sig, expected_sig):
            return None
        payload_dict = json.loads(_b64url_decode(body_b64))
        tp = TokenPayload(**payload_dict)
        if tp.is_expired():
            return None
        return tp
    except Exception:
        return None


def extract_user_from_request(request) -> User | None:
    """Extract user from Authorization header or X-API-Key."""
    # Try Bearer token first
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        payload = verify_token(token)
        if payload:
            return User(user_id=payload.user_id, role=payload.role, org_id=payload.org_id)

    # Try X-API-Key (lookup in DB)
    api_key = request.headers.get("X-API-Key")
    if api_key:
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        # Would query DB here — for now check env var for admin key
        admin_key = os.getenv("TL_ADMIN_API_KEY", "")
        if admin_key and hmac.compare_digest(api_key, admin_key):
            return User(user_id="api_admin", role="admin")

    return None


def require_role(min_role: str):
    """Decorator: require minimum role level for an endpoint."""
    min_level = ROLES.get(min_role, {}).get("level", 1)

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            from fastapi import Request, HTTPException
            request = kwargs.get("request")
            if request is None:
                # Try to find request in args
                for arg in args:
                    if hasattr(arg, "headers"):
                        request = arg
                        break
            if request is None:
                raise HTTPException(401, "Authentication required")
            user = extract_user_from_request(request)
            if user is None:
                raise HTTPException(401, "Invalid or missing authentication")
            user_level = ROLES.get(user.role, {}).get("level", 0)
            if user_level < min_level:
                raise HTTPException(403, f"Insufficient permissions. Required: {min_role}, Current: {user.role}")
            kwargs["current_user"] = user
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# In-memory user store (production would use DB)
_users: dict[str, dict] = {
    "admin": {"user_id": "admin", "role": "admin", "password_hash": hashlib.sha256("admin".encode()).hexdigest()},
    "analyst1": {"user_id": "analyst1", "role": "analyst", "password_hash": hashlib.sha256("analyst".encode()).hexdigest()},
    "reviewer1": {"user_id": "reviewer1", "role": "reviewer", "password_hash": hashlib.sha256("reviewer".encode()).hexdigest()},
}


def authenticate_user(username: str, password: str) -> str | None:
    """Authenticate user and return token. Returns None if invalid."""
    user = _users.get(username)
    if not user:
        return None
    pw_hash = hashlib.sha256(password.encode()).hexdigest()
    if not hmac.compare_digest(pw_hash, user["password_hash"]):
        return None
    return create_token(user["user_id"], user["role"])


def register_user(username: str, password: str, role: str = "viewer") -> dict | None:
    """Register a new user."""
    if username in _users:
        return None
    _users[username] = {
        "user_id": username,
        "role": role,
        "password_hash": hashlib.sha256(password.encode()).hexdigest(),
    }
    return {"user_id": username, "role": role}
