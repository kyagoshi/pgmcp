# pgmcp

PostgreSQLデータベースのテーブル情報を取得するMCPサーバーです。

## 機能

- **list_tables**: 指定したスキーマのテーブル一覧を取得
- **get_table_schema**: 指定したテーブルのカラム情報（名前、型、NULL許可、デフォルト値、主キー）を取得

## 要件

- Python 3.10以上
- uv（パッケージ管理）
- PostgreSQLデータベースへのアクセス

## インストール

```bash
# リポジトリをクローン
git clone https://github.com/kyagoshi/pgmcp.git
cd pgmcp

# 依存関係をインストール
uv sync
```

## MCP設定

Claude DesktopなどのMCPクライアントで使用する場合、設定ファイルに以下を追加してください。

### Claude Desktop

`~/Library/Application Support/Claude/claude_desktop_config.json`（macOS）または`%APPDATA%\Claude\claude_desktop_config.json`（Windows）に以下を追加:

```json
{
  "mcpServers": {
    "pgmcp": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/pgmcp", "server.py"],
      "env": {
        "PGHOST": "localhost",
        "PGPORT": "5432",
        "PGDATABASE": "your_database",
        "PGUSER": "your_username",
        "PGPASSWORD": "your_password"
      }
    }
  }
}
```

### 環境変数

| 変数名 | 説明 | デフォルト値 |
|--------|------|-------------|
| `PGHOST` | PostgreSQLホスト名 | `localhost` |
| `PGPORT` | PostgreSQLポート番号 | `5432` |
| `PGDATABASE` | データベース名 | （必須） |
| `PGUSER` | ユーザー名 | （必須） |
| `PGPASSWORD` | パスワード | （必須） |

## 使用方法

### ツール: list_tables

指定したスキーマのテーブル一覧を取得します。

**パラメータ:**

- `schema` (string, optional): スキーマ名。デフォルトは `"public"`

**戻り値例:**

```text
| table_name | table_type |
|------------|------------|
| users | BASE TABLE |
| orders | BASE TABLE |
```

### ツール: get_table_schema

指定したテーブルのカラム情報を取得します。

**パラメータ:**

- `table_name` (string, required): テーブル名
- `schema` (string, optional): スキーマ名。デフォルトは `"public"`

**戻り値例:**

```text
| column_name | data_type | nullable | default | PK |
|-------------|-----------|----------|---------|-----|
| id | integer | NO | nextval('users_id_seq'::regclass) | ✓ |
| name | character varying(100) | NO | - |  |
| email | character varying(255) | YES | - |  |
```

## 開発

### 開発用依存関係のインストール

```bash
uv sync --extra dev
```

### テスト用データベースの起動

Docker Composeを使用してテスト用のPostgreSQLデータベースを起動できます。

```bash
# データベースを起動
docker compose up -d

# データベースを停止
docker compose down

# データベースを停止してボリュームも削除
docker compose down -v
```

テスト用データベースの接続情報:

| 項目 | 値 |
|------|-----|
| ホスト | localhost |
| ポート | 5433 |
| データベース | testdb |
| ユーザー | testuser |
| パスワード | testpass |

### テストの実行

```bash
# 全テストを実行
uv run pytest tests/ -v

# ユニットテストのみ（DB不要）
uv run pytest tests/test_server.py -v

# 統合テストのみ（要Docker）
uv run pytest tests/test_integration.py -v
```

### コード品質チェック

```bash
# リンター（ruff）
uv run ruff check .

# 自動修正
uv run ruff check --fix .

# フォーマッター（ruff format）
uv run ruff format .

# フォーマットチェックのみ
uv run ruff format --check .

# 型チェック（mypy）
uv run mypy server.py tests/

# 全チェックを一括実行
uv run ruff check . && uv run ruff format --check . && uv run mypy server.py tests/
```

### ローカルでのサーバー実行

```bash
# 環境変数を設定して実行
PGHOST=localhost PGPORT=5433 PGDATABASE=testdb PGUSER=testuser PGPASSWORD=testpass uv run server.py
```

### FastMCP開発サーバー

```bash
uv run fastmcp dev server.py
```
