English | [日本語](README.ja.md)

# Stowgraph

Turns per-repository JSON files into a single graph of how your Docker images and containers relate.
Nodes are images and containers, edges are "derive" and "run", and colors are repositories.

## Why Stowgraph

- **Nothing extra to install:** `generate.py` needs only the Python standard library and the docker command. The viewer is a single HTML file with no external libraries, so there is no npm and no build step.
- **A browser is all you need:** open `index.html` directly as a file and it works with no server and no external requests. It works offline, and on a machine without Docker.
- **Read-only access to Docker:** it only lists and inspects, and never changes images or containers. No resident service or container, so no Docker socket to hand out.
- **Small enough to read:** one Python file and one HTML file.

## Usage

### 1. Set up (once)

Install Python with pyenv and create a virtual environment `.venv` in this folder. From then on, run commands with `.venv/bin/python`.

```bash
cd stowgraph
git -C "$(pyenv root)" pull   # only if the pyenv definitions are outdated and the pinned version is missing
pyenv install -s "$(cat .python-version)"
"$(pyenv root)/versions/$(cat .python-version)/bin/python" -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

<details>
<summary>About the Python version</summary>

The version is pinned in `.python-version` and libraries in `requirements.txt`.
If `generate.py` is run with anything other than the `.venv` of the pinned version, it stops and prints the reason.
To raise the version, edit `.python-version`, delete `.venv`, and recreate it.

Do not go back to a Python older than 3.14.10.
In October 2026, weak private keys were found in eight intermediate CAs of eMudhra, an Indian certificate authority ([eMudhra's statement](https://emudhra.com/en/post/certificate-security-incident)).
Python 3.14.10 blocks these keys in the `ssl` module ([release notes](https://www.python.org/downloads/release/python-31410/), CVE-2026-115557), and the pip bundled with 3.14.10 is 26.2.2, whose certificate bundle (certifi 2026.10.19) no longer includes the affected emSign root (checked locally).
A pip older than 26.2.2 keeps trusting that root through its bundled certifi ([Python notice](https://discuss.python.org/t/information-for-python-users-regarding-emudhra-emsign-ca-certificate-security-incident/109576) and the explanation in its thread).
If you ever add certifi to `requirements.txt`, use 2026.10.19 or later.

</details>

### 2. Generate the JSON

Run this for each repository, in an environment where the docker command works.

```bash
cd stowgraph
.venv/bin/python generate.py ../my-app
# Add images that do not appear in config files and are used only at run time with --image
.venv/bin/python generate.py ../my-lab --image quay.io/frrouting/frr:10.7.1
```

If the state of Docker changes, run it again. The JSON is not updated automatically.

> [!NOTE]
> The value of `--image` is passed as it is to `docker image inspect`. Pass only image names you trust. The script only reads Docker (`images`, `ps`, `inspect`) and never starts, changes or removes anything.

> [!WARNING]
> The JSON contains the repository's local absolute path. Check it before putting it anywhere public or pasting it into an issue.

### 3. Open the graph

- **Serve over HTTP (recommended):** `repos/` is read automatically, and the "Reload" button refreshes it.

  ```bash
  .venv/bin/python -m http.server 8765 --bind 127.0.0.1   # open http://localhost:8765/ in a browser
  ```

  Without `--bind 127.0.0.1` the server listens on all interfaces and may be visible from outside this PC. Always add it.

- **Open as a file:** open `index.html` directly and choose `repos/` with "Choose folder", or pick the JSON files with "Choose files".

The page shows English or Japanese according to your browser's language. Use the button at the top right to switch; the choice is remembered in the browser.

## Claude Code skill

`.claude/skills/stowgraph-json/` contains a skill that lets Claude Code do step 2.
Start Claude Code in this folder and pass it the path of the target repository.

```text
/stowgraph-json ../my-app
/stowgraph-json ../my-lab --image quay.io/frrouting/frr:10.7.1
```

If `--image` is omitted, the candidates are the images that were `runtime` images in the previous JSON and the `image:` values written in the target repository's YAML files.
It does not change files in the target repository, and writes only one JSON file in `repos/`.

The skill is written in English. A Japanese version is in `SKILL.ja.md`; to use it, replace `SKILL.md` with it.

## Details

<details>
<summary>File layout</summary>

```
stowgraph/
├── index.html                    # Graph viewer (no external libraries, single file; English / Japanese UI)
├── generate.py                   # Builds the JSON for one repository from your local Docker
├── schema/repo-graph.schema.json # Definition of the JSON structure (JSON Schema)
├── .python-version               # Python version to use (read by pyenv)
├── requirements.txt              # Libraries to use (currently standard library only)
├── README.md / README.ja.md      # This file (English / Japanese)
├── LICENSE / NOTICE              # Apache License 2.0 / copyright notice
├── SECURITY.md                   # How to report a vulnerability
├── .claude/skills/stowgraph-json/  # Claude Code skill (SKILL.md, SKILL.ja.md for Japanese, check.sh)
├── .venv/                        # Virtual environment (created during setup)
└── repos/                        # One file per repository goes here (not tracked by git)
    ├── my-app.json
    └── my-lab.json
```

The JSON files in `repos/` are built from each person's own Docker state, so git does not track them. The same goes for `.venv/`.

</details>

<details>
<summary>JSON structure and design principles</summary>

One file per repository. The authoritative definition is in `schema/repo-graph.schema.json`.

```jsonc
{
  "$schema": "../schema/repo-graph.schema.json",
  "schemaVersion": 1,
  "repository": {
    "name": "my-app",                    // Required. Key for the legend and color coding (unique across files)
    "path": "/path/to/my-app",
    "color": "#e07a2e"                   // Optional. Assigned automatically if omitted
  },
  "generatedAt": "2026-01-02T03:04:05Z",
  "images": [
    {
      "id": "sha256:aaaa…",              // Required. Node identifier
      "tags": ["mcr.microsoft.com/devcontainers/typescript-node:24-bookworm"],
      "role": "base",                    // base / derived / runtime. Inferred if omitted
      "parent": null,                    // ID of the base image → "derive" edge
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
      "id": "cccc…",                     // Required. 64-digit container ID
      "name": "happy_newton",
      "image": "sha256:bbbb…",           // Required. ID of the image it started from → "run" edge
      "state": "exited",
      "created": "2026-01-02T00:00:00Z"
    }
  ]
}
```

- **Edges are not stored; they are derived from references:** relationships are expressed only by the ID references `parent` and `image`. A separate list of edges could disagree with the nodes.
- **Merge by ID:** if the same ID appears in multiple files, it becomes a single node. A node shared by several repositories, such as a base image, gets a striped color band.
- **Write ancestors in each file:** the base of a derived image is also listed in that repository's file. Even without the other repositories' files, each repository's graph is complete on its own.
- **Fill in IDs that have no definition:** if a referenced ID is defined in no file, it is shown as an "unknown image" and listed in the notices.

</details>

<details>
<summary>generate.py attribution rules and limitations</summary>

| Target | Condition for attributing it to the repository |
|---|---|
| Container | A label value contains the repository path (Dev Containers, Compose, containerlab, etc.), or it was started from a `vsc-` derived image (see below) |
| Image | The image such a container was started from, an image named `vsc-<folder name>-<64-digit hash>[-features][-uid]`, or one given with `--image` |
| Base | Among the images whose layer sequence is a prefix of one of the images above, the one with the most layers (walk up the ancestors) |

Limitations:

- Parent-child relationships are inferred by comparing layers. With the newer storage format, Docker does not record the parent.
- If a base image is deleted, the derived image is written as a standalone node with no parent.
- Deleted containers are not listed. The JSON is a snapshot from the time it was generated.
- A container started from a shared image (such as frr given with `--image`, or postgres used in Compose) is not listed unless its labels contain the repository path, because the image alone cannot tell which repository it belongs to.

</details>

## License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for the full text and [NOTICE](NOTICE) for the copyright notice.
To report a vulnerability, see [SECURITY.md](SECURITY.md).

Docker is a trademark of Docker, Inc. This project is not affiliated with Docker, Inc. or Anthropic.
