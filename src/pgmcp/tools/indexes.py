"""
インデックス関連ツール

テーブルのインデックス情報の取得
"""

from typing import Any

from pgmcp.connection import get_connection


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


def get_table_indexes_impl(table_name: str, schema: str = "public") -> str:
    """
    指定したテーブルのインデックス情報を取得します。

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
