"""
MCPツール群

各ツールはサブモジュールで定義され、server.pyでMCPサーバーに登録されます。
"""

from pgmcp.tools.foreign_keys import get_foreign_keys_impl
from pgmcp.tools.indexes import get_table_indexes_impl
from pgmcp.tools.schema import get_table_schema_impl, list_tables_impl

__all__ = [
    "list_tables_impl",
    "get_table_schema_impl",
    "get_table_indexes_impl",
    "get_foreign_keys_impl",
]
