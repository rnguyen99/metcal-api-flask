"""Initialize the SQLite database with required tables and seed data."""
from __future__ import annotations

import sqlite3
from contextlib import closing

from auth import hash_password
from config import settings
from logger import logger

ASSET_SEED_DATA = [
    {
        "name": "Thermal Camera",
        "category": "Diagnostics",
        "owner": "Maintenance",
        "status": "active",
        "location": "Warehouse A",
        "value": 2850.00,
        "purchase_date": "2023-05-17",
        "metadata": "Calibrated Q4",
    },
    {
        "name": "Server Rack",
        "category": "IT",
        "owner": "Infrastructure",
        "status": "active",
        "location": "Data Center 2",
        "value": 12400.00,
        "purchase_date": "2022-11-03",
        "metadata": "42U, dual PDU",
    },
]

ASSET_TABLE_SQL = """
CREATE TABLE asset (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT,
    owner TEXT,
    status TEXT,
    location TEXT,
    value REAL,
    purchase_date TEXT,
    metadata TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT
);
"""

USER_TABLE_SQL = """
CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'admin',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    cursor = connection.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    )
    return cursor.fetchone() is not None


def ensure_tables(connection: sqlite3.Connection) -> None:
    if not table_exists(connection, "asset"):
        logger.info("creating asset table")
        connection.execute(ASSET_TABLE_SQL)

    if not table_exists(connection, "user"):
        logger.info("creating user table")
        connection.execute(USER_TABLE_SQL)

    connection.commit()


def seed_admin_user(connection: sqlite3.Connection) -> None:
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(1) FROM user")
    (count,) = cursor.fetchone()
    if count == 0:
        logger.info("seeding default admin user")
        cursor.execute(
            "INSERT INTO user (username, password_hash, role) VALUES (?, ?, ?)",
            ("admin", hash_password("password"), "admin"),
        )
        connection.commit()
    else:
        logger.info("admin user already present, skipping seed")


def seed_assets(connection: sqlite3.Connection) -> None:
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(1) FROM asset")
    (count,) = cursor.fetchone()
    if count == 0:
        logger.info("seeding sample asset records")
        cursor.executemany(
            """
            INSERT INTO asset (
                name, category, owner, status, location, value, purchase_date, metadata
            ) VALUES (:name, :category, :owner, :status, :location, :value, :purchase_date, :metadata)
            """,
            ASSET_SEED_DATA,
        )
        connection.commit()
    else:
        logger.info("asset table already contains records, skipping seed")


def initialize_database() -> None:
    with closing(sqlite3.connect(settings.database_path)) as connection:
        ensure_tables(connection)
        seed_admin_user(connection)
        seed_assets(connection)
        logger.info("database initialization complete")


if __name__ == "__main__":
    initialize_database()
