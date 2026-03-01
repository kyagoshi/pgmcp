"""
サンプルデータ取得ツールのユニットテスト
"""

from unittest.mock import MagicMock, patch

from pgmcp.tools import get_sample_data_impl


class TestGetSampleData:
    """get_sample_data ツールのテスト"""

    @patch("pgmcp.tools.sample_data.get_connection")
    def test_get_sample_data_returns_data(self, mock_get_connection: MagicMock) -> None:
        """サンプルデータが正しくMarkdown Table形式で返されることを確認"""
        # モックカーソルの設定
        mock_cursor = MagicMock()

        # カラム名のモック
        mock_cursor.fetchall.side_effect = [
            [("id",), ("name",), ("email",)],  # カラム名
            [
                (1, "Alice", "alice@example.com"),
                (2, "Bob", "bob@example.com"),
            ],  # データ
        ]

        # コンテキストマネージャのモック
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_connection.return_value = mock_conn

        # テスト実行
        result = get_sample_data_impl("users")

        # 検証
        assert "| id | name | email |" in result
        assert "| 1 | Alice | alice@example.com |" in result
        assert "| 2 | Bob | bob@example.com |" in result

    @patch("pgmcp.tools.sample_data.get_connection")
    def test_get_sample_data_with_null_values(
        self, mock_get_connection: MagicMock
    ) -> None:
        """NULL値を含むデータのテスト"""
        mock_cursor = MagicMock()

        mock_cursor.fetchall.side_effect = [
            [("id",), ("name",), ("email",)],
            [
                (1, "Alice", None),
                (2, "Bob", "bob@example.com"),
            ],
        ]

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_connection.return_value = mock_conn

        result = get_sample_data_impl("users")

        # NULL値が "-" で表示されることを確認
        assert "| 1 | Alice | - |" in result
        assert "| 2 | Bob | bob@example.com |" in result

    @patch("pgmcp.tools.sample_data.get_connection")
    def test_get_sample_data_with_custom_schema(
        self, mock_get_connection: MagicMock
    ) -> None:
        """カスタムスキーマを指定した場合のテスト"""
        mock_cursor = MagicMock()

        mock_cursor.fetchall.side_effect = [
            [("id",), ("action",)],
            [(1, "INSERT"), (2, "UPDATE")],
        ]

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_connection.return_value = mock_conn

        result = get_sample_data_impl("logs", schema="audit")

        assert "| id | action |" in result
        assert "| 1 | INSERT |" in result
        assert "| 2 | UPDATE |" in result

    @patch("pgmcp.tools.sample_data.get_connection")
    def test_get_sample_data_with_custom_limit(
        self, mock_get_connection: MagicMock
    ) -> None:
        """カスタムlimitを指定した場合のテスト"""
        mock_cursor = MagicMock()

        mock_cursor.fetchall.side_effect = [
            [("id",), ("name",)],
            [(1, "Alice"), (2, "Bob"), (3, "Charlie")],
        ]

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_connection.return_value = mock_conn

        get_sample_data_impl("users", limit=3)

        # limitパラメータが正しく渡されたか確認
        # 2回目のexecute呼び出しでlimitが使われる
        call_args_list = mock_cursor.execute.call_args_list
        assert len(call_args_list) == 2
        # 2回目の呼び出しの引数を確認（limitが3であること）
        assert call_args_list[1][0][1] == (3,)

    @patch("pgmcp.tools.sample_data.get_connection")
    def test_get_sample_data_limit_max_constraint(
        self, mock_get_connection: MagicMock
    ) -> None:
        """limitが最大値を超える場合のテスト"""
        mock_cursor = MagicMock()

        mock_cursor.fetchall.side_effect = [
            [("id",)],
            [(1,)],
        ]

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_connection.return_value = mock_conn

        # limitに200を指定しても100に制限される
        get_sample_data_impl("users", limit=200)

        call_args_list = mock_cursor.execute.call_args_list
        # 2回目の呼び出しでlimitが100に制限されていることを確認
        assert call_args_list[1][0][1] == (100,)

    @patch("pgmcp.tools.sample_data.get_connection")
    def test_get_sample_data_limit_min_constraint(
        self, mock_get_connection: MagicMock
    ) -> None:
        """limitが最小値を下回る場合のテスト"""
        mock_cursor = MagicMock()

        mock_cursor.fetchall.side_effect = [
            [("id",)],
            [(1,)],
        ]

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_connection.return_value = mock_conn

        # limitに0を指定しても1に制限される
        get_sample_data_impl("users", limit=0)

        call_args_list = mock_cursor.execute.call_args_list
        # 2回目の呼び出しでlimitが1に制限されていることを確認
        assert call_args_list[1][0][1] == (1,)

    @patch("pgmcp.tools.sample_data.get_connection")
    def test_get_sample_data_nonexistent_table(
        self, mock_get_connection: MagicMock
    ) -> None:
        """存在しないテーブルの場合のテスト"""
        mock_cursor = MagicMock()
        # カラムが見つからない場合
        mock_cursor.fetchall.return_value = []

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_connection.return_value = mock_conn

        result = get_sample_data_impl("nonexistent_table")

        assert result == "テーブルが見つかりませんでした。"

    @patch("pgmcp.tools.sample_data.get_connection")
    def test_get_sample_data_empty_table(self, mock_get_connection: MagicMock) -> None:
        """データが空のテーブルの場合のテスト"""
        mock_cursor = MagicMock()

        mock_cursor.fetchall.side_effect = [
            [("id",), ("name",)],  # カラムは存在
            [],  # データは空
        ]

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_connection.return_value = mock_conn

        result = get_sample_data_impl("empty_table")

        assert result == "データが見つかりませんでした。"
