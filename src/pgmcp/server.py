"""
pgmcp - PostgreSQL MCP Server

PostgreSQLデータベースのテーブル一覧とスキーマ情報を提供するMCPサーバー
"""

from fastmcp import FastMCP

from pgmcp.tools import (
    generate_er_diagram_impl,
    get_foreign_keys_impl,
    get_table_indexes_impl,
    get_table_schema_impl,
    list_tables_impl,
)

# MCPサーバーインスタンスを作成
mcp = FastMCP("pgmcp")


@mcp.tool
def list_tables(schema: str = "public") -> str:
    """
    指定したスキーマのテーブル一覧を取得します。

    Args:
        schema: スキーマ名（デフォルト: "public"）

    Returns:
        テーブル情報のMarkdown Table形式の文字列。
    """
    return list_tables_impl(schema)


@mcp.tool
def get_table_schema(table_name: str, schema: str = "public") -> str:
    """
    指定したテーブルのカラム情報を取得します。

    Args:
        table_name: テーブル名
        schema: スキーマ名（デフォルト: "public"）

    Returns:
        カラム情報のMarkdown Table形式の文字列。
        各カラムはcolumn_name, data_type, nullable, default, PK, commentを含む。
    """
    return get_table_schema_impl(table_name, schema)


@mcp.tool
def get_table_indexes(table_name: str, schema: str = "public") -> str:
    """
    指定したテーブルのインデックス情報を取得します。

    Args:
        table_name: テーブル名
        schema: スキーマ名（デフォルト: "public"）

    Returns:
        インデックス情報のMarkdown Table形式の文字列。
        各インデックスはindex_name, columns, unique, type, definitionを含む。
    """
    return get_table_indexes_impl(table_name, schema)


@mcp.tool
def get_foreign_keys(table_name: str, schema: str = "public") -> str:
    """
    指定したテーブルの外部キー情報を取得します。

    Args:
        table_name: テーブル名
        schema: スキーマ名（デフォルト: "public"）

    Returns:
        外部キー情報のMarkdown Table形式の文字列。
        各外部キーはconstraint_name, column_name, foreign_table, foreign_columnを含む。
    """
    return get_foreign_keys_impl(table_name, schema)


@mcp.tool
def generate_er_diagram(
    schema: str = "public",
    tables: list[str] | None = None,
) -> str:
    """
    データベースのテーブル関係をMermaid形式のER図として生成します。

    Args:
        schema: スキーマ名（デフォルト: "public"）
        tables: 対象テーブルのリスト（省略時は全テーブル）

    Returns:
        Mermaid ER図形式の文字列。
        テーブル名、カラム名、型、主キー、コメント、外部キー関係を含む。
        Virtual Foreign Keys（命名規則から推測される外部キー）も含む。
    """
    return generate_er_diagram_impl(schema, tables)


def main() -> None:
    """MCPサーバーを起動"""
    mcp.run()


if __name__ == "__main__":
    main()
