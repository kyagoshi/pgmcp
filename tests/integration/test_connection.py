"""
データベース接続の統合テスト
"""

from pgmcp.connection import get_connection


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
