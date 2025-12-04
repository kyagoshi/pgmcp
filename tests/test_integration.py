"""
pgmcp Medium Size テストコード

実際のPostgreSQLデータベースに接続して行う統合テスト
docker compose up -d でデータベースを起動してから実行してください
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

from server import _get_table_schema_impl, _list_tables_impl, get_connection


@pytest.fixture(scope="module")
def db_connection() -> Generator[bool, None, None]:
    """データベース接続が可能かを確認するフィクスチャ"""
    try:
        conn = get_connection()
        conn.close()
        yield True
    except Exception as e:
        pytest.skip(f"データベースに接続できません: {e}")


class TestListTablesIntegration:
    """list_tables の統合テスト"""

    def test_list_tables_public_schema(self, db_connection: bool) -> None:
        """publicスキーマのテーブル一覧を取得"""
        result = _list_tables_impl(schema="public")

        # Markdown Table形式であることを確認
        assert "| table_name | table_type |" in result
        assert "|------------|------------|" in result

        # 期待されるテーブルが含まれていることを確認
        assert "| users | BASE TABLE |" in result
        assert "| orders | BASE TABLE |" in result
        assert "| products | BASE TABLE |" in result

    def test_list_tables_audit_schema(self, db_connection: bool) -> None:
        """auditスキーマのテーブル一覧を取得"""
        result = _list_tables_impl(schema="audit")

        assert "| table_name | table_type |" in result
        assert "| logs | BASE TABLE |" in result

    def test_list_tables_nonexistent_schema(self, db_connection: bool) -> None:
        """存在しないスキーマの場合"""
        result = _list_tables_impl(schema="nonexistent_schema")

        assert result == "テーブルが見つかりませんでした。"


class TestGetTableSchemaIntegration:
    """get_table_schema の統合テスト"""

    def test_get_users_table_schema(self, db_connection: bool) -> None:
        """usersテーブルのスキーマを取得"""
        result = _get_table_schema_impl("users", schema="public")

        # ヘッダーの確認
        assert "| column_name | data_type | nullable | default | PK |" in result

        # カラムの確認
        assert "| id | integer |" in result
        assert "✓" in result  # 主キーマーカー
        assert "| name | character varying(100) | NO |" in result
        assert "| email | character varying(255) | YES |" in result
        assert "| created_at | timestamp with time zone |" in result

    def test_get_orders_table_schema(self, db_connection: bool) -> None:
        """ordersテーブルのスキーマを取得（外部キーを含む）"""
        result = _get_table_schema_impl("orders", schema="public")

        # カラムの確認
        assert "| id | integer |" in result
        assert "| user_id | integer | NO |" in result
        assert "| total_amount | numeric(10,2) | NO |" in result
        assert "| status | character varying(50) |" in result

    def test_get_products_table_schema(self, db_connection: bool) -> None:
        """productsテーブルのスキーマを取得"""
        result = _get_table_schema_impl("products", schema="public")

        assert "| id | integer |" in result
        assert "| name | character varying(200) | NO |" in result
        assert "| description | text | YES |" in result
        assert "| price | numeric(10,2) | NO |" in result
        assert "| stock | integer |" in result

    def test_get_audit_logs_table_schema(self, db_connection: bool) -> None:
        """audit.logsテーブルのスキーマを取得（別スキーマ）"""
        result = _get_table_schema_impl("logs", schema="audit")

        assert "| id | bigint |" in result
        assert "| table_name | character varying(100) |" in result
        assert "| action | character varying(20) |" in result
        assert "| old_data | jsonb |" in result
        assert "| new_data | jsonb |" in result

    def test_get_nonexistent_table_schema(self, db_connection: bool) -> None:
        """存在しないテーブルの場合"""
        result = _get_table_schema_impl("nonexistent_table", schema="public")

        assert result == "テーブルが見つかりませんでした。"


class TestDatabaseConnection:
    """データベース接続のテスト"""

    def test_connection_successful(self, db_connection: bool) -> None:
        """データベースに正常に接続できることを確認"""
        conn = get_connection()
        assert conn is not None

        # 簡単なクエリを実行
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            result = cur.fetchone()
            assert result is not None
            assert result[0] == 1

        conn.close()

    def test_connection_returns_correct_database(self, db_connection: bool) -> None:
        """正しいデータベースに接続していることを確認"""
        conn = get_connection()

        with conn.cursor() as cur:
            cur.execute("SELECT current_database()")
            result = cur.fetchone()
            assert result is not None
            assert result[0] == "testdb"

        conn.close()
