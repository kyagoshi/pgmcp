"""
ER図生成ツールのユニットテスト
"""

from unittest.mock import MagicMock, patch

from pgmcp.tools.er_diagram import (
    _detect_virtual_foreign_keys,
    _format_mermaid_er_diagram,
    _simplify_data_type,
    generate_er_diagram_impl,
)


class TestSimplifyDataType:
    """_simplify_data_type のテスト"""

    def test_simplify_integer(self) -> None:
        """integer型の変換"""
        assert _simplify_data_type("integer") == "integer"

    def test_simplify_varchar_with_length(self) -> None:
        """character varying(n)型の変換"""
        assert _simplify_data_type("character varying(100)") == "varchar"

    def test_simplify_timestamp_with_timezone(self) -> None:
        """timestamp with time zone型の変換"""
        assert _simplify_data_type("timestamp with time zone") == "timestamptz"

    def test_simplify_numeric_with_precision(self) -> None:
        """numeric(p,s)型の変換"""
        assert _simplify_data_type("numeric(10,2)") == "numeric"

    def test_simplify_integer_array(self) -> None:
        """integer[]型の変換"""
        assert _simplify_data_type("integer[]") == "integer_array"

    def test_simplify_text_array(self) -> None:
        """text[]型の変換"""
        assert _simplify_data_type("text[]") == "text_array"

    def test_simplify_unknown_type(self) -> None:
        """未知の型の変換"""
        assert _simplify_data_type("custom_type") == "custom_type"


class TestDetectVirtualForeignKeys:
    """_detect_virtual_foreign_keys のテスト"""

    def test_detect_simple_virtual_fk(self) -> None:
        """単純な _id パターンの検出"""
        tables_info = [
            {
                "table_name": "users",
                "columns": [
                    {
                        "column_name": "id",
                        "is_primary_key": True,
                        "is_foreign_key": False,
                    },
                    {
                        "column_name": "name",
                        "is_primary_key": False,
                        "is_foreign_key": False,
                    },
                ],
            },
            {
                "table_name": "orders",
                "columns": [
                    {
                        "column_name": "id",
                        "is_primary_key": True,
                        "is_foreign_key": False,
                    },
                    {
                        "column_name": "user_id",
                        "is_primary_key": False,
                        "is_foreign_key": False,
                    },
                ],
            },
        ]

        virtual_fks = _detect_virtual_foreign_keys(tables_info, "public", None)

        assert len(virtual_fks) == 1
        assert virtual_fks[0]["from_table"] == "orders"
        assert virtual_fks[0]["from_column"] == "user_id"
        assert virtual_fks[0]["to_table"] == "users"
        assert virtual_fks[0]["to_column"] == "id"

    def test_skip_existing_foreign_key(self) -> None:
        """既存の外部キーはスキップされる"""
        tables_info = [
            {
                "table_name": "users",
                "columns": [
                    {
                        "column_name": "id",
                        "is_primary_key": True,
                        "is_foreign_key": False,
                    },
                ],
            },
            {
                "table_name": "orders",
                "columns": [
                    {
                        "column_name": "id",
                        "is_primary_key": True,
                        "is_foreign_key": False,
                    },
                    # 既にFKとして定義されている
                    {
                        "column_name": "user_id",
                        "is_primary_key": False,
                        "is_foreign_key": True,
                    },
                ],
            },
        ]

        virtual_fks = _detect_virtual_foreign_keys(tables_info, "public", None)

        assert len(virtual_fks) == 0

    def test_detect_plural_table_name(self) -> None:
        """複数形テーブル名の検出 (category -> categories)"""
        tables_info = [
            {
                "table_name": "categories",
                "columns": [
                    {
                        "column_name": "id",
                        "is_primary_key": True,
                        "is_foreign_key": False,
                    },
                ],
            },
            {
                "table_name": "products",
                "columns": [
                    {
                        "column_name": "id",
                        "is_primary_key": True,
                        "is_foreign_key": False,
                    },
                    {
                        "column_name": "category_id",
                        "is_primary_key": False,
                        "is_foreign_key": False,
                    },
                ],
            },
        ]

        virtual_fks = _detect_virtual_foreign_keys(tables_info, "public", None)

        assert len(virtual_fks) == 1
        assert virtual_fks[0]["to_table"] == "categories"

    def test_no_match_for_unknown_table(self) -> None:
        """存在しないテーブルへの参照は検出しない"""
        tables_info = [
            {
                "table_name": "orders",
                "columns": [
                    {
                        "column_name": "id",
                        "is_primary_key": True,
                        "is_foreign_key": False,
                    },
                    {
                        "column_name": "unknown_id",
                        "is_primary_key": False,
                        "is_foreign_key": False,
                    },
                ],
            },
        ]

        virtual_fks = _detect_virtual_foreign_keys(tables_info, "public", None)

        assert len(virtual_fks) == 0

    def test_detect_no_suffix_pattern(self) -> None:
        """_no サフィックスパターンの検出"""
        tables_info = [
            {
                "table_name": "orders",
                "columns": [
                    {
                        "column_name": "order_no",
                        "is_primary_key": True,
                        "is_foreign_key": False,
                    },
                ],
            },
            {
                "table_name": "order_items",
                "columns": [
                    {
                        "column_name": "id",
                        "is_primary_key": True,
                        "is_foreign_key": False,
                    },
                    {
                        "column_name": "order_no",
                        "is_primary_key": False,
                        "is_foreign_key": False,
                    },
                ],
            },
        ]

        virtual_fks = _detect_virtual_foreign_keys(tables_info, "public", None)

        assert len(virtual_fks) == 1
        assert virtual_fks[0]["from_table"] == "order_items"
        assert virtual_fks[0]["from_column"] == "order_no"
        assert virtual_fks[0]["to_table"] == "orders"
        assert virtual_fks[0]["to_column"] == "order_no"

    def test_detect_same_pk_column_name(self) -> None:
        """他のテーブルのPKと同名のカラムを検出"""
        tables_info = [
            {
                "table_name": "users",
                "columns": [
                    {
                        "column_name": "user_code",
                        "is_primary_key": True,
                        "is_foreign_key": False,
                    },
                    {
                        "column_name": "name",
                        "is_primary_key": False,
                        "is_foreign_key": False,
                    },
                ],
            },
            {
                "table_name": "orders",
                "columns": [
                    {
                        "column_name": "id",
                        "is_primary_key": True,
                        "is_foreign_key": False,
                    },
                    {
                        "column_name": "user_code",
                        "is_primary_key": False,
                        "is_foreign_key": False,
                    },
                ],
            },
        ]

        virtual_fks = _detect_virtual_foreign_keys(tables_info, "public", None)

        assert len(virtual_fks) == 1
        assert virtual_fks[0]["from_table"] == "orders"
        assert virtual_fks[0]["from_column"] == "user_code"
        assert virtual_fks[0]["to_table"] == "users"
        assert virtual_fks[0]["to_column"] == "user_code"


class TestFormatMermaidErDiagram:
    """_format_mermaid_er_diagram のテスト"""

    def test_format_single_table(self) -> None:
        """単一テーブルのフォーマット"""
        tables_info = [
            {
                "table_name": "users",
                "columns": [
                    {
                        "column_name": "id",
                        "data_type": "integer",
                        "is_primary_key": True,
                        "is_foreign_key": False,
                        "comment": "ユーザーID",
                    },
                    {
                        "column_name": "name",
                        "data_type": "character varying(100)",
                        "is_primary_key": False,
                        "is_foreign_key": False,
                        "comment": None,
                    },
                ],
            },
        ]

        result = _format_mermaid_er_diagram(tables_info, [], [])

        assert "erDiagram" in result
        assert "users {" in result
        assert "integer id PK" in result
        assert '"ユーザーID"' in result
        assert "varchar name" in result

    def test_format_with_foreign_key_relation(self) -> None:
        """外部キー関係のフォーマット"""
        tables_info = [
            {
                "table_name": "users",
                "columns": [
                    {
                        "column_name": "id",
                        "data_type": "integer",
                        "is_primary_key": True,
                        "is_foreign_key": False,
                        "comment": None,
                    },
                ],
            },
            {
                "table_name": "orders",
                "columns": [
                    {
                        "column_name": "id",
                        "data_type": "integer",
                        "is_primary_key": True,
                        "is_foreign_key": False,
                        "comment": None,
                    },
                    {
                        "column_name": "user_id",
                        "data_type": "integer",
                        "is_primary_key": False,
                        "is_foreign_key": True,
                        "comment": None,
                    },
                ],
            },
        ]
        relations = [
            {
                "from_table": "orders",
                "from_column": "user_id",
                "to_table": "users",
                "to_column": "id",
            },
        ]

        result = _format_mermaid_er_diagram(tables_info, relations, [])

        assert 'users ||--o{ orders : "has"' in result

    def test_format_with_virtual_foreign_key(self) -> None:
        """Virtual Foreign Keyのフォーマット（点線）"""
        tables_info = [
            {
                "table_name": "users",
                "columns": [
                    {
                        "column_name": "id",
                        "data_type": "integer",
                        "is_primary_key": True,
                        "is_foreign_key": False,
                        "comment": None,
                    },
                ],
            },
            {
                "table_name": "logs",
                "columns": [
                    {
                        "column_name": "id",
                        "data_type": "integer",
                        "is_primary_key": True,
                        "is_foreign_key": False,
                        "comment": None,
                    },
                    {
                        "column_name": "user_id",
                        "data_type": "integer",
                        "is_primary_key": False,
                        "is_foreign_key": False,
                        "comment": None,
                    },
                ],
            },
        ]
        virtual_fks = [
            {
                "from_table": "logs",
                "from_column": "user_id",
                "to_table": "users",
                "to_column": "id",
            },
        ]

        result = _format_mermaid_er_diagram(tables_info, [], virtual_fks)

        assert 'users ||..o{ logs : "references"' in result
        assert "integer user_id FK" in result

    def test_format_empty_tables(self) -> None:
        """テーブルが空の場合"""
        result = _format_mermaid_er_diagram([], [], [])

        assert result == "対象のテーブルが見つかりませんでした。"


class TestGenerateErDiagramImpl:
    """generate_er_diagram_impl のテスト"""

    @patch("pgmcp.tools.er_diagram.get_connection")
    def test_generate_er_diagram_basic(self, mock_get_connection: MagicMock) -> None:
        """基本的なER図生成"""
        # テーブル情報用のモックカーソル
        mock_cursor = MagicMock()
        mock_cursor.fetchall.side_effect = [
            # _get_tables_info のクエリ結果
            [
                ("users", "id", "integer", True, False, "ユーザーID"),
                ("users", "name", "character varying(100)", False, False, None),
                ("orders", "id", "integer", True, False, None),
                ("orders", "user_id", "integer", False, True, None),
            ],
            # _get_foreign_key_relations のクエリ結果
            [
                ("orders", "user_id", "users", "id"),
            ],
        ]

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_connection.return_value = mock_conn

        result = generate_er_diagram_impl()

        assert "erDiagram" in result
        assert "users {" in result
        assert "orders {" in result
        assert 'users ||--o{ orders : "has"' in result

    @patch("pgmcp.tools.er_diagram.get_connection")
    def test_generate_er_diagram_with_table_filter(
        self, mock_get_connection: MagicMock
    ) -> None:
        """テーブルフィルターを指定したER図生成"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.side_effect = [
            # _get_tables_info のクエリ結果
            [
                ("users", "id", "integer", True, False, None),
                ("users", "name", "character varying(100)", False, False, None),
                ("orders", "id", "integer", True, False, None),
                ("products", "id", "integer", True, False, None),
            ],
            # _get_foreign_key_relations のクエリ結果
            [],
        ]

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_connection.return_value = mock_conn

        result = generate_er_diagram_impl(tables=["users", "orders"])

        assert "users {" in result
        assert "orders {" in result
        assert "products {" not in result

    @patch("pgmcp.tools.er_diagram.get_connection")
    def test_generate_er_diagram_warning_for_many_tables(
        self, mock_get_connection: MagicMock
    ) -> None:
        """テーブルが多い場合の警告（100超）"""
        # 101個のテーブルを生成
        tables_data = []
        for i in range(101):
            tables_data.append((f"table_{i}", "id", "integer", True, False, None))

        mock_cursor = MagicMock()
        mock_cursor.fetchall.side_effect = [
            tables_data,
            [],  # 外部キー関係なし
        ]

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_connection.return_value = mock_conn

        result = generate_er_diagram_impl()

        assert "⚠️ 警告:" in result
        assert "101個のテーブル" in result

    @patch("pgmcp.tools.er_diagram.get_connection")
    def test_generate_er_diagram_no_warning_for_100_tables(
        self, mock_get_connection: MagicMock
    ) -> None:
        """100テーブル以下では警告なし"""
        # 100個のテーブルを生成
        tables_data = []
        for i in range(100):
            tables_data.append((f"table_{i}", "id", "integer", True, False, None))

        mock_cursor = MagicMock()
        mock_cursor.fetchall.side_effect = [
            tables_data,
            [],  # 外部キー関係なし
        ]

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_connection.return_value = mock_conn

        result = generate_er_diagram_impl()

        assert "⚠️ 警告:" not in result

    @patch("pgmcp.tools.er_diagram.get_connection")
    def test_generate_er_diagram_no_tables(
        self, mock_get_connection: MagicMock
    ) -> None:
        """テーブルが存在しない場合"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.side_effect = [
            [],  # テーブルなし
            [],  # 外部キー関係なし
        ]

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_connection.return_value = mock_conn

        result = generate_er_diagram_impl()

        assert result == "対象のテーブルが見つかりませんでした。"
