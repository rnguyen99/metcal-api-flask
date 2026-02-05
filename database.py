"""SQLite data access helpers."""
from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import date
from typing import Any, Dict, List, Optional

from config import settings

ASSET_COLUMNS = (
    "name",
    "category",
    "owner",
    "status",
    "location",
    "value",
    "purchase_date",
    "metadata",
)


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = sqlite3.Row
    return conn


def _normalize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    normalized: Dict[str, Any] = {}
    for key, value in payload.items():
        if isinstance(value, date):
            normalized[key] = value.isoformat()
        else:
            normalized[key] = value
    return normalized


def fetch_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    with closing(_get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, password_hash, role FROM user WHERE username = ?",
            (username,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def fetch_all_assets() -> List[Dict[str, Any]]:
    with closing(_get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, category, owner, status, location, value, purchase_date,"
            " metadata, created_at, updated_at FROM asset ORDER BY id DESC"
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def fetch_asset(asset_id: int) -> Optional[Dict[str, Any]]:
    with closing(_get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, category, owner, status, location, value, purchase_date,"
            " metadata, created_at, updated_at FROM asset WHERE id = ?",
            (asset_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def insert_asset(payload: Dict[str, Any]) -> int:
    normalized = _normalize_payload(payload)
    with closing(_get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO asset (name, category, owner, status, location, value, purchase_date, metadata)
            VALUES (:name, :category, :owner, :status, :location, :value, :purchase_date, :metadata)
            """,
            {column: normalized.get(column) for column in ASSET_COLUMNS},
        )
        conn.commit()
        return cursor.lastrowid


def update_asset(asset_id: int, payload: Dict[str, Any]) -> bool:
    normalized = _normalize_payload(payload)
    if not normalized:
        return False

    set_clause = ", ".join(f"{column} = ?" for column in normalized.keys())
    values = list(normalized.values())
    values.append(asset_id)

    with closing(_get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE asset SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            values,
        )
        conn.commit()
        return cursor.rowcount > 0
