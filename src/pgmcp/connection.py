"""
データベース接続管理
"""

import os

import psycopg2
from psycopg2.extensions import connection


def get_connection() -> connection:
    """環境変数からPostgreSQL接続を作成"""
    conn = psycopg2.connect(
        host=os.environ.get("PGHOST", "localhost"),
        port=os.environ.get("PGPORT", "5432"),
        database=os.environ.get("PGDATABASE"),
        user=os.environ.get("PGUSER"),
        password=os.environ.get("PGPASSWORD"),
    )

    # 誤操作防止のため接続をリードオンリーに固定
    conn.set_session(readonly=True)

    return conn
