"""
統合テスト用の共通フィクスチャ
"""

import os
from collections.abc import Generator

import pytest

# テスト用のDB接続情報を設定
os.environ.setdefault("PGHOST", "localhost")
os.environ.setdefault("PGPORT", "5433")
os.environ.setdefault("PGDATABASE", "testdb")
os.environ.setdefault("PGUSER", "testuser")
os.environ.setdefault("PGPASSWORD", "testpass")

from pgmcp.connection import get_connection


@pytest.fixture(scope="module")
def db_connection() -> Generator[bool, None, None]:
    """データベース接続が可能かを確認するフィクスチャ"""
    try:
        conn = get_connection()
        conn.close()
        yield True
    except Exception as e:
        pytest.skip(f"データベースに接続できません: {e}")
