[English](README.md) | 日本語

# Stowgraph

リポジトリごとの JSON から、Docker のイメージとコンテナの関係を 1 枚のグラフにします。
ノードはイメージとコンテナ、エッジは「派生」と「起動」、色はリポジトリです。

## Stowgraph の強み

- **追加で入れるものがない:** `generate.py` は Python の標準ライブラリと docker コマンドだけで動きます。表示側も外部ライブラリなしの HTML 1 ファイルなので、npm もビルドも要りません。
- **ブラウザだけで見られる:** `index.html` はファイルとして直接開けば、サーバーなし・外部通信なしで表示できます。オフラインでも、Docker のないマシンでも見られます。
- **Docker は読むだけ:** 一覧と詳細を読むだけで、イメージやコンテナは変更しません。常駐サービスもコンテナも置かないので、Docker ソケットを渡す必要もありません。
- **全部読んで確かめられる:** Python 1 ファイルと HTML 1 ファイルだけです。

## 使い方

### 1. 準備（最初に一度だけ）

pyenv で Python を入れ、このフォルダに仮想環境 `.venv` を作ります。以降は `.venv/bin/python` で実行します。

```bash
cd stowgraph
git -C "$(pyenv root)" pull   # pyenv の定義が古く、固定したバージョンがないときだけ
pyenv install -s "$(cat .python-version)"
"$(pyenv root)/versions/$(cat .python-version)/bin/python" -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

<details>
<summary>Python のバージョンについて</summary>

バージョンは `.python-version` で、ライブラリは `requirements.txt` で固定しています。
`generate.py` は、固定したバージョンの `.venv` 以外で実行すると、理由を表示して止まります。
バージョンを上げるときは `.python-version` を書き換え、`.venv` を消して作り直してください。

3.14.10 より古い Python には戻さないでください。
2026 年 10 月に、インドの認証局 eMudhra の中間 CA 8 本で、秘密鍵が弱い（推測できる）値だったと分かりました（[eMudhra の声明](https://emudhra.com/en/post/certificate-security-incident)）。
Python 3.14.10 は、これらの鍵を `ssl` モジュールで拒否します（[リリースノート](https://www.python.org/downloads/release/python-31410/)、CVE-2026-115557）。3.14.10 に同梱の pip は 26.2.2 で、その証明書バンドル（certifi 2026.10.19）には、問題の emSign ルートが含まれません（手元の環境で確認）。
26.2.2 より古い pip は、同梱の certifi 経由でこのルートを信頼したままです（[Python のお知らせ](https://discuss.python.org/t/information-for-python-users-regarding-emudhra-emsign-ca-certificate-security-incident/109576)と、そのスレッド内の説明）。
`requirements.txt` に certifi を加える場合は、2026.10.19 以降を使ってください。

</details>

### 2. JSON を作る

docker コマンドが動く環境で、リポジトリごとに実行します。

```bash
cd stowgraph
.venv/bin/python generate.py ../my-app
# 設定ファイルに現れず、実行時にだけ使うイメージは --image で足す
.venv/bin/python generate.py ../my-lab --image quay.io/frrouting/frr:10.7.1
```

Docker の状態が変わったら、やり直してください。JSON は自動では更新されません。

> [!NOTE]
> `--image` に渡した値は、そのまま `docker image inspect` に渡されます。信頼できるイメージ名だけを渡してください。このスクリプトは Docker の情報を読むだけ（`images`・`ps`・`inspect`）で、起動・変更・削除は行いません。

> [!WARNING]
> JSON にはリポジトリのローカルの絶対パスが入ります。公開する場所へ置いたり、issue に貼ったりする前に、中身を確認してください。

### 3. グラフを開く

- **HTTP で配信する（おすすめ）:** `repos/` を自動で読み、「再読込」ボタンで最新にできます。

  ```bash
  .venv/bin/python -m http.server 8765 --bind 127.0.0.1   # ブラウザで http://localhost:8765/ を開く
  ```

  `--bind 127.0.0.1` を省くと全インターフェースで待ち受け、同じ PC の外からも見えることがあります。必ず付けてください。

- **ファイルとして開く:** `index.html` を直接開き、「フォルダを選択」で `repos/` を選ぶか、「ファイルを選択」で JSON を選びます。

画面はブラウザの言語に合わせて英語か日本語で表示します。右上のボタンで切り替えられ、選んだ言語はブラウザに記憶されます。

## Claude Code スキル

`.claude/skills/stowgraph-json/` に、手順 2 を Claude Code に任せるスキルがあります。
このフォルダで Claude Code を起動し、対象リポジトリのパスを渡します。

```text
/stowgraph-json ../my-app
/stowgraph-json ../my-lab --image quay.io/frrouting/frr:10.7.1
```

`--image` を省くと、前回の JSON で実行用だったイメージと、対象リポジトリの YAML に書かれた `image:` を候補にします。
対象リポジトリのファイルは変更せず、書き出すのは `repos/` の JSON 1 つだけです。

スキルの本文は英語です。日本語版は `SKILL.ja.md` にあるので、使いたいときは `SKILL.md` と差し替えてください。

## 詳細

<details>
<summary>ファイル構成</summary>

```
stowgraph/
├── index.html                    # グラフ表示（外部ライブラリなし・1ファイル。画面は英語・日本語）
├── generate.py                   # 手元の Docker から 1 リポジトリ分の JSON を作る
├── schema/repo-graph.schema.json # JSON の構造定義（JSON Schema）
├── .python-version               # 使う Python のバージョン（pyenv が読む）
├── requirements.txt              # 使うライブラリ（今は標準ライブラリのみ）
├── README.md / README.ja.md      # このファイル（英語 / 日本語）
├── LICENSE / NOTICE              # Apache License 2.0 / 著作権表示
├── SECURITY.md                   # 脆弱性の報告方法
├── .claude/skills/stowgraph-json/  # Claude Code 用のスキル（SKILL.md、日本語版の SKILL.ja.md、check.sh）
├── .venv/                        # 仮想環境（準備で作る）
└── repos/                        # ここに 1 リポジトリ 1 ファイルで置く（git 管理外）
    ├── my-app.json
    └── my-lab.json
```

`repos/` の JSON は各自の Docker の状態から作るため、git では管理しません。`.venv/` も同様です。

</details>

<details>
<summary>JSON の構造と設計の考え方</summary>

1 リポジトリにつき 1 ファイルです。正式な定義は `schema/repo-graph.schema.json` にあります。

```jsonc
{
  "$schema": "../schema/repo-graph.schema.json",
  "schemaVersion": 1,
  "repository": {
    "name": "my-app",                    // 必須。凡例と色分けのキー（ファイル間で一意）
    "path": "/path/to/my-app",
    "color": "#e07a2e"                   // 任意。省略すると自動で割り当てる
  },
  "generatedAt": "2026-01-02T03:04:05Z",
  "images": [
    {
      "id": "sha256:aaaa…",              // 必須。ノードの識別子
      "tags": ["mcr.microsoft.com/devcontainers/typescript-node:24-bookworm"],
      "role": "base",                    // base / derived / runtime。省略時は推定
      "parent": null,                    // 土台のイメージ ID → エッジ「派生」
      "layers": 25, "size": 1900000000, "created": "2026-01-01T00:00:00Z"
    },
    {
      "id": "sha256:bbbb…",
      "tags": ["vsc-my-app-…-uid:latest"],
      "role": "derived",
      "parent": "sha256:aaaa…",
      "layers": 26
    }
  ],
  "containers": [
    {
      "id": "cccc…",                     // 必須。64 桁のコンテナ ID
      "name": "happy_newton",
      "image": "sha256:bbbb…",           // 必須。起動元のイメージ ID → エッジ「起動」
      "state": "exited",
      "created": "2026-01-02T00:00:00Z"
    }
  ]
}
```

- **エッジは持たせず、参照から作る:** 関係は `parent` と `image` の ID 参照だけで表します。エッジの一覧を別に持つと、ノードと食い違う余地ができるためです。
- **ID で合成する:** 複数のファイルに同じ ID があれば 1 つのノードにまとめます。ベースイメージのように共有されているノードは、色帯が縞になります。
- **祖先も各ファイルに書く:** 派生イメージの土台は、そのリポジトリのファイルにも載せます。他のリポジトリのファイルが無くても、そのリポジトリだけで関係図が完結します。
- **定義のない ID は補う:** 参照先がどのファイルにも無い場合は「不明なイメージ」として表示し、注意欄に出します。

</details>

<details>
<summary>generate.py の判定ルールと限界</summary>

| 対象 | リポジトリに属すると判定する条件 |
|---|---|
| コンテナ | ラベルの値にリポジトリのパスを含む（Dev Containers、Compose、containerlab など）、または下記の `vsc-` 派生イメージから起動したもの |
| イメージ | 上記コンテナの起動元、`vsc-<フォルダ名>-<64桁のハッシュ>[-features][-uid]` という名前、`--image` で指定したもの |
| 土台 | 上記イメージと層の並びが前方一致するイメージのうち、最も層が多いもの（祖先をたどる） |

限界:

- 親子関係は層の比較による推定です。Docker は新しい保存方式では親の情報を記録しません。
- 土台のイメージを削除すると、派生イメージは親のない単独のノードとして出力されます。
- 削除済みのコンテナは載りません。JSON は生成した時点の写しです。
- 共通イメージ（`--image` で指定した frr や、Compose で使う postgres など）から起動したコンテナは、ラベルにリポジトリのパスが無いと載りません。起動元のイメージだけでは、どのリポジトリのものか区別できないためです。

</details>

## ライセンス

Apache License 2.0 です。全文は [LICENSE](LICENSE)、著作権表示は [NOTICE](NOTICE) にあります。
脆弱性の報告方法は [SECURITY.md](SECURITY.md) を参照してください。

Docker は Docker, Inc. の商標です。このプロジェクトは Docker, Inc. とも Anthropic とも関係ありません。
