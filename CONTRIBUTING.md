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

## セキュリティスキャン (pip-audit)

- `.github/workflows/pip-audit.yml` で Pull Request と週次（月曜 03:00 UTC）に `pip-audit` を実行します。
- High/Critical もしくは重大度不明の脆弱性を検出した場合にジョブを失敗扱いにします。
- ローカルでの実行例（uv 前提）:

```bash
uv export --format requirements.txt --locked --no-hashes --quiet > requirements.txt
uvx --from pip-audit==2.10.0 pip-audit \
  --progress-spinner=off \
  --requirement requirements.txt \
  --vulnerability-service osv \
  --format json > pip-audit.json
uv run python scripts/pip_audit_gate.py --input pip-audit.json --summary pip-audit-summary.txt
cat pip-audit-summary.txt
```

- 重大度が付与されていない脆弱性は安全側に倒し、失敗として扱います。

## ローカル開発

### サーバーの実行

```bash
# 環境変数を設定して実行
PGHOST=localhost PGPORT=5433 PGDATABASE=testdb PGUSER=testuser PGPASSWORD=testpass uv run server.py
```

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
