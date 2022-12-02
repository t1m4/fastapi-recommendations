from http import HTTPStatus
from typing import Any

import pydantic
from fastapi import Depends, HTTPException, Query
from fastapi.security import APIKeyHeader

from app.auth.services import authentication
from app.auth.types import AuthPlatform, User
from app.auth.utils import get_jwt_payload

security = APIKeyHeader(
    name="X-Internal-Authorization",
    scheme_name="InternalToken",
    description=(
        "Token for the internal network. Use this token if try to make calls " "inside the internal network or locally."
    ),
)


def _parse_user(payload: dict[str, Any]) -> User:
    try:
        return User(**payload)
    except pydantic.ValidationError:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Can't parse user from token",
        )


def _check_user_access(user: User) -> None:
    if not user.has_financial_access:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="User doesn't have financial access",
        )


def get_user(token: str = Depends(security)) -> User:
    """
    Extract JWT token from request headers, decode JWT, build User object
    and validate access
    """
    print(authentication.client._admin_user_headers())
    payload = get_jwt_payload(token=token, key="")
    user = _parse_user(payload=payload)
    _check_user_access(user=user)
    return user


def get_auth_platform(token: str = Query(...)) -> AuthPlatform:
    """
    Extract JWT token from query parameters, decode JWT and build object
    with info about platform
    """
    payload = get_jwt_payload(token=token)
    return AuthPlatform(**payload)
