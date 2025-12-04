"""
pgmcp テストコード

PostgreSQL MCPサーバーのユニットテスト
"""

from unittest.mock import MagicMock, patch

from pgmcp.server import _get_table_schema_impl, _list_tables_impl


class TestListTables:
    """list_tables ツールのテスト"""

    @patch("pgmcp.server.get_connection")
    def test_list_tables_returns_table_list(
        self, mock_get_connection: MagicMock
    ) -> None:
        """テーブル一覧が正しくMarkdown Table形式で返されることを確認"""
        # モックカーソルの設定
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ("orders", "BASE TABLE"),
            ("users", "BASE TABLE"),
            ("user_view", "VIEW"),
        ]

        # コンテキストマネージャのモック
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_connection.return_value = mock_conn

        # テスト実行
        result = _list_tables_impl()

        # 検証
        assert "| table_name | table_type |" in result
        assert "| orders | BASE TABLE |" in result
        assert "| users | BASE TABLE |" in result
        assert "| user_view | VIEW |" in result

    @patch("pgmcp.server.get_connection")
    def test_list_tables_with_custom_schema(
        self, mock_get_connection: MagicMock
    ) -> None:
        """カスタムスキーマを指定した場合のテスト"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("audit_log", "BASE TABLE")]

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_connection.return_value = mock_conn

        # カスタムスキーマでテスト実行
        result = _list_tables_impl(schema="audit")

        # 検証
        assert "| audit_log | BASE TABLE |" in result

        # スキーマパラメータが正しく渡されたか確認
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        assert call_args[0][1] == ("audit",)

    @patch("pgmcp.server.get_connection")
    def test_list_tables_empty_result(self, mock_get_connection: MagicMock) -> None:
        """テーブルが存在しない場合のテスト"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_connection.return_value = mock_conn

        result = _list_tables_impl()

        assert result == "テーブルが見つかりませんでした。"


class TestGetTableSchema:
    """get_table_schema ツールのテスト"""

    @patch("pgmcp.server.get_connection")
    def test_get_table_schema_returns_columns(
        self, mock_get_connection: MagicMock
    ) -> None:
        """カラム情報がMarkdown Table形式で正しく返されることを確認"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ("id", "integer", "NO", "nextval('users_id_seq'::regclass)", True),
            ("name", "character varying(100)", "NO", None, False),
            ("email", "character varying(255)", "YES", None, False),
            ("created_at", "timestamp with time zone", "NO", "now()", False),
        ]

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_connection.return_value = mock_conn

        # テスト実行
        result = _get_table_schema_impl("users")

        # 検証
        assert "| column_name | data_type | nullable | default | PK |" in result
        assert "| id | integer | NO |" in result
        assert "✓" in result  # 主キーマーカー
        assert "| name | character varying(100) | NO |" in result
        assert "| email | character varying(255) | YES |" in result

    @patch("pgmcp.server.get_connection")
    def test_get_table_schema_with_custom_schema(
        self, mock_get_connection: MagicMock
    ) -> None:
        """カスタムスキーマを指定した場合のテスト"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ("log_id", "bigint", "NO", None, True),
        ]

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_connection.return_value = mock_conn

        # カスタムスキーマでテスト実行
        result = _get_table_schema_impl("audit_log", schema="audit")

        # 検証
        assert "| log_id | bigint | NO |" in result

        # パラメータが正しく渡されたか確認
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        assert call_args[0][1] == ("audit_log", "audit")

    @patch("pgmcp.server.get_connection")
    def test_get_table_schema_nonexistent_table(
        self, mock_get_connection: MagicMock
    ) -> None:
        """存在しないテーブルの場合のテスト"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_connection.return_value = mock_conn

        result = _get_table_schema_impl("nonexistent_table")

        assert result == "テーブルが見つかりませんでした。"
