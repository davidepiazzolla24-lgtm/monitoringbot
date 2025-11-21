from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer


@dataclass
class User:
    username: str
    role: str
    provider: str

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


# In a real-world setup, these tokens would be validated against your IdP or OAuth provider.
_FAKE_TOKENS: Dict[str, User] = {
    "viewer-token": User(username="viewer@example.com", role="viewer", provider="oauth"),
    "admin-token": User(username="admin@example.com", role="admin", provider="sso"),
}


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)


def _resolve_token(token: Optional[str]) -> User:
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing credentials")
    user = _FAKE_TOKENS.get(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return user


def get_current_user(
    bearer_token: Optional[str] = Depends(oauth2_scheme),
    sso_token: Optional[str] = Header(None, alias="X-Company-SSO"),
) -> User:
    """Resolve the user from either OAuth2 bearer token or SSO header.

    This keeps the backend flexible for local development (bearer tokens)
    and production (SSO header) without changing the authorization model.
    """

    if sso_token:
        return _resolve_token(sso_token)
    return _resolve_token(bearer_token)


def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return user
