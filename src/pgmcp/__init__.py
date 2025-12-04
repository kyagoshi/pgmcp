"""
pgmcp - PostgreSQL MCP Server

PostgreSQLデータベースのテーブル一覧とスキーマ情報を提供するMCPサーバー
"""

from pgmcp.server import main, mcp

__version__ = "0.1.0"
__all__ = ["main", "mcp"]
