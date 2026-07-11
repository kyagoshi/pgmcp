# 開発ガイド

このドキュメントは pgmcp の開発者向けの情報を提供します。

## 開発環境のセットアップ

### 前提条件

- Python 3.10以上
- uv（パッケージ管理）
- Docker（統合テスト用）

### 開発用依存関係のインストール

```bash
# リポジトリをクローン
git clone https://github.com/kyagoshi/pgmcp.git
cd pgmcp

# 開発用依存関係をインストール
uv sync --extra dev
```

## テスト

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

## コード品質

### リンター・フォーマッター

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

### Pre-commit フック

コミット前に自動でコード品質チェックを実行します。

```bash
# pre-commitのセットアップ（初回のみ）
uv run pre-commit install

# 手動で全ファイルに対してチェックを実行
uv run pre-commit run --all-files
```

## セキュリティスキャン (uv audit)

- `.github/workflows/uv-audit.yml` で Pull Request と週次（月曜 03:00 UTC）に `uv audit --locked --preview-features audit-command` を実行します。
- OSV に登録された既知の脆弱性を1件でも検出した場合、ジョブを失敗扱いにします。
- 依存関係を更新した場合は、必ずロックファイルの整合性と監査結果を確認してください。

### ローカルでの実行例

```bash
uv lock --check
uv audit --locked --preview-features audit-command
```

脆弱性は修正版への更新で解消し、恒久的な除外は追加しないでください。修正版が公開されていない脆弱性をやむを得ず一時除外する場合は、理由と見直し期限を Pull Request に記載したうえで、uv 標準の `--ignore-until-fixed <ID>` を使用します。

## ローカル開発

### サーバーの実行

```bash
# 環境変数を設定して実行
PGHOST=localhost PGPORT=5433 PGDATABASE=testdb PGUSER=testuser PGPASSWORD=testpass uv run server.py
```

**注意**: データベース接続は自動的にリードオンリーで確立されます（`psycopg2.connection.set_session(readonly=True)`）。書き込み系のクエリを実行すると `ReadOnlySqlTransaction` エラーが発生します。

### FastMCP開発サーバー

FastMCPの開発サーバーを使用すると、ホットリロードやデバッグが容易になります。

```bash
uv run fastmcp dev server.py
```

## プロジェクト構造

```text
pgmcp/
├── src/
│   └── pgmcp/
│       ├── __init__.py
│       └── server.py      # MCPサーバーの実装
├── tests/
│   ├── test_server.py     # ユニットテスト
│   └── test_integration.py # 統合テスト
├── docker/
│   └── init.sql           # テストDB初期化SQL
├── docker-compose.yml     # テスト用Docker設定
├── pyproject.toml         # プロジェクト設定
├── LICENSE                # Apache License 2.0
├── THIRD_PARTY_LICENSES   # 依存ライブラリのライセンス
├── CONTRIBUTING.md        # このファイル
└── README.md              # ユーザー向けドキュメント
```

## 依存ライブラリのライセンス確認

新しい依存関係を追加する際は、ライセンスの互換性を確認してください。

```bash
# licensecheck をインストール（dev 依存に含まれます）
uv sync --extra dev
# または個別に導入する場合
uv pip install licensecheck

# ライセンスチェックを実行
licensecheck
```

## リリース手順

1. バージョン番号を `pyproject.toml` で更新
2. CHANGELOG を更新（必要な場合）
3. テストが全て通ることを確認
4. タグを作成してプッシュ

```bash
git tag v0.1.0
git push origin v0.1.0
```
