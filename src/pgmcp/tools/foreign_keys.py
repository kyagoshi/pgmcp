"""
外部キー関連ツール

テーブルの外部キー情報の取得
"""

from typing import Any

from pgmcp.connection import get_connection


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


def get_foreign_keys_impl(table_name: str, schema: str = "public") -> str:
    """
    指定したテーブルの外部キー情報を取得します。

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
