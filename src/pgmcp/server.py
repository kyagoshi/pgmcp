"""
pgmcp - PostgreSQL MCP Server

PostgreSQLデータベースのテーブル一覧とスキーマ情報を提供するMCPサーバー
"""

import os
from typing import Any

import psycopg2
from fastmcp import FastMCP
from psycopg2.extensions import connection

# MCPサーバーインスタンスを作成
mcp = FastMCP("pgmcp")


def get_connection() -> connection:
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


def _format_table_indexes(rows: list[tuple[Any, ...]]) -> str:
    """インデックス一覧をMarkdown Table形式にフォーマット"""
    if not rows:
        return "インデックスが見つかりませんでした。"

    lines = [
        "| index_name | columns | unique | type | definition |",
        "|------------|---------|--------|------|------------|",
    ]
    for row in rows:
        index_name, columns, is_unique, index_type, definition = row
        unique = "✓" if is_unique else ""
        lines.append(
            f"| {index_name} | {columns} | {unique} | {index_type} | {definition} |"
        )

    return "\n".join(lines)


def _format_foreign_keys(rows: list[tuple[Any, ...]]) -> str:
    """外部キー一覧をMarkdown Table形式にフォーマット"""
    if not rows:
        return "外部キーが見つかりませんでした。"

    lines = [
        "| constraint_name | column_name | foreign_table | foreign_column |",
        "|-----------------|-------------|---------------|----------------|",
    ]
    for row in rows:
        constraint_name, column_name, foreign_table, foreign_column = row
        lines.append(
            f"| {constraint_name} | {column_name} | {foreign_table} | {foreign_column} |"
        )

    return "\n".join(lines)


def _format_table_schema(rows: list[tuple[Any, ...]]) -> str:
    """テーブルスキーマをMarkdown Table形式にフォーマット"""
    if not rows:
        return "テーブルが見つかりませんでした。"

    lines = [
        "| column_name | data_type | nullable | default | PK | comment |",
        "|-------------|-----------|----------|---------|-----|---------|",
    ]
    for row in rows:
        column_name, data_type, is_nullable, column_default, is_primary_key, comment = (
            row
        )
        nullable = "YES" if is_nullable == "YES" else "NO"
        default = column_default if column_default else "-"
        pk = "✓" if is_primary_key else ""
        comment_str = comment if comment else ""
        lines.append(
            f"| {column_name} | {data_type} | {nullable} | {default} | {pk} | {comment_str} |"
        )

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

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(query, (schema,))
        rows = cur.fetchall()

    return _format_table_list(rows)


def _get_table_schema_impl(table_name: str, schema: str = "public") -> str:
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
            ) AS is_primary_key,
            pg_catalog.col_description(a.attrelid, a.attnum) AS column_comment
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

    with get_connection() as conn, conn.cursor() as cur:
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
        各カラムはcolumn_name, data_type, nullable, default, PK, commentを含む。
    """
    return _get_table_schema_impl(table_name, schema)


def _get_table_indexes_impl(table_name: str, schema: str = "public") -> str:
    """
    指定したテーブルのインデックス情報を取得します（内部実装）。

    Args:
        table_name: テーブル名
        schema: スキーマ名（デフォルト: "public"）

    Returns:
        インデックス情報のMarkdown Table形式の文字列。
    """
    query = """
        SELECT
            i.relname AS index_name,
            array_to_string(
                ARRAY(
                    SELECT pg_catalog.pg_get_indexdef(ix.indexrelid, k + 1, true)
                    FROM generate_subscripts(ix.indkey, 1) AS k
                    ORDER BY k
                ),
                ', '
            ) AS columns,
            ix.indisunique AS is_unique,
            am.amname AS index_type,
            pg_catalog.pg_get_indexdef(ix.indexrelid) AS definition
        FROM pg_catalog.pg_index ix
        JOIN pg_catalog.pg_class i ON i.oid = ix.indexrelid
        JOIN pg_catalog.pg_class t ON t.oid = ix.indrelid
        JOIN pg_catalog.pg_namespace n ON n.oid = t.relnamespace
        JOIN pg_catalog.pg_am am ON am.oid = i.relam
        WHERE t.relname = %s
          AND n.nspname = %s
        ORDER BY i.relname
    """

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(query, (table_name, schema))
        rows = cur.fetchall()

    return _format_table_indexes(rows)


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
    return _get_table_indexes_impl(table_name, schema)


def _get_foreign_keys_impl(table_name: str, schema: str = "public") -> str:
    """
    指定したテーブルの外部キー情報を取得します（内部実装）。

    Args:
        table_name: テーブル名
        schema: スキーマ名（デフォルト: "public"）

    Returns:
        外部キー情報のMarkdown Table形式の文字列。
    """
    query = """
        SELECT
            con.conname AS constraint_name,
            a.attname AS column_name,
            ref_class.relname AS foreign_table,
            ref_attr.attname AS foreign_column
        FROM pg_catalog.pg_constraint con
        JOIN pg_catalog.pg_class cls ON cls.oid = con.conrelid
        JOIN pg_catalog.pg_namespace nsp ON nsp.oid = cls.relnamespace
        JOIN pg_catalog.pg_attribute a ON a.attrelid = con.conrelid
            AND a.attnum = ANY(con.conkey)
        JOIN pg_catalog.pg_class ref_class ON ref_class.oid = con.confrelid
        JOIN pg_catalog.pg_attribute ref_attr ON ref_attr.attrelid = con.confrelid
            AND ref_attr.attnum = ANY(con.confkey)
            AND array_position(con.conkey, a.attnum) = array_position(con.confkey, ref_attr.attnum)
        WHERE con.contype = 'f'
          AND cls.relname = %s
          AND nsp.nspname = %s
        ORDER BY con.conname, a.attnum
    """

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(query, (table_name, schema))
        rows = cur.fetchall()

    return _format_foreign_keys(rows)


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
    return _get_foreign_keys_impl(table_name, schema)


def main() -> None:
    """MCPサーバーを起動"""
    mcp.run()


if __name__ == "__main__":
    main()
