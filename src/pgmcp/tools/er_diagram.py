"""
ER図生成ツール

データベースのテーブル関係をMermaid形式のER図として出力
"""

from typing import Any

from pgmcp.connection import get_connection


def _get_tables_info(
    schema: str, tables: list[str] | None = None
) -> list[dict[str, Any]]:
    """
    テーブルのカラム情報を取得

    Args:
        schema: スキーマ名
        tables: 対象テーブルのリスト（Noneの場合は全テーブル）

    Returns:
        テーブル情報のリスト
    """
    query = """
        SELECT
            c.relname AS table_name,
            a.attname AS column_name,
            pg_catalog.format_type(a.atttypid, a.atttypmod) AS data_type,
            COALESCE(
                (SELECT TRUE
                 FROM pg_catalog.pg_constraint con
                 WHERE con.conrelid = a.attrelid
                   AND a.attnum = ANY(con.conkey)
                   AND con.contype = 'p'),
                FALSE
            ) AS is_primary_key,
            COALESCE(
                (SELECT TRUE
                 FROM pg_catalog.pg_constraint con
                 WHERE con.conrelid = a.attrelid
                   AND a.attnum = ANY(con.conkey)
                   AND con.contype = 'f'),
                FALSE
            ) AS is_foreign_key,
            pg_catalog.col_description(a.attrelid, a.attnum) AS column_comment
        FROM pg_catalog.pg_attribute a
        JOIN pg_catalog.pg_class c ON c.oid = a.attrelid
        JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = %s
          AND c.relkind = 'r'
          AND a.attnum > 0
          AND NOT a.attisdropped
        ORDER BY c.relname, a.attnum
    """

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(query, (schema,))
        rows = cur.fetchall()

    # テーブルごとにグループ化
    tables_dict: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        table_name, column_name, data_type, is_pk, is_fk, comment = row
        if tables is not None and table_name not in tables:
            continue
        if table_name not in tables_dict:
            tables_dict[table_name] = []
        tables_dict[table_name].append(
            {
                "column_name": column_name,
                "data_type": data_type,
                "is_primary_key": is_pk,
                "is_foreign_key": is_fk,
                "comment": comment,
            }
        )

    return [
        {"table_name": name, "columns": columns}
        for name, columns in tables_dict.items()
    ]


def _get_foreign_key_relations(
    schema: str, tables: list[str] | None = None
) -> list[dict[str, str]]:
    """
    外部キー関係を取得

    Args:
        schema: スキーマ名
        tables: 対象テーブルのリスト（Noneの場合は全テーブル）

    Returns:
        外部キー関係のリスト
    """
    query = """
        SELECT DISTINCT
            cls.relname AS from_table,
            a.attname AS from_column,
            ref_class.relname AS to_table,
            ref_attr.attname AS to_column
        FROM pg_catalog.pg_constraint con
        JOIN pg_catalog.pg_class cls ON cls.oid = con.conrelid
        JOIN pg_catalog.pg_namespace nsp ON nsp.oid = cls.relnamespace
        JOIN pg_catalog.pg_attribute a ON a.attrelid = con.conrelid
            AND a.attnum = ANY(con.conkey)
        JOIN pg_catalog.pg_class ref_class ON ref_class.oid = con.confrelid
        JOIN pg_catalog.pg_namespace ref_nsp ON ref_nsp.oid = ref_class.relnamespace
        JOIN pg_catalog.pg_attribute ref_attr ON ref_attr.attrelid = con.confrelid
            AND ref_attr.attnum = ANY(con.confkey)
            AND array_position(con.conkey, a.attnum) = array_position(con.confkey, ref_attr.attnum)
        WHERE con.contype = 'f'
          AND nsp.nspname = %s
          AND ref_nsp.nspname = %s
        ORDER BY cls.relname, ref_class.relname
    """

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(query, (schema, schema))
        rows = cur.fetchall()

    relations = []
    for row in rows:
        from_table, from_column, to_table, to_column = row
        # tablesが指定されている場合、両方のテーブルがリストに含まれている必要がある
        if tables is not None and (from_table not in tables or to_table not in tables):
            continue
        relations.append(
            {
                "from_table": from_table,
                "from_column": from_column,
                "to_table": to_table,
                "to_column": to_column,
            }
        )

    return relations


def _detect_virtual_foreign_keys(
    tables_info: list[dict[str, Any]], schema: str, tables: list[str] | None = None
) -> list[dict[str, str]]:
    """
    Virtual Foreign Keys（命名規則から推測される外部キー）を検出

    Args:
        tables_info: テーブル情報のリスト
        schema: スキーマ名
        tables: 対象テーブルのリスト

    Returns:
        推測される外部キー関係のリスト
    """
    # テーブル名のセットを作成
    table_names = {t["table_name"] for t in tables_info}

    # 各テーブルのPKカラム名を収集
    pk_columns: dict[str, set[str]] = {}
    for table in tables_info:
        pk_columns[table["table_name"]] = {
            col["column_name"] for col in table["columns"] if col["is_primary_key"]
        }

    # 既存の外部キーカラムを収集
    fk_columns: set[tuple[str, str]] = set()
    for table in tables_info:
        for col in table["columns"]:
            if col["is_foreign_key"]:
                fk_columns.add((table["table_name"], col["column_name"]))

    virtual_fks = []
    for table in tables_info:
        for col in table["columns"]:
            column_name = col["column_name"]
            # 既に外部キーとして定義されている場合はスキップ
            if (table["table_name"], column_name) in fk_columns:
                continue
            # 自分自身がPKの場合はスキップ（PKは他テーブルへの参照ではない）
            if col["is_primary_key"]:
                continue

            matched_table = None
            matched_column = None

            # パターン1: _id または _no で終わるカラムをチェック
            for suffix in ("_id", "_no"):
                if column_name.endswith(suffix):
                    # 推測されるテーブル名
                    potential_table = column_name[: -len(suffix)]
                    # 複数形も試す
                    potential_tables = [
                        potential_table,
                        potential_table + "s",
                        potential_table + "es",
                    ]
                    # 特殊なパターン: category -> categories
                    if potential_table.endswith("y"):
                        potential_tables.append(potential_table[:-1] + "ies")

                    for pt in potential_tables:
                        if pt in table_names and pt != table["table_name"]:
                            matched_table = pt
                            # 参照先のPKを探す（idまたはnoを優先）
                            ref_pk = pk_columns.get(pt, set())
                            if "id" in ref_pk:
                                matched_column = "id"
                            elif "no" in ref_pk:
                                matched_column = "no"
                            elif ref_pk:
                                matched_column = next(iter(ref_pk))
                            else:
                                matched_column = "id"  # デフォルト
                            break
                    if matched_table:
                        break

            # パターン2: 他のテーブルのPKと同名のカラム（_id, _no サフィックスなし）
            if not matched_table:
                for other_table in tables_info:
                    if other_table["table_name"] == table["table_name"]:
                        continue
                    other_pk = pk_columns.get(other_table["table_name"], set())
                    if column_name in other_pk:
                        matched_table = other_table["table_name"]
                        matched_column = column_name
                        break

            if matched_table and matched_column:
                virtual_fks.append(
                    {
                        "from_table": table["table_name"],
                        "from_column": column_name,
                        "to_table": matched_table,
                        "to_column": matched_column,
                    }
                )

    return virtual_fks


def _simplify_data_type(data_type: str) -> str:
    """
    データ型を簡略化してMermaid ER図用に変換

    Args:
        data_type: PostgreSQLのデータ型

    Returns:
        簡略化されたデータ型
    """
    # 括弧内の詳細情報を除去し、基本型名のみを取得
    type_map = {
        "integer": "integer",
        "bigint": "bigint",
        "smallint": "smallint",
        "serial": "serial",
        "bigserial": "bigserial",
        "character varying": "varchar",
        "character": "char",
        "text": "text",
        "boolean": "boolean",
        "timestamp with time zone": "timestamptz",
        "timestamp without time zone": "timestamp",
        "date": "date",
        "time with time zone": "timetz",
        "time without time zone": "time",
        "numeric": "numeric",
        "decimal": "decimal",
        "real": "real",
        "double precision": "double",
        "uuid": "uuid",
        "json": "json",
        "jsonb": "jsonb",
        "bytea": "bytea",
        "interval": "interval",
    }

    # 配列型の処理
    if data_type.endswith("[]"):
        base_type = data_type[:-2]
        simplified = _simplify_data_type(base_type)
        return f"{simplified}_array"

    # 括弧前の型名を抽出
    base_type = data_type.split("(")[0].strip()

    return type_map.get(base_type, base_type.replace(" ", "_"))


def _format_mermaid_er_diagram(
    tables_info: list[dict[str, Any]],
    relations: list[dict[str, str]],
    virtual_fks: list[dict[str, str]],
) -> str:
    """
    Mermaid ER図形式にフォーマット

    Args:
        tables_info: テーブル情報のリスト
        relations: 外部キー関係のリスト
        virtual_fks: 推測される外部キー関係のリスト

    Returns:
        Mermaid ER図形式の文字列
    """
    if not tables_info:
        return "対象のテーブルが見つかりませんでした。"

    lines = ["erDiagram"]

    # Virtual FK対象カラムを特定（FKマーカー付与用）
    virtual_fk_columns = {
        (vfk["from_table"], vfk["from_column"]) for vfk in virtual_fks
    }

    # テーブル定義を出力
    for table in sorted(tables_info, key=lambda t: t["table_name"]):
        table_name = table["table_name"]
        lines.append(f"    {table_name} {{")
        for col in table["columns"]:
            simplified_type = _simplify_data_type(col["data_type"])
            markers = []
            if col["is_primary_key"]:
                markers.append("PK")
            if (
                col["is_foreign_key"]
                or (table_name, col["column_name"]) in virtual_fk_columns
            ):
                markers.append("FK")
            marker_str = " " + ",".join(markers) if markers else ""
            comment = f' "{col["comment"]}"' if col["comment"] else ""
            lines.append(
                f"        {simplified_type} {col['column_name']}{marker_str}{comment}"
            )
        lines.append("    }")

    # 関係を出力（実際の外部キー）
    for rel in relations:
        # 多対1の関係を表現: from_table は to_table の1つのレコードを参照
        lines.append(f'    {rel["to_table"]} ||--o{{ {rel["from_table"]} : "has"')

    # Virtual Foreign Keysを出力（破線スタイルはMermaidでは対応していないのでコメントで区別）
    for vfk in virtual_fks:
        # 重複チェック
        is_duplicate = any(
            r["from_table"] == vfk["from_table"]
            and r["to_table"] == vfk["to_table"]
            and r["from_column"] == vfk["from_column"]
            for r in relations
        )
        if not is_duplicate:
            lines.append(
                f'    {vfk["to_table"]} ||..o{{ {vfk["from_table"]} : "references"'
            )

    return "\n".join(lines)


def generate_er_diagram_impl(
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
    """
    # テーブル情報を取得
    tables_info = _get_tables_info(schema, tables)

    # テーブル数が多い場合の警告
    warning = ""
    if len(tables_info) > 100 and tables is None:
        warning = (
            f"⚠️ 警告: {len(tables_info)}個のテーブルが見つかりました。"
            "tables パラメータで対象を絞り込むことをお勧めします。\n\n"
        )

    # 外部キー関係を取得
    relations = _get_foreign_key_relations(schema, tables)

    # Virtual Foreign Keysを検出
    virtual_fks = _detect_virtual_foreign_keys(tables_info, schema, tables)

    # Mermaid形式にフォーマット
    diagram = _format_mermaid_er_diagram(tables_info, relations, virtual_fks)

    return warning + diagram
