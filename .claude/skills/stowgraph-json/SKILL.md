---
name: stowgraph-json
description: "Write the Docker image/container relationship data (JSON) for a given repository into this stowgraph folder's repos/ and reflect it in the Docker relationship graph. Use when asked to \"update the Docker graph\", \"update Stowgraph\", \"generate the Stowgraph JSON\", or \"add this repository to the graph\"; when the graph should be refreshed after a DevContainer rebuild or after deleting images or containers; or when /stowgraph-json is typed. 日本語の依頼でも起動する: 「Docker 関係図を更新して」「Stowgraph を更新して」「Stowgraph の JSON を作って」「このリポジトリを関係図に載せて」と言われたとき、DevContainer の再ビルドやイメージ・コンテナの削除の後に関係図へ反映したいとき。"
argument-hint: "<repository path> [--image <image used only at run time> ...]"
allowed-tools: Bash(bash ${CLAUDE_SKILL_DIR}/check.sh), Bash(.venv/bin/python generate.py *), Bash(docker image inspect *)
---

# stowgraph-json

Write the JSON for one given repository with the generator script. Never edit the JSON by hand.
This skill is used from a Claude Code session started in the stowgraph folder. All paths below are relative to the stowgraph folder.
The generator script and the JSON structure are described in `README.md`.
Reply to the user in the language they used.

## Current status

```!
bash ${CLAUDE_SKILL_DIR}/check.sh
```

## Steps

1. **Check the prerequisites.** If any of "docker", "generate.py", or "venv" above shows `unavailable` or `missing`, stop here and tell the user why.
   If venv is unavailable, point the user to the "Set up" steps in the README to create `.venv`.
   A session inside a DevContainer often has no docker command,
   so tell the user to open the stowgraph folder in an environment where the docker command works and run it there.

2. **Decide the target repository.** The first token of the arguments `$ARGUMENTS` is the target repository path. The rest are arguments for the generator script, such as `--image`.
   If no path is given, ask the user which repository to add.
   The output goes to `repos/<folder name>.json` (or the name given with `--name`).

3. **Decide which images to add.** The generator script cannot automatically find images that do not appear in config files and are used only at run time
   (such as containerlab routers), so they are passed with `--image`.
   - If `--image` is given in the arguments, use it as is.
   - Otherwise, build a candidate list from both of the following.
     - Tags of the images whose `role` was `runtime` in the previous JSON (`repos/<name>.json`).
       If the previous ones are dropped, regenerating removes those images from the graph.
     - Values of `image:` written in the target repository's `*.yml` / `*.yaml` files (Compose or containerlab topologies).
       Exclude `node_modules` and `.git`.
   - Run `docker image inspect <image>` for each candidate; exclude the ones not present locally and report them.
     Values containing variable expansion (`${…}`) cannot be resolved as image names either, so exclude them.

4. **Generate.** Add the display name and color (`--name` / `--color`) only when the user asks.

   ```bash
   .venv/bin/python generate.py <repository path> [--image <image> ...]
   ```

5. **Check the result and report.** Read the output JSON and briefly tell the user:
   - The number of images and containers, the name and role (base / derived / runtime) of each, and the container states
   - The images passed with `--image`, and the images excluded because they are not present locally
   - If both counts are 0, the likely causes (the DevContainer has never been built, the containers and images were deleted,
     or the folder was renamed so it no longer matches the vsc- image names)
   - How to view the graph. If it is already being served over HTTP, use "Reload" on the page; otherwise run the command below and open http://localhost:8765/

     ```bash
     .venv/bin/python -m http.server 8765 --bind 127.0.0.1
     ```

     Always add `--bind 127.0.0.1`. Without it, the server listens on all interfaces and is reachable from outside localhost.

## Notes

- This skill does not change files in the target repository. The only thing it writes is one JSON file in `repos/`.
- The JSON of the same repository is overwritten. The previous content is not kept.
- JSON in `repos/` contains local paths, so it is not tracked by git (already in `.gitignore`).
- See `README.md` for the attribution rules and limitations (for example, containers started from a shared image are not included).
