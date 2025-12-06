"""
ER図生成ツールの統合テスト
"""

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from pgmcp.tools import generate_er_diagram_impl


def validate_mermaid_syntax(mermaid_content: str) -> tuple[bool, str]:
    """
    Mermaid CLIを使用してMermaid構文を検証

    Args:
        mermaid_content: Mermaid形式の文字列

    Returns:
        (is_valid, error_message) のタプル
    """
    # mmdcコマンドが利用可能か確認
    if not shutil.which("mmdc"):
        return True, "mmdc not available, skipping validation"

    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = Path(tmpdir) / "diagram.mmd"
        output_file = Path(tmpdir) / "diagram.svg"
        puppeteer_config_file = Path(tmpdir) / "puppeteer-config.json"

        input_file.write_text(mermaid_content, encoding="utf-8")

        # Puppeteer config with --no-sandbox for CI environments
        puppeteer_config = {"args": ["--no-sandbox", "--disable-setuid-sandbox"]}
        puppeteer_config_file.write_text(json.dumps(puppeteer_config), encoding="utf-8")

        try:
            result = subprocess.run(
                [
                    "mmdc",
                    "-i",
                    str(input_file),
                    "-o",
                    str(output_file),
                    "-p",
                    str(puppeteer_config_file),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0 and output_file.exists():
                return True, ""
            return False, result.stderr
        except subprocess.TimeoutExpired:
            return False, "Mermaid CLI timed out"
        except Exception as e:
            return False, str(e)


class TestGenerateErDiagramIntegration:
    """generate_er_diagram の統合テスト"""

    def test_generate_er_diagram_public_schema(self, db_connection: bool) -> None:
        """publicスキーマのER図を生成"""
        result = generate_er_diagram_impl(schema="public")

        # Mermaid ER図形式であることを確認
        assert "erDiagram" in result

        # 基本テーブルが含まれていることを確認
        assert "users {" in result
        assert "orders {" in result
        assert "products {" in result

        # カラム情報が含まれていることを確認
        assert "integer id PK" in result
        assert "varchar" in result

    def test_generate_er_diagram_with_foreign_keys(self, db_connection: bool) -> None:
        """外部キー関係を含むER図を生成"""
        result = generate_er_diagram_impl(
            schema="public",
            tables=["users", "orders"],
        )

        # テーブル定義が含まれていることを確認
        assert "users {" in result
        assert "orders {" in result

        # 外部キー関係が含まれていることを確認
        assert 'users ||--o{ orders : "has"' in result

        # FKマーカーが含まれていることを確認
        assert "FK" in result

    def test_generate_er_diagram_with_table_filter(self, db_connection: bool) -> None:
        """テーブルフィルターを指定してER図を生成"""
        result = generate_er_diagram_impl(
            schema="public",
            tables=["users", "products"],
        )

        # 指定したテーブルが含まれていることを確認
        assert "users {" in result
        assert "products {" in result

        # 指定していないテーブルが含まれていないことを確認
        assert "orders {" not in result

    def test_generate_er_diagram_audit_schema(self, db_connection: bool) -> None:
        """auditスキーマのER図を生成"""
        result = generate_er_diagram_impl(schema="audit")

        # auditスキーマのテーブルが含まれていることを確認
        assert "logs {" in result

        # jsonb型が含まれていることを確認
        assert "jsonb" in result

    def test_generate_er_diagram_nonexistent_schema(self, db_connection: bool) -> None:
        """存在しないスキーマの場合"""
        result = generate_er_diagram_impl(schema="nonexistent_schema")

        assert result == "対象のテーブルが見つかりませんでした。"

    def test_generate_er_diagram_self_reference(self, db_connection: bool) -> None:
        """自己参照テーブルのER図を生成"""
        result = generate_er_diagram_impl(
            schema="public",
            tables=["self_reference_test"],
        )

        # 自己参照テーブルが含まれていることを確認
        assert "self_reference_test {" in result

        # parent_idが外部キーとしてマークされていることを確認
        assert "parent_id" in result
        assert "FK" in result

    def test_generate_er_diagram_multiple_foreign_keys(
        self, db_connection: bool
    ) -> None:
        """複数の外部キーを持つテーブルのER図を生成"""
        result = generate_er_diagram_impl(
            schema="public",
            tables=["users", "categories", "tags", "multiple_fk_test"],
        )

        # すべてのテーブルが含まれていることを確認
        assert "users {" in result
        assert "categories {" in result
        assert "tags {" in result
        assert "multiple_fk_test {" in result

        # 外部キー関係が含まれていることを確認
        assert "users ||--o{ multiple_fk_test" in result or "has" in result

    def test_generate_er_diagram_cascade_tables(self, db_connection: bool) -> None:
        """カスケード削除・更新テーブルのER図を生成"""
        result = generate_er_diagram_impl(
            schema="public",
            tables=["cascade_parent", "cascade_child", "cascade_set_null"],
        )

        # すべてのテーブルが含まれていることを確認
        assert "cascade_parent {" in result
        assert "cascade_child {" in result
        assert "cascade_set_null {" in result

        # 外部キー関係が含まれていることを確認
        assert "cascade_parent ||--o{ cascade_child" in result

    def test_generate_er_diagram_with_comments(self, db_connection: bool) -> None:
        """コメント付きテーブルのER図を生成"""
        result = generate_er_diagram_impl(
            schema="public",
            tables=["users"],
        )

        # コメントが含まれていることを確認
        assert "ユーザーID" in result
        assert "ユーザー名" in result

    def test_generate_er_diagram_data_types(self, db_connection: bool) -> None:
        """様々なデータ型のテーブルのER図を生成"""
        result = generate_er_diagram_impl(
            schema="public",
            tables=["numeric_types_test", "string_types_test", "datetime_types_test"],
        )

        # テーブルが含まれていることを確認
        assert "numeric_types_test {" in result
        assert "string_types_test {" in result
        assert "datetime_types_test {" in result

        # 様々なデータ型が含まれていることを確認
        assert "smallint" in result
        assert "bigint" in result
        assert "varchar" in result
        assert "text" in result

    def test_generate_er_diagram_json_types(self, db_connection: bool) -> None:
        """JSON型テーブルのER図を生成"""
        result = generate_er_diagram_impl(
            schema="public",
            tables=["json_types_test"],
        )

        assert "json_types_test {" in result
        assert "json" in result
        assert "jsonb" in result

    def test_generate_er_diagram_array_types(self, db_connection: bool) -> None:
        """配列型テーブルのER図を生成"""
        result = generate_er_diagram_impl(
            schema="public",
            tables=["array_types_test"],
        )

        assert "array_types_test {" in result
        assert "integer_array" in result or "int_array" in result

    def test_generate_er_diagram_many_columns(self, db_connection: bool) -> None:
        """多数のカラムを持つテーブルのER図を生成"""
        result = generate_er_diagram_impl(
            schema="public",
            tables=["many_columns_test"],
        )

        assert "many_columns_test {" in result
        # カラムが含まれていることを確認
        assert "col_01" in result
        assert "col_30" in result

    def test_generate_er_diagram_warning_for_all_tables(
        self, db_connection: bool
    ) -> None:
        """全テーブル取得時（テーブル数が100以下なら警告なし）"""
        result = generate_er_diagram_impl(schema="public")

        # テストデータベースのテーブル数は100以下なので警告は出ない
        # 100を超える場合のみ警告が表示される
        assert "erDiagram" in result

    def test_generate_er_diagram_virtual_foreign_keys(
        self, db_connection: bool
    ) -> None:
        """Virtual Foreign Keys（命名規則から推測される外部キー）の検出"""
        # cascade_set_null テーブルには parent_id があり、
        # cascade_parent テーブルへの参照が推測される
        # ただし、実際にFKとして定義されている場合は実線で表示される
        result = generate_er_diagram_impl(
            schema="public",
            tables=["cascade_parent", "cascade_set_null"],
        )

        # テーブル間の関係が何らかの形で表現されていることを確認
        assert "cascade_parent" in result
        assert "cascade_set_null" in result
        # 実際のFKまたはVirtual FKとして関係が表現される
        assert "||--o{" in result or "||..o{" in result

    def test_generate_er_diagram_virtual_foreign_keys_uuid_pk(
        self, db_connection: bool
    ) -> None:
        """UUID型PKと *_id カラムによるVirtual FKの検出"""
        result = generate_er_diagram_impl(
            schema="public",
            tables=["vfk_uuid_parent", "vfk_uuid_child"],
        )

        assert "vfk_uuid_parent {" in result
        assert "vfk_uuid_child {" in result
        assert 'vfk_uuid_parent ||..o{ vfk_uuid_child : "references"' in result
        # 親はPKのみ、子の参照カラムにFKマーカー
        assert "uuid vfk_uuid_parent_id PK" in result
        assert "uuid vfk_uuid_parent_id FK" in result
        assert "uuid vfk_uuid_parent_id PK,FK" not in result

    def test_generate_er_diagram_virtual_foreign_keys_no_pk(
        self, db_connection: bool
    ) -> None:
        """BIGINT型PKと *_no カラムによるVirtual FKの検出"""
        result = generate_er_diagram_impl(
            schema="public",
            tables=["vfk_no_parent", "vfk_no_child"],
        )

        assert "vfk_no_parent {" in result
        assert "vfk_no_child {" in result
        assert 'vfk_no_parent ||..o{ vfk_no_child : "references"' in result
        assert "bigint vfk_no_parent_no PK" in result
        # 子テーブルの参照カラムにFKマーカーが付く
        assert "bigint vfk_no_parent_no FK" in result

    def test_generate_er_diagram_virtual_foreign_keys_complex(
        self, db_connection: bool
    ) -> None:
        """20個超のテーブルを含む複雑なVirtual FKシナリオ"""
        tables = [
            "vfk_uuid_customer",
            "vfk_uuid_address",
            "vfk_uuid_order",
            "vfk_uuid_order_item",
            "vfk_uuid_product",
            "vfk_uuid_category",
            "vfk_uuid_invoice",
            "vfk_uuid_payment",
            "vfk_uuid_payment_method",
            "vfk_uuid_shipment",
            "vfk_uuid_warehouse",
            "vfk_uuid_region",
            "vfk_uuid_shipment_event",
            "vfk_uuid_return_request",
            "vfk_uuid_return_reason",
            "vfk_uuid_loyalty_account",
            "vfk_uuid_loyalty_activity",
            "vfk_uuid_marketing_campaign",
            "vfk_uuid_campaign_enrollment",
            "vfk_uuid_coupon",
            "vfk_uuid_coupon_redemption",
            "vfk_no_customer",
            "vfk_no_order",
            "vfk_no_order_item",
            "vfk_no_product",
            "vfk_no_category",
            "vfk_no_supplier",
            "vfk_no_supplier_product",
            "vfk_no_warehouse",
            "vfk_no_region",
            "vfk_no_inventory",
        ]

        result = generate_er_diagram_impl(schema="public", tables=tables)

        assert "erDiagram" in result
        assert "vfk_uuid_customer {" in result and "vfk_no_customer {" in result
        # 代表的なVirtual FKが検出されていることを確認
        assert 'vfk_uuid_customer ||..o{ vfk_uuid_order : "references"' in result
        assert 'vfk_uuid_order ||..o{ vfk_uuid_order_item : "references"' in result
        assert 'vfk_uuid_order ||..o{ vfk_uuid_invoice : "references"' in result
        assert 'vfk_uuid_invoice ||..o{ vfk_uuid_payment : "references"' in result
        assert 'vfk_no_customer ||..o{ vfk_no_order : "references"' in result
        assert 'vfk_no_order ||..o{ vfk_no_order_item : "references"' in result


class TestMermaidSyntaxValidation:
    """Mermaid構文の検証テスト（Mermaid CLIが必要）"""

    @pytest.fixture
    def requires_mermaid_cli(self) -> bool:
        """Mermaid CLIが利用可能か確認"""
        if not shutil.which("mmdc"):
            pytest.skip("Mermaid CLI (mmdc) is not installed")
        return True

    def test_basic_er_diagram_syntax(
        self, db_connection: bool, requires_mermaid_cli: bool
    ) -> None:
        """基本的なER図がMermaid構文として有効か検証"""
        result = generate_er_diagram_impl(
            schema="public",
            tables=["users", "orders", "products"],
        )

        is_valid, error = validate_mermaid_syntax(result)
        assert is_valid, f"Mermaid構文エラー: {error}"

    def test_complex_er_diagram_syntax(
        self, db_connection: bool, requires_mermaid_cli: bool
    ) -> None:
        """複雑なER図（複数のテーブル、外部キー、コメント）が有効か検証"""
        result = generate_er_diagram_impl(
            schema="public",
            tables=[
                "users",
                "orders",
                "products",
                "categories",
                "tags",
                "multiple_fk_test",
            ],
        )

        is_valid, error = validate_mermaid_syntax(result)
        assert is_valid, f"Mermaid構文エラー: {error}"

    def test_self_reference_er_diagram_syntax(
        self, db_connection: bool, requires_mermaid_cli: bool
    ) -> None:
        """自己参照テーブルを含むER図が有効か検証"""
        result = generate_er_diagram_impl(
            schema="public",
            tables=["self_reference_test"],
        )

        is_valid, error = validate_mermaid_syntax(result)
        assert is_valid, f"Mermaid構文エラー: {error}"

    def test_various_data_types_syntax(
        self, db_connection: bool, requires_mermaid_cli: bool
    ) -> None:
        """様々なデータ型を含むER図が有効か検証"""
        result = generate_er_diagram_impl(
            schema="public",
            tables=[
                "numeric_types_test",
                "string_types_test",
                "datetime_types_test",
                "json_types_test",
                "array_types_test",
            ],
        )

        is_valid, error = validate_mermaid_syntax(result)
        assert is_valid, f"Mermaid構文エラー: {error}"

    def test_audit_schema_syntax(
        self, db_connection: bool, requires_mermaid_cli: bool
    ) -> None:
        """別スキーマのER図が有効か検証"""
        result = generate_er_diagram_impl(schema="audit")

        is_valid, error = validate_mermaid_syntax(result)
        assert is_valid, f"Mermaid構文エラー: {error}"
