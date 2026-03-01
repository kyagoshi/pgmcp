"""
サンプルデータ取得ツール

テーブルからサンプルデータを取得
"""

from typing import Any

from pgmcp.connection import get_connection


def _format_sample_data(rows: list[tuple[Any, ...]], columns: list[str]) -> str:
    """サンプルデータをMarkdown Table形式にフォーマット"""
    if not rows:
        return "データが見つかりませんでした。"

    # ヘッダー行を作成
    header = "| " + " | ".join(columns) + " |"
    separator = "|" + "|".join(["-" * (len(col) + 2) for col in columns]) + "|"

    lines = [header, separator]

    # データ行を作成
    for row in rows:
        # NULL値を "-" で表示、その他の値は文字列に変換
        formatted_values = [str(val) if val is not None else "-" for val in row]
        line = "| " + " | ".join(formatted_values) + " |"
        lines.append(line)

    return "\n".join(lines)


def get_sample_data_impl(
    table_name: str, schema: str = "public", limit: int = 5
) -> str:
    """
    指定したテーブルからサンプルデータを取得します。

    Args:
        table_name: テーブル名
        schema: スキーマ名（デフォルト: "public"）
        limit: 取得する行数（デフォルト: 5、最大: 100）

    Returns:
        サンプルデータのMarkdown Table形式の文字列。
    """
    # limitの範囲を制限（セキュリティ対策）
    if limit < 1:
        limit = 1
    elif limit > 100:
        limit = 100

    # カラム名を取得するクエリ
    column_query = """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = %s
          AND table_name = %s
        ORDER BY ordinal_position
    """

    with get_connection() as conn, conn.cursor() as cur:
        # カラム名を取得
        cur.execute(column_query, (schema, table_name))
        column_rows = cur.fetchall()

        if not column_rows:
            return "テーブルが見つかりませんでした。"

        columns = [row[0] for row in column_rows]

        # サンプルデータを取得
        # SQL injectionを防ぐため、テーブル名とスキーマ名は識別子として適切にエスケープ
        from psycopg2 import sql

        data_query = sql.SQL("SELECT * FROM {}.{} LIMIT %s").format(
            sql.Identifier(schema), sql.Identifier(table_name)
        )

        cur.execute(data_query, (limit,))
        rows = cur.fetchall()

    return _format_sample_data(rows, columns)
