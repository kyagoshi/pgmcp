"""
外部キー関連ツールの統合テスト
"""

from pgmcp.tools import get_foreign_keys_impl


class TestGetForeignKeysIntegration:
    """get_foreign_keys の統合テスト"""

    def test_get_orders_foreign_keys(self, db_connection: bool) -> None:
        """ordersテーブルの外部キー情報を取得"""
        result = get_foreign_keys_impl("orders", schema="public")

        # ヘッダーの確認
        assert (
            "| constraint_name | column_name | foreign_table | foreign_column |"
            in result
        )

        # 外部キーの確認
        assert "orders_user_id_fkey" in result
        assert "user_id" in result
        assert "users" in result

    def test_get_multiple_fk_table_foreign_keys(self, db_connection: bool) -> None:
        """multiple_fk_testテーブルの外部キー情報を取得（複数の外部キー）"""
        result = get_foreign_keys_impl("multiple_fk_test", schema="public")

        # 複数の外部キーが含まれていることを確認
        assert "user_id" in result
        assert "users" in result
        assert "category_id" in result
        assert "categories" in result
        assert "tag_id" in result
        assert "tags" in result

    def test_get_self_reference_foreign_keys(self, db_connection: bool) -> None:
        """self_reference_testテーブルの外部キー情報を取得（自己参照）"""
        result = get_foreign_keys_impl("self_reference_test", schema="public")

        assert "parent_id" in result
        assert "self_reference_test" in result  # 自己参照

    def test_get_cascade_child_foreign_keys(self, db_connection: bool) -> None:
        """cascade_childテーブルの外部キー情報を取得"""
        result = get_foreign_keys_impl("cascade_child", schema="public")

        assert "parent_id" in result
        assert "cascade_parent" in result

    def test_get_users_foreign_keys(self, db_connection: bool) -> None:
        """usersテーブルの外部キー情報を取得（外部キーなし）"""
        result = get_foreign_keys_impl("users", schema="public")

        assert result == "外部キーが見つかりませんでした。"

    def test_get_nonexistent_table_foreign_keys(self, db_connection: bool) -> None:
        """存在しないテーブルの場合"""
        result = get_foreign_keys_impl("nonexistent_table", schema="public")

        assert result == "外部キーが見つかりませんでした。"
