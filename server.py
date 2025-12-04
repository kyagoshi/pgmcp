"""
pgmcp - PostgreSQL MCP Server

PostgreSQLデータベースのテーブル一覧とスキーマ情報を提供するMCPサーバー
"""

import os
from typing import Any

import psycopg2
from fastmcp import FastMCP

# MCPサーバーインスタンスを作成
mcp = FastMCP("pgmcp")


def get_connection():
    """環境変数からPostgreSQL接続を作成"""
    return psycopg2.connect(
        host=os.environ.get("PGHOST", "localhost"),
        port=os.environ.get("PGPORT", "5432"),
        database=os.environ.get("PGDATABASE"),
        user=os.environ.get("PGUSER"),
        password=os.environ.get("PGPASSWORD"),
    )


def _format_table_list(rows: list[tuple[Any, ...]]) -> str:
    """テーブル一覧をMarkdown Table形式にフォーマット"""
    if not rows:
        return "テーブルが見つかりませんでした。"

    lines = [
        "| table_name | table_type |",
        "|------------|------------|",
    ]
    for row in rows:
        table_name, table_type = row
        lines.append(f"| {table_name} | {table_type} |")

    return "\n".join(lines)


def _format_table_schema(rows: list[tuple[Any, ...]]) -> str:
    """テーブルスキーマをMarkdown Table形式にフォーマット"""
    if not rows:
        return "テーブルが見つかりませんでした。"

    lines = [
        "| column_name | data_type | nullable | default | PK |",
        "|-------------|-----------|----------|---------|-----|",
    ]
    for row in rows:
        column_name, data_type, is_nullable, column_default, is_primary_key = row
        nullable = "YES" if is_nullable == "YES" else "NO"
        default = column_default if column_default else "-"
        pk = "✓" if is_primary_key else ""
        lines.append(f"| {column_name} | {data_type} | {nullable} | {default} | {pk} |")

    return "\n".join(lines)


def _list_tables_impl(schema: str = "public") -> str:
    """
    指定したスキーマのテーブル一覧を取得します（内部実装）。

    Args:
        schema: スキーマ名（デフォルト: "public"）

    Returns:
        テーブル情報のMarkdown Table形式の文字列。
    """
    query = """
        SELECT 
            table_name,
            table_type
        FROM information_schema.tables
        WHERE table_schema = %s
        ORDER BY table_name
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (schema,))
            rows = cur.fetchall()

    return _format_table_list(rows)


def _get_table_schema_impl(
    table_name: str, schema: str = "public"
) -> str:
    """
    指定したテーブルのカラム情報を取得します（内部実装）。

    Args:
        table_name: テーブル名
        schema: スキーマ名（デフォルト: "public"）

    Returns:
        カラム情報のMarkdown Table形式の文字列。
    """
    query = """
        SELECT 
            a.attname AS column_name,
            pg_catalog.format_type(a.atttypid, a.atttypmod) AS data_type,
            CASE WHEN a.attnotnull THEN 'NO' ELSE 'YES' END AS is_nullable,
            pg_catalog.pg_get_expr(d.adbin, d.adrelid) AS column_default,
            COALESCE(
                (SELECT TRUE 
                 FROM pg_catalog.pg_constraint con
                 WHERE con.conrelid = a.attrelid 
                   AND a.attnum = ANY(con.conkey)
                   AND con.contype = 'p'),
                FALSE
            ) AS is_primary_key
        FROM pg_catalog.pg_attribute a
        JOIN pg_catalog.pg_class c ON c.oid = a.attrelid
        JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
        LEFT JOIN pg_catalog.pg_attrdef d ON d.adrelid = a.attrelid AND d.adnum = a.attnum
        WHERE c.relname = %s
          AND n.nspname = %s
          AND a.attnum > 0
          AND NOT a.attisdropped
        ORDER BY a.attnum
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (table_name, schema))
            rows = cur.fetchall()

    return _format_table_schema(rows)


@mcp.tool
def list_tables(schema: str = "public") -> str:
    """
    指定したスキーマのテーブル一覧を取得します。

    Args:
        schema: スキーマ名（デフォルト: "public"）

    Returns:
        テーブル情報のMarkdown Table形式の文字列。
    """
    return _list_tables_impl(schema)


@mcp.tool
def get_table_schema(table_name: str, schema: str = "public") -> str:
    """
    指定したテーブルのカラム情報を取得します。

    Args:
        table_name: テーブル名
        schema: スキーマ名（デフォルト: "public"）

    Returns:
        カラム情報のMarkdown Table形式の文字列。
        各カラムはcolumn_name, data_type, nullable, default, PKを含む。
    """
    return _get_table_schema_impl(table_name, schema)


def main():
    """MCPサーバーを起動"""
    mcp.run()


if __name__ == "__main__":
    main()
