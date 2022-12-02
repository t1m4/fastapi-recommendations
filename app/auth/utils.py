from http import HTTPStatus

import jwt
from fastapi import HTTPException

from app.config import config
from app.types import StrDict


def get_jwt_payload(token: str, key: str = config.JWT_SECRET_KEY) -> StrDict:
    try:
        return jwt.decode(token, key=key, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Can't decode authorization token",
        )


def create_jwt_token(payload: StrDict, key: str = config.JWT_SECRET_KEY) -> str:
    return jwt.encode(
        payload=payload,
        key=key,
        algorithm="HS256",
    )
