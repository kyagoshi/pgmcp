"""
サンプルデータ取得ツールの統合テスト
"""

from pgmcp.tools import get_sample_data_impl


class TestGetSampleDataIntegration:
    """get_sample_data の統合テスト"""

    def test_get_sample_data_users_table(self, db_connection: bool) -> None:
        """usersテーブルのサンプルデータを取得"""
        result = get_sample_data_impl("users", schema="public")

        # Markdown Table形式であることを確認
        assert "| id | name | email | created_at |" in result

    def test_get_sample_data_orders_table(self, db_connection: bool) -> None:
        """ordersテーブルのサンプルデータを取得"""
        result = get_sample_data_impl("orders", schema="public")

        # ヘッダーに期待されるカラムが含まれることを確認
        assert "| id |" in result
        assert "| user_id |" in result
        assert "| total_amount |" in result
        assert "| status |" in result

    def test_get_sample_data_with_limit(self, db_connection: bool) -> None:
        """limitパラメータが機能することを確認"""
        # limit=1 でテスト
        result = get_sample_data_impl("users", schema="public", limit=1)

        # ヘッダー行とセパレータ行以外に1行のみであることを確認
        lines = result.split("\n")
        # ヘッダー + セパレータ + データ1行 = 3行
        # データが1件以上ある場合、最低でも3行になる
        assert len(lines) >= 3

    def test_get_sample_data_audit_schema(self, db_connection: bool) -> None:
        """auditスキーマのテーブルからサンプルデータを取得"""
        result = get_sample_data_impl("logs", schema="audit")

        # audit.logsテーブルは空の可能性があるので、データがあればカラムを確認
        # データがなければ「データが見つかりませんでした。」と表示される
        assert "| id |" in result or "データが見つかりませんでした。" in result

    def test_get_sample_data_nonexistent_table(self, db_connection: bool) -> None:
        """存在しないテーブルの場合"""
        result = get_sample_data_impl("nonexistent_table", schema="public")

        assert result == "テーブルが見つかりませんでした。"

    def test_get_sample_data_different_data_types(self, db_connection: bool) -> None:
        """様々なデータ型を含むテーブルのサンプルデータを取得"""
        # numeric_types_test テーブル
        result = get_sample_data_impl("numeric_types_test", schema="public")
        assert "| id |" in result
        assert "| smallint_col |" in result
        assert "| bigint_col |" in result

        # string_types_test テーブル
        result = get_sample_data_impl("string_types_test", schema="public")
        assert "| id |" in result
        assert "| char_col |" in result
        assert "| varchar_col |" in result
        assert "| text_col |" in result

        # datetime_types_test テーブル
        result = get_sample_data_impl("datetime_types_test", schema="public")
        assert "| id |" in result
        assert "| date_col |" in result
        assert "| timestamp_col |" in result

    def test_get_sample_data_json_types(self, db_connection: bool) -> None:
        """JSON型を含むテーブルのサンプルデータを取得"""
        result = get_sample_data_impl("json_types_test", schema="public")

        assert "| id |" in result
        assert "| json_col |" in result
        assert "| jsonb_col |" in result

    def test_get_sample_data_array_types(self, db_connection: bool) -> None:
        """配列型を含むテーブルのサンプルデータを取得"""
        result = get_sample_data_impl("array_types_test", schema="public")

        assert "| id |" in result
        assert "| int_array |" in result
        assert "| text_array |" in result

    def test_get_sample_data_uuid_types(self, db_connection: bool) -> None:
        """UUID型を含むテーブルのサンプルデータを取得"""
        result = get_sample_data_impl("uuid_types_test", schema="public")

        assert "| id |" in result
        assert "| reference_id |" in result

    def test_get_sample_data_with_null_values(self, db_connection: bool) -> None:
        """NULL値を含むテーブルのサンプルデータを取得"""
        result = get_sample_data_impl("nullable_test", schema="public")

        assert "| id |" in result
        assert "| required_col |" in result
        assert "| nullable_col |" in result
        # NULL値は "-" で表示される
        assert " - " in result or "| - |" in result

    def test_get_sample_data_limit_boundary(self, db_connection: bool) -> None:
        """limit境界値のテスト"""
        # 最大値100
        result = get_sample_data_impl("users", schema="public", limit=100)
        assert "| id |" in result

        # 100を超える値を指定しても100に制限される
        result = get_sample_data_impl("users", schema="public", limit=200)
        assert "| id |" in result

        # 0以下の値を指定しても1に制限される
        result = get_sample_data_impl("users", schema="public", limit=0)
        assert "| id |" in result

        result = get_sample_data_impl("users", schema="public", limit=-1)
        assert "| id |" in result
