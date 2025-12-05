"""
インデックス関連ツールの統合テスト
"""

from pgmcp.tools import get_table_indexes_impl


class TestGetTableIndexesIntegration:
    """get_table_indexes の統合テスト"""

    def test_get_users_table_indexes(self, db_connection: bool) -> None:
        """usersテーブルのインデックス情報を取得"""
        result = get_table_indexes_impl("users", schema="public")

        # ヘッダーの確認
        assert "| index_name | columns | unique | type | definition |" in result

        # インデックスの確認
        assert "users_pkey" in result
        assert "users_email_idx" in result
        assert "users_created_at_idx" in result
        assert "btree" in result
        assert "✓" in result  # ユニークインデックスマーカー

    def test_get_orders_table_indexes(self, db_connection: bool) -> None:
        """ordersテーブルのインデックス情報を取得"""
        result = get_table_indexes_impl("orders", schema="public")

        assert "orders_pkey" in result
        assert "orders_user_id_idx" in result
        assert "orders_status_idx" in result
        # 複合インデックスの確認
        assert "orders_user_status_idx" in result
        assert "orders_user_created_idx" in result

    def test_get_products_table_indexes(self, db_connection: bool) -> None:
        """productsテーブルのインデックス情報を取得（GINインデックスを含む）"""
        result = get_table_indexes_impl("products", schema="public")

        assert "products_pkey" in result
        assert "products_name_idx" in result
        assert "products_price_idx" in result
        assert "gin" in result  # GINインデックス
        assert "btree" in result

    def test_get_audit_logs_table_indexes(self, db_connection: bool) -> None:
        """audit.logsテーブルのインデックス情報を取得（別スキーマ）"""
        result = get_table_indexes_impl("logs", schema="audit")

        assert "logs_pkey" in result

    def test_get_nonexistent_table_indexes(self, db_connection: bool) -> None:
        """存在しないテーブルの場合"""
        result = get_table_indexes_impl("nonexistent_table", schema="public")

        assert result == "インデックスが見つかりませんでした。"

    def test_composite_pk_indexes(self, db_connection: bool) -> None:
        """複合主キーテーブルのインデックス情報を取得"""
        result = get_table_indexes_impl("composite_pk_test", schema="public")

        assert "composite_pk_test_pkey" in result
        # 複合主キーのカラムが含まれていることを確認
        assert "key_part1" in result
        assert "key_part2" in result
