"""
外部キー関連ツールのユニットテスト
"""

from unittest.mock import MagicMock, patch

from pgmcp.tools import get_foreign_keys_impl


class TestGetForeignKeys:
    """get_foreign_keys ツールのテスト"""

    @patch("pgmcp.tools.foreign_keys.get_connection")
    def test_get_foreign_keys_returns_foreign_keys(
        self, mock_get_connection: MagicMock
    ) -> None:
        """外部キー情報がMarkdown Table形式で正しく返されることを確認"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ("orders_user_id_fkey", "user_id", "users", "id"),
            ("orders_product_id_fkey", "product_id", "products", "id"),
        ]

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_connection.return_value = mock_conn

        # テスト実行
        result = get_foreign_keys_impl("orders")

        # 検証
        assert (
            "| constraint_name | column_name | foreign_table | foreign_column |"
            in result
        )
        assert "| orders_user_id_fkey | user_id | users | id |" in result
        assert "| orders_product_id_fkey | product_id | products | id |" in result

    @patch("pgmcp.tools.foreign_keys.get_connection")
    def test_get_foreign_keys_with_custom_schema(
        self, mock_get_connection: MagicMock
    ) -> None:
        """カスタムスキーマを指定した場合のテスト"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ("audit_logs_user_id_fkey", "user_id", "users", "id"),
        ]

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_connection.return_value = mock_conn

        # カスタムスキーマでテスト実行
        result = get_foreign_keys_impl("audit_logs", schema="audit")

        # 検証
        assert "| audit_logs_user_id_fkey | user_id | users | id |" in result

        # パラメータが正しく渡されたか確認
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        assert call_args[0][1] == ("audit_logs", "audit")

    @patch("pgmcp.tools.foreign_keys.get_connection")
    def test_get_foreign_keys_no_foreign_keys(
        self, mock_get_connection: MagicMock
    ) -> None:
        """外部キーが存在しない場合のテスト"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_connection.return_value = mock_conn

        result = get_foreign_keys_impl("users")

        assert result == "外部キーが見つかりませんでした。"
