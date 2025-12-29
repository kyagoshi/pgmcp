# pip-audit失敗: 新たな脆弱性の検出 (2025-12-29)

## 概要

2025年12月29日03:35(UTC)に実行された定期セキュリティ監査(pip-audit)が失敗しました。

**参照:**
- Workflow Run: https://github.com/kyagoshi/pgmcp/actions/runs/20564134795
- Check Suite: https://github.com/kyagoshi/pgmcp/commit/24c7446ca9036bd18767ae91122edd9b41a56180/checks?check_suite_id=53155477067
- Commit: 24c7446ca9036bd18767ae91122edd9b41a56180

## 検出された脆弱性

FastMCPおよびMCP Python SDKに複数の新しい脆弱性が2025年12月に公開されました:

### 1. CVE-2025-62801 - FastMCP Command Injection
- **影響範囲**: FastMCP < 2.13.0
- **深刻度**: High (CVSS 7.8)
- **内容**: Windows環境で`server_name`フィールドを通じたOSコマンドインジェクション
- **修正バージョン**: FastMCP 2.13.0以降

### 2. CVE-2025-62800 - FastMCP Reflected XSS
- **影響範囲**: FastMCP < 2.13.0
- **内容**: OAuthコールバックページにおける反射型XSS
- **修正バージョン**: FastMCP 2.13.0以降

### 3. CVE-2025-66416 - MCP SDK DNS Rebinding
- **影響範囲**: MCP SDK < 1.23.0
- **深刻度**: High (CVSS 7.6)
- **内容**: localhost上の認証なしHTTPサーバーにおけるDNSリバインディング攻撃
- **修正バージョン**: MCP SDK 1.23.0以降
- **備考**: `.pip-audit-ignore.json`で一時的に除外中（fastmcp 2.14待ち）

### 4. CVE-2025-53366 - MCP SDK DoS
- **影響範囲**: MCP SDK < 1.9.4
- **内容**: 不正なリクエストによるDoS
- **修正バージョン**: MCP SDK 1.9.4以降

## 対応方針

### 短期対応（緊急）

1. **FastMCPのアップグレード**: 2.13.0以降へ
   - CVE-2025-62801とCVE-2025-62800を修正
   
2. **一時的な脆弱性除外の追加**:
   - `.pip-audit-ignore.json`に新規CVEを追加（必要に応じて）

### 中期対応

1. **MCP SDKのアップグレード**: 1.23.0以降へ
   - FastMCP 2.14がMCP SDK 1.23.0をサポート後に実施
   - CVE-2025-66416の除外を解除

2. **依存関係の定期的な見直し**
   - 月次でのセキュリティ監査結果の確認

## 影響範囲

- このリポジトリは読み取り専用のPostgreSQLクエリを実行するMCPサーバーです
- FastMCPはサーバーフレームワークとして使用されていますが:
  - Windows環境での実行は想定していない（CVE-2025-62801の影響は限定的）
  - OAuth機能は使用していない（CVE-2025-62800の影響は限定的）
  - HTTP transportは使用していない（CVE-2025-66416の影響は限定的）

ただし、セキュリティベストプラクティスとして、すべての脆弱性を修正することが推奨されます。

## 実装タスク

- [ ] FastMCP 2.13.0以降へのアップグレード
- [ ] pyproject.tomlの依存関係更新
- [ ] uv.lockの更新
- [ ] pip-auditの再実行と確認
- [ ] 必要に応じて`.pip-audit-ignore.json`の更新
- [ ] THIRD_PARTY_LICENSESファイルの更新（該当する場合）
- [ ] テストの実行と確認
- [ ] ドキュメントの更新（該当する場合）

## 関連Issue

- #15 - Security Audit (pip-audit)の失敗時に検出された結果表示を行う
- #12 - 依存ライブラリの脆弱性チェックとCI導入（クローズ済み）

## 参考リンク

- [NVD - CVE-2025-62801](https://nvd.nist.gov/vuln/detail/CVE-2025-62801)
- [GitHub Advisory - CVE-2025-66416](https://github.com/advisories/GHSA-9h52-p55h-vw2f)
- [FastMCP Security Advisories](https://github.com/jlowin/fastmcp/security/advisories)
