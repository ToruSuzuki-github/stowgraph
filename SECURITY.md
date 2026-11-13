# Security Policy

English | [日本語](#セキュリティポリシー)

## Supported versions

Only the latest version on the `main` branch is supported.

## Reporting a vulnerability

Please report vulnerabilities **privately**, not in a public issue.

1. Open the **Security** tab of this repository.
2. Choose **Report a vulnerability** (GitHub's private vulnerability reporting).

Please include:

- Steps to reproduce, and the impact you expect
- The affected file or function
- If you attach a JSON file from `repos/`, remove the local paths first (they contain your directory layout)

This is a personal project, so replies are best effort.

## Scope

Stowgraph is a local tool. It reads JSON files and runs the `docker` CLI on your machine. Examples of what is in scope:

- Script execution in `index.html` caused by a crafted JSON file (cross-site scripting)
- Unintended command execution or file writes outside `repos/` in `generate.py`

Serving the folder with `python -m http.server` on an interface other than `127.0.0.1` exposes it to other machines. That is a configuration choice and is out of scope; the documentation always uses `--bind 127.0.0.1`.

---

# セキュリティポリシー

## 対象バージョン

`main` ブランチの最新版のみを対象とします。

## 脆弱性の報告

脆弱性は、公開の Issue ではなく**非公開で**報告してください。

1. このリポジトリの **Security** タブを開きます。
2. **Report a vulnerability**（GitHub の Private vulnerability reporting）を選びます。

次の内容を書いてください。

- 再現手順と、想定される影響
- 該当するファイルや関数
- `repos/` の JSON を添付する場合は、先にローカルのパスを消してください（ディレクトリ構成が含まれます）

個人のプロジェクトのため、返信は可能な範囲で行います。

## 範囲

Stowgraph は手元で動かすツールで、JSON を読み、お使いのマシンで `docker` コマンドを実行します。対象の例は次のとおりです。

- 細工した JSON によって `index.html` でスクリプトが実行されること（クロスサイトスクリプティング）
- `generate.py` による意図しないコマンド実行や、`repos/` 以外へのファイル書き込み

`python -m http.server` を `127.0.0.1` 以外で待ち受けると、ほかのマシンから見えます。これは利用者の設定の問題で、対象外です。ドキュメントでは常に `--bind 127.0.0.1` を付けています。
