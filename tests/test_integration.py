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

from pgmcp.server import (
    _get_table_indexes_impl,
    _get_table_schema_impl,
    _list_tables_impl,
    get_connection,
)


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
        assert (
            "| column_name | data_type | nullable | default | PK | comment |" in result
        )

        # カラムの確認
        assert "| id | integer |" in result
        assert "✓" in result  # 主キーマーカー
        assert "| name | character varying(100) | NO |" in result
        assert "| email | character varying(255) | YES |" in result
        assert "| created_at | timestamp with time zone |" in result

        # コメントの確認
        assert "ユーザーID" in result
        assert "ユーザー名" in result
        assert "メールアドレス" in result

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


class TestNumericTypesIntegration:
    """数値型テストテーブルの統合テスト"""

    def test_numeric_types_table_schema(self, db_connection: bool) -> None:
        """数値型テーブルのスキーマを取得"""
        result = _get_table_schema_impl("numeric_types_test", schema="public")

        assert "| smallint_col | smallint |" in result
        assert "| bigint_col | bigint |" in result
        assert "| numeric_col | numeric(20,5) |" in result
        assert "| real_col | real |" in result
        assert "| double_col | double precision |" in result


class TestStringTypesIntegration:
    """文字列型テストテーブルの統合テスト"""

    def test_string_types_table_schema(self, db_connection: bool) -> None:
        """文字列型テーブルのスキーマを取得"""
        result = _get_table_schema_impl("string_types_test", schema="public")

        assert "| char_col | character(10) |" in result
        assert "| varchar_col | character varying(255) |" in result
        assert "| text_col | text |" in result


class TestDatetimeTypesIntegration:
    """日付・時刻型テストテーブルの統合テスト"""

    def test_datetime_types_table_schema(self, db_connection: bool) -> None:
        """日付・時刻型テーブルのスキーマを取得"""
        result = _get_table_schema_impl("datetime_types_test", schema="public")

        assert "| date_col | date |" in result
        assert "| time_col | time without time zone |" in result
        assert "| time_with_tz | time with time zone |" in result
        assert "| timestamp_col | timestamp without time zone |" in result
        assert "| timestamp_with_tz | timestamp with time zone |" in result
        assert "| interval_col | interval |" in result


class TestJsonTypesIntegration:
    """JSON型テストテーブルの統合テスト"""

    def test_json_types_table_schema(self, db_connection: bool) -> None:
        """JSON型テーブルのスキーマを取得"""
        result = _get_table_schema_impl("json_types_test", schema="public")

        assert "| json_col | json |" in result
        assert "| jsonb_col | jsonb |" in result


class TestArrayTypesIntegration:
    """配列型テストテーブルの統合テスト"""

    def test_array_types_table_schema(self, db_connection: bool) -> None:
        """配列型テーブルのスキーマを取得"""
        result = _get_table_schema_impl("array_types_test", schema="public")

        assert "| int_array | integer[] |" in result
        assert "| text_array | text[] |" in result
        assert "| multi_dim_array | integer[] |" in result


class TestUuidTypesIntegration:
    """UUID型テストテーブルの統合テスト"""

    def test_uuid_types_table_schema(self, db_connection: bool) -> None:
        """UUID型テーブルのスキーマを取得"""
        result = _get_table_schema_impl("uuid_types_test", schema="public")

        assert "| id | uuid |" in result
        assert "| reference_id | uuid |" in result


class TestBinaryTypesIntegration:
    """バイナリ型テストテーブルの統合テスト"""

    def test_binary_types_table_schema(self, db_connection: bool) -> None:
        """バイナリ型テーブルのスキーマを取得"""
        result = _get_table_schema_impl("binary_types_test", schema="public")

        assert "| binary_data | bytea |" in result


class TestEdgeCasesIntegration:
    """エッジケーステストテーブルの統合テスト"""

    def test_nullable_table_schema(self, db_connection: bool) -> None:
        """NULL値を含むテーブルのスキーマを取得"""
        result = _get_table_schema_impl("nullable_test", schema="public")

        assert "| required_col | character varying(100) | NO |" in result
        assert "| nullable_col | character varying(100) | YES |" in result
        assert "| nullable_with_default | character varying(100) | YES |" in result

    def test_empty_default_table_schema(self, db_connection: bool) -> None:
        """空文字デフォルト値テーブルのスキーマを取得"""
        result = _get_table_schema_impl("empty_default_test", schema="public")

        assert "| empty_string_default |" in result
        assert "| space_default |" in result
        assert "| normal_default |" in result

    def test_special_characters_table_exists(self, db_connection: bool) -> None:
        """特殊文字を含むテーブルが一覧に含まれることを確認"""
        result = _list_tables_impl(schema="public")

        assert "Special-Table_Name!@#" in result

    def test_special_characters_table_schema(self, db_connection: bool) -> None:
        """特殊文字を含むテーブルのスキーマを取得"""
        result = _get_table_schema_impl("Special-Table_Name!@#", schema="public")

        assert "Column With Spaces" in result
        assert "column-with-dashes" in result
        assert "日本語カラム" in result

    def test_long_table_name_exists(self, db_connection: bool) -> None:
        """長いテーブル名のテーブルが一覧に含まれることを確認"""
        result = _list_tables_impl(schema="public")

        # PostgreSQLは識別子を63文字に切り詰めるため、切り詰められた名前で確認
        assert (
            "this_is_a_very_long_table_name_that_tests_the_limits_of_identif" in result
        )

    def test_long_table_name_schema(self, db_connection: bool) -> None:
        """長いテーブル名のテーブルのスキーマを取得"""
        # PostgreSQLは識別子を63文字に切り詰める
        result = _get_table_schema_impl(
            "this_is_a_very_long_table_name_that_tests_the_limits_of_identif",
            schema="public",
        )

        # カラム名も63文字に切り詰められている
        assert (
            "this_is_a_very_long_column_name_that_also_tests_identifier_limi" in result
        )


class TestComplexRelationsIntegration:
    """複雑なリレーションテストテーブルの統合テスト"""

    def test_composite_pk_table_schema(self, db_connection: bool) -> None:
        """複合主キーテーブルのスキーマを取得"""
        result = _get_table_schema_impl("composite_pk_test", schema="public")

        # 両方のキーパートが主キーとしてマークされていることを確認
        assert "| key_part1 | integer | NO |" in result
        assert "| key_part2 | character varying(50) | NO |" in result
        # 少なくとも2つの主キーマーカーがあることを確認
        assert result.count("✓") >= 2

    def test_multiple_fk_table_schema(self, db_connection: bool) -> None:
        """複数外部キーテーブルのスキーマを取得"""
        result = _get_table_schema_impl("multiple_fk_test", schema="public")

        assert "| user_id | integer |" in result
        assert "| category_id | integer |" in result
        assert "| tag_id | integer |" in result

    def test_self_reference_table_schema(self, db_connection: bool) -> None:
        """自己参照外部キーテーブルのスキーマを取得"""
        result = _get_table_schema_impl("self_reference_test", schema="public")

        assert "| parent_id | integer | YES |" in result

    def test_cascade_tables_exist(self, db_connection: bool) -> None:
        """カスケードテーブルが一覧に含まれることを確認"""
        result = _list_tables_impl(schema="public")

        assert "cascade_parent" in result
        assert "cascade_child" in result
        assert "cascade_set_null" in result


class TestOtherTablesIntegration:
    """その他のテストテーブルの統合テスト"""

    def test_many_columns_table_schema(self, db_connection: bool) -> None:
        """大量カラムテーブルのスキーマを取得"""
        result = _get_table_schema_impl("many_columns_test", schema="public")

        # 複数のカラムが含まれていることを確認
        assert "| col_01 |" in result
        assert "| col_10 |" in result
        assert "| col_20 |" in result
        assert "| col_30 |" in result

    def test_partitioned_table_exists(self, db_connection: bool) -> None:
        """パーティションテーブルが一覧に含まれることを確認"""
        result = _list_tables_impl(schema="public")

        assert "partitioned_logs" in result
        assert "partitioned_logs_2024" in result
        assert "partitioned_logs_2025" in result

    def test_inheritance_tables_exist(self, db_connection: bool) -> None:
        """継承テーブルが一覧に含まれることを確認"""
        result = _list_tables_impl(schema="public")

        assert "base_entity" in result
        assert "person_entity" in result
        assert "organization_entity" in result

    def test_inheritance_child_table_schema(self, db_connection: bool) -> None:
        """継承子テーブルのスキーマを取得（親のカラムも含む）"""
        result = _get_table_schema_impl("person_entity", schema="public")

        # 親テーブルのカラム
        assert "| id | integer |" in result
        assert "| name | character varying(100) |" in result
        assert "| created_at |" in result
        # 子テーブル固有のカラム
        assert "| email | character varying(255) |" in result
        assert "| birth_date | date |" in result


class TestListTablesExtended:
    """list_tables の拡張統合テスト"""

    def test_list_tables_includes_all_new_tables(self, db_connection: bool) -> None:
        """すべての新しいテストテーブルが一覧に含まれることを確認"""
        result = _list_tables_impl(schema="public")

        expected_tables = [
            "numeric_types_test",
            "string_types_test",
            "datetime_types_test",
            "json_types_test",
            "array_types_test",
            "uuid_types_test",
            "binary_types_test",
            "nullable_test",
            "empty_default_test",
            "composite_pk_test",
            "categories",
            "tags",
            "multiple_fk_test",
            "self_reference_test",
            "cascade_parent",
            "cascade_child",
            "cascade_set_null",
            "many_columns_test",
        ]

        for table in expected_tables:
            assert table in result, f"テーブル '{table}' が一覧に含まれていません"


class TestGetTableIndexesIntegration:
    """get_table_indexes の統合テスト"""

    def test_get_users_table_indexes(self, db_connection: bool) -> None:
        """usersテーブルのインデックス情報を取得"""
        result = _get_table_indexes_impl("users", schema="public")

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
        result = _get_table_indexes_impl("orders", schema="public")

        assert "orders_pkey" in result
        assert "orders_user_id_idx" in result
        assert "orders_status_idx" in result
        # 複合インデックスの確認
        assert "orders_user_status_idx" in result
        assert "orders_user_created_idx" in result

    def test_get_products_table_indexes(self, db_connection: bool) -> None:
        """productsテーブルのインデックス情報を取得（GINインデックスを含む）"""
        result = _get_table_indexes_impl("products", schema="public")

        assert "products_pkey" in result
        assert "products_name_idx" in result
        assert "products_price_idx" in result
        assert "gin" in result  # GINインデックス
        assert "btree" in result

    def test_get_audit_logs_table_indexes(self, db_connection: bool) -> None:
        """audit.logsテーブルのインデックス情報を取得（別スキーマ）"""
        result = _get_table_indexes_impl("logs", schema="audit")

        assert "logs_pkey" in result

    def test_get_nonexistent_table_indexes(self, db_connection: bool) -> None:
        """存在しないテーブルの場合"""
        result = _get_table_indexes_impl("nonexistent_table", schema="public")

        assert result == "インデックスが見つかりませんでした。"

    def test_composite_pk_indexes(self, db_connection: bool) -> None:
        """複合主キーテーブルのインデックス情報を取得"""
        result = _get_table_indexes_impl("composite_pk_test", schema="public")

        assert "composite_pk_test_pkey" in result
        # 複合主キーのカラムが含まれていることを確認
        assert "key_part1" in result
        assert "key_part2" in result
