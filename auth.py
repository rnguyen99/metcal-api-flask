"""Authentication utilities for JWT handling."""
from __future__ import annotations

import datetime as dt
from functools import wraps
from typing import Callable, Dict, Optional

import bcrypt
import jwt
from flask import Response, g, jsonify, request

import database
from config import settings
from logger import logger


def hash_password(password: str) -> str:
    """Create a bcrypt hash for the supplied password."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except ValueError:
        logger.warning("invalid bcrypt hash encountered")
        return False


def authenticate_user(username: str, password: str) -> bool:
    user = database.fetch_user_by_username(username)
    if not user:
        return False
    return verify_password(password, user["password_hash"])


def create_access_token(username: str) -> str:
    now = dt.datetime.utcnow()
    payload = {
        "sub": username,
        "iss": settings.issuer,
        "aud": settings.audience,
        "iat": now,
        "exp": now + dt.timedelta(hours=settings.jwt_expires_hours),
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token


def decode_access_token(token: str) -> Dict[str, str]:
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
        audience=settings.audience,
        issuer=settings.issuer,
    )


def token_required(func: Callable) -> Callable:
    """Decorator to enforce bearer token authentication."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            logger.warning("missing bearer token: path=%s", request.path)
            return jsonify({"detail": "Bearer token required"}), 401

        token = auth_header.split(" ", 1)[1].strip()
        try:
            payload = decode_access_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"detail": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"detail": "Invalid token"}), 401

        g.current_user = payload.get("sub")
        return func(*args, **kwargs)

    return wrapper
