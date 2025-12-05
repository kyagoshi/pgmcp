# pgmcp

[![Tests](https://github.com/kyagoshi/pgmcp/actions/workflows/test.yml/badge.svg)](https://github.com/kyagoshi/pgmcp/actions/workflows/test.yml)

PostgreSQLデータベースのテーブル情報を取得するMCPサーバーです。

## 機能

- **list_tables**: 指定したスキーマのテーブル一覧を取得
- **get_table_schema**: 指定したテーブルのカラム情報（名前、型、NULL許可、デフォルト値、主キー、コメント）を取得
- **get_table_indexes**: 指定したテーブルのインデックス情報（名前、カラム、ユニーク、タイプ、定義）を取得
- **get_foreign_keys**: 指定したテーブルの外部キー情報（制約名、カラム、参照先テーブル、参照先カラム）を取得

## 要件

- Python 3.10以上
- uv（パッケージ管理）
- PostgreSQLデータベースへのアクセス

## インストール

### uvx（推奨）

`uvx`を使えばインストール不要で直接実行できます:

```bash
uvx --from git+https://github.com/kyagoshi/pgmcp pgmcp
```

### ローカルインストール

```bash
git clone https://github.com/kyagoshi/pgmcp.git
cd pgmcp
uv sync
```

## MCP設定

### Claude Desktop

`~/Library/Application Support/Claude/claude_desktop_config.json`（macOS）または`%APPDATA%\Claude\claude_desktop_config.json`（Windows）に以下を追加:

```json
{
  "mcpServers": {
    "pgmcp": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/kyagoshi/pgmcp", "pgmcp"],
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

### VS Code (GitHub Copilot)

`.vscode/mcp.json` に以下を追加:

```json
{
  "servers": {
    "pgmcp": {
      "type": "stdio",
      "command": "uvx",
      "args": ["--from", "git+https://github.com/kyagoshi/pgmcp", "pgmcp"],
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

### list_tables

指定したスキーマのテーブル一覧を取得します。

**パラメータ:**

- `schema` (string, optional): スキーマ名。デフォルトは `"public"`

**出力例:**

```text
| table_name | table_type |
|------------|------------|
| users | BASE TABLE |
| orders | BASE TABLE |
```

### get_table_schema

指定したテーブルのカラム情報を取得します。

**パラメータ:**

- `table_name` (string, required): テーブル名
- `schema` (string, optional): スキーマ名。デフォルトは `"public"`

**出力例:**

```text
| column_name | data_type | nullable | default | PK | comment |
|-------------|-----------|----------|---------|-----|----------|
| id | integer | NO | nextval('users_id_seq'::regclass) | ✓ | ユーザーID |
| name | character varying(100) | NO | - |  | ユーザー名 |
| email | character varying(255) | YES | - |  | メールアドレス |
```

### get_table_indexes

指定したテーブルのインデックス情報を取得します。

**パラメータ:**

- `table_name` (string, required): テーブル名
- `schema` (string, optional): スキーマ名。デフォルトは `"public"`

**出力例:**

```text
| index_name | columns | unique | type | definition |
|------------|---------|--------|------|------------|
| users_pkey | id | ✓ | btree | CREATE UNIQUE INDEX users_pkey ON public.users USING btree (id) |
| users_email_idx | email | ✓ | btree | CREATE UNIQUE INDEX users_email_idx ON public.users USING btree (email) |
```

### get_foreign_keys

指定したテーブルの外部キー情報を取得します。

**パラメータ:**

- `table_name` (string, required): テーブル名
- `schema` (string, optional): スキーマ名。デフォルトは `"public"`

**出力例:**

```text
| constraint_name | column_name | foreign_table | foreign_column |
|-----------------|-------------|---------------|----------------|
| orders_user_id_fkey | user_id | users | id |
```

## 開発

開発者向けの情報は [CONTRIBUTING.md](CONTRIBUTING.md) を参照してください。

## ライセンス

このプロジェクトは [Apache License 2.0](LICENSE) の下でライセンスされています。

依存ライブラリのライセンス情報は [THIRD_PARTY_LICENSES](THIRD_PARTY_LICENSES) を参照してください。
