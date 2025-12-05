"""
インデックス関連ツールのユニットテスト
"""

from unittest.mock import MagicMock, patch

from pgmcp.tools import get_table_indexes_impl


class TestGetTableIndexes:
    """get_table_indexes ツールのテスト"""

    @patch("pgmcp.tools.indexes.get_connection")
    def test_get_table_indexes_returns_indexes(
        self, mock_get_connection: MagicMock
    ) -> None:
        """インデックス情報がMarkdown Table形式で正しく返されることを確認"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            (
                "users_pkey",
                "id",
                True,
                "btree",
                "CREATE UNIQUE INDEX users_pkey ON public.users USING btree (id)",
            ),
            (
                "users_email_idx",
                "email",
                True,
                "btree",
                "CREATE UNIQUE INDEX users_email_idx ON public.users USING btree (email) WHERE (email IS NOT NULL)",
            ),
            (
                "users_created_at_idx",
                "created_at",
                False,
                "btree",
                "CREATE INDEX users_created_at_idx ON public.users USING btree (created_at)",
            ),
        ]

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_connection.return_value = mock_conn

        # テスト実行
        result = get_table_indexes_impl("users")

        # 検証
        assert "| index_name | columns | unique | type | definition |" in result
        assert "| users_pkey | id | ✓ | btree |" in result
        assert "| users_email_idx | email | ✓ | btree |" in result
        assert "| users_created_at_idx | created_at |  | btree |" in result

    @patch("pgmcp.tools.indexes.get_connection")
    def test_get_table_indexes_with_custom_schema(
        self, mock_get_connection: MagicMock
    ) -> None:
        """カスタムスキーマを指定した場合のテスト"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            (
                "logs_pkey",
                "id",
                True,
                "btree",
                "CREATE UNIQUE INDEX logs_pkey ON audit.logs USING btree (id)",
            ),
        ]

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_connection.return_value = mock_conn

        # カスタムスキーマでテスト実行
        result = get_table_indexes_impl("logs", schema="audit")

        # 検証
        assert "| logs_pkey | id | ✓ | btree |" in result

        # パラメータが正しく渡されたか確認
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        assert call_args[0][1] == ("logs", "audit")

    @patch("pgmcp.tools.indexes.get_connection")
    def test_get_table_indexes_no_indexes(self, mock_get_connection: MagicMock) -> None:
        """インデックスが存在しない場合のテスト"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_connection.return_value = mock_conn

        result = get_table_indexes_impl("nonexistent_table")

        assert result == "インデックスが見つかりませんでした。"
