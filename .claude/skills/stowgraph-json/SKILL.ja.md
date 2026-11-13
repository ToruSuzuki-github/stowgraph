---
name: stowgraph-json
description: "指定したリポジトリの Docker イメージとコンテナの関係データ（JSON）を、この stowgraph フォルダの repos/ に書き出し、Docker 関係図に反映する。「Docker 関係図を更新して」「Stowgraph を更新して」「Stowgraph の JSON を作って」「このリポジトリを関係図に載せて」と言われたとき、DevContainer の再ビルドやイメージ・コンテナの削除の後に関係図へ反映したいとき、または /stowgraph-json と入力されたときに使う。"
argument-hint: "<リポジトリのパス> [--image 実行時に使うイメージ ...]"
allowed-tools: Bash(bash ${CLAUDE_SKILL_DIR}/check.sh), Bash(.venv/bin/python generate.py *), Bash(docker image inspect *)
---

# stowgraph-json

指定したリポジトリ 1 つ分の JSON を、生成スクリプトで書き出す。JSON は手で編集しない。
このスキルは stowgraph フォルダで起動した Claude Code から使う。以下のパスはすべて stowgraph フォルダからの相対パス。
生成スクリプトと JSON 構造の説明は `README.ja.md` にある。
ユーザーには、依頼に使われた言語で返答する。

## 現在の状況

```!
bash ${CLAUDE_SKILL_DIR}/check.sh
```

## 手順

1. **前提を確かめる。** 上の「docker」「generate.py」「venv」のどれかが `unavailable` または `missing` のときは、ここで止めて理由を伝える。
   venv が使えないときは、`README.ja.md` の「使い方」の「1. 準備」の手順で `.venv` を作るよう案内する。
   DevContainer の中のセッションは docker コマンドを持たないことが多いため、
   docker コマンドが動く環境で stowgraph フォルダを開いて実行するよう案内する。

2. **対象のリポジトリを決める。** 引数 `$ARGUMENTS` の先頭が対象リポジトリのパス。残りは `--image` などの生成スクリプトへの引数。
   パスの指定がなければ、どのリポジトリを載せるかユーザーに尋ねる。
   出力先は `repos/<フォルダ名>.json`（`--name` を付けたときはその名前）。

3. **追加するイメージを決める。** 生成スクリプトは、設定ファイルに現れず実行時にだけ使うイメージ
   （containerlab のルータなど）を自動では見つけられないため、`--image` で渡す。
   - 引数に `--image` が指定されていれば、それをそのまま使う。
   - 指定がなければ、次の 2 つを合わせた候補を作る。
     - 前回の JSON（`repos/<名前>.json`）で `role` が `runtime` だったイメージのタグ。
       前回分を落とすと、再生成で関係図からそのイメージが消えてしまう。
     - 対象リポジトリの `*.yml` / `*.yaml` に書かれた `image:` の値（Compose や containerlab のトポロジー）。
       `node_modules` と `.git` は除く。
   - 候補ごとに `docker image inspect <イメージ>` を実行し、手元に無いものは除外して報告に回す。
     変数展開（`${…}`）を含む値もイメージ名として解決できないため除外する。

4. **生成する。** 表示名・色の指定はユーザーに頼まれたときだけ付ける（`--name` / `--color`）。

   ```bash
   .venv/bin/python generate.py <リポジトリのパス> [--image <イメージ> ...]
   ```

5. **結果を確かめて報告する。** 出力された JSON を読み、次を短く伝える。
   - イメージとコンテナの件数、それぞれの名前と役割（base / derived / runtime）、コンテナの状態
   - `--image` で渡したイメージと、手元に無いため除外したイメージ
   - どちらも 0 件なら、考えられる原因（DevContainer を一度もビルドしていない、コンテナとイメージを削除済み、
     フォルダ名を変えて vsc- イメージの名前と合わない）
   - 関係図の見方。HTTP で配信中なら画面の「再読込」、未配信なら次のコマンドで http://localhost:8765/ を開く

     ```bash
     .venv/bin/python -m http.server 8765 --bind 127.0.0.1
     ```

     `--bind 127.0.0.1` は必ず付ける。省くと全インターフェースで待ち受け、localhost 以外からも見えてしまう。

## 注意

- このスキルは対象リポジトリのファイルを変更しない。書き込むのは `repos/` の JSON 1 つだけ。
- 同じリポジトリの JSON は上書きされる。以前の内容は残らない。
- `repos/` の JSON にはローカルのパスが入るため、git では管理しない（`.gitignore` 済み）。
- 判定ルールと限界（共通イメージから起動したコンテナは載らない等）は `README.ja.md` を参照する。
