"""Database connection and utilities for scrapers."""

import os
from typing import Any
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv(dotenv_path='../../.env')


def get_connection():
    """Get a database connection."""
    return psycopg2.connect(
        os.getenv('DATABASE_URL', 'postgresql://localhost:5432/cardpulse'),
        cursor_factory=RealDictCursor
    )


def execute_query(query: str, params: tuple = None) -> list[dict]:
    """Execute a query and return results."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            if cur.description:
                return cur.fetchall()
            return []


def execute_insert(query: str, params: tuple = None) -> Any:
    """Execute an insert and return the result."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            conn.commit()
            if cur.description:
                return cur.fetchone()
            return None


def execute_batch(query: str, params_list: list[tuple]) -> None:
    """Execute a batch of inserts."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            for params in params_list:
                cur.execute(query, params)
            conn.commit()
