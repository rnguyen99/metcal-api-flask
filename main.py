"""Flask application entry point."""
from __future__ import annotations

import time
from typing import Tuple, Type

from flask import Flask, jsonify, g, request
from flask_cors import CORS
from pydantic import BaseModel, ValidationError
from werkzeug.exceptions import BadRequest, HTTPException

import auth
import database
from config import settings
from logger import logger
from models import (
    AssetCreate,
    AssetResponse,
    AssetUpdate,
    ErrorResponse,
    TokenRequest,
    TokenResponse,
)

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False
CORS(app, resources={r"/api/*": {"origins": "*"}})


@app.before_request
def start_timer() -> None:
    g.start_time = time.perf_counter()


@app.after_request
def log_response(response):  # type: ignore[override]
    duration_ms = 0.0
    if hasattr(g, "start_time"):
        duration_ms = (time.perf_counter() - g.start_time) * 1000

    user = getattr(g, "current_user", "anonymous")
    client_ip = (request.headers.get("X-Forwarded-For") or request.remote_addr or "-").split(",")[0].strip()

    logger.info(
        "method=%s path=%s status=%s duration_ms=%.2f ip=%s user=%s",
        request.method,
        request.path,
        response.status_code,
        duration_ms,
        client_ip,
        user,
    )
    return response


@app.errorhandler(HTTPException)
def handle_http_exception(exc: HTTPException):  # type: ignore[override]
    payload = ErrorResponse(detail=exc.description or exc.name)
    logger.warning(
        "http_error status=%s path=%s detail=%s", exc.code, request.path, payload.detail
    )
    return jsonify(payload.model_dump()), exc.code


@app.errorhandler(Exception)
def handle_uncaught_exception(exc: Exception):  # type: ignore[override]
    logger.exception("unhandled_error path=%s", request.path)
    payload = ErrorResponse(detail="Internal server error")
    return jsonify(payload.model_dump()), 500


def _bind_body(model: Type[BaseModel]) -> Tuple[BaseModel, None] | Tuple[None, list[dict]]:
    payload = request.get_json(silent=True)
    if payload is None:
        return None, [{"msg": "Request body must be valid JSON."}]
    try:
        return model.model_validate(payload), None
    except ValidationError as exc:
        return None, exc.errors()


@app.route("/api/token", methods=["POST"])
def issue_token():
    data, errors = _bind_body(TokenRequest)
    if errors:
        return jsonify({"detail": "Invalid request payload", "errors": errors}), 400

    assert isinstance(data, TokenRequest)
    if not auth.authenticate_user(data.username, data.password):
        logger.warning("failed_login username=%s", data.username)
        return jsonify({"detail": "Invalid credentials"}), 401

    token = auth.create_access_token(data.username)
    response = TokenResponse(access_token=token, expires_in=settings.jwt_expires_hours * 3600)
    return jsonify(response.model_dump())


@app.route("/api/assets", methods=["GET"])
@auth.token_required
def list_assets():
    assets = database.fetch_all_assets()
    response = [AssetResponse.model_validate(asset).model_dump() for asset in assets]
    return jsonify(response)


@app.route("/api/asset/<int:asset_id>", methods=["GET"])
@auth.token_required
def get_asset(asset_id: int):
    asset = database.fetch_asset(asset_id)
    if not asset:
        return jsonify({"detail": "Asset not found"}), 404
    response = AssetResponse.model_validate(asset)
    return jsonify(response.model_dump())


@app.route("/api/asset", methods=["POST"])
@auth.token_required
def create_asset():
    data, errors = _bind_body(AssetCreate)
    if errors:
        return jsonify({"detail": "Invalid request payload", "errors": errors}), 400

    assert isinstance(data, AssetCreate)
    asset_id = database.insert_asset(data.model_dump())
    asset = database.fetch_asset(asset_id)
    if not asset:
        logger.error("asset_missing_after_create id=%s", asset_id)
        return jsonify({"detail": "Asset retrieval failed"}), 500
    response = AssetResponse.model_validate(asset)
    return jsonify(response.model_dump()), 201


@app.route("/api/asset/<int:asset_id>", methods=["PUT"])
@auth.token_required
def update_asset(asset_id: int):
    data, errors = _bind_body(AssetUpdate)
    if errors:
        return jsonify({"detail": "Invalid request payload", "errors": errors}), 400

    assert isinstance(data, AssetUpdate)
    update_payload = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_payload:
        return jsonify({"detail": "No fields provided for update"}), 400

    updated = database.update_asset(asset_id, update_payload)
    if not updated:
        return jsonify({"detail": "Asset not found"}), 404

    asset = database.fetch_asset(asset_id)
    if not asset:
        logger.error("asset_missing_after_update id=%s", asset_id)
        return jsonify({"detail": "Asset retrieval failed"}), 500
    response = AssetResponse.model_validate(asset)
    return jsonify(response.model_dump())


@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    from waitress import serve

    serve(app, host="0.0.0.0", port=8000)
