# uv Migration & Dependabot Setup — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate `yt-sub-playlist` from `pip + requirements.txt + venv` to `uv` with a committed lockfile, wire `standard-version` to keep `pyproject.toml` in sync, and add a Dependabot config that watches the Python stack.

**Architecture:** Single PEP 621 `pyproject.toml` becomes the dependency manifest; `uv.lock` becomes the resolver state of record. Flask dashboard deps live behind a `dashboard` optional extra. `standard-version` gets a small custom updater so version bumps land in both `package.json` and `pyproject.toml`. Dependabot's native `uv` ecosystem watches the lockfile weekly.

**Tech Stack:** Python 3.11, uv 0.11+, Hatchling (build backend), Node + pnpm (existing `standard-version` tooling), GitHub Dependabot.

**Spec:** `docs/superpowers/specs/2026-06-26-uv-and-dependabot-migration-design.md`

---

## File Structure

| Action | Path | Responsibility |
|---|---|---|
| Create | `pyproject.toml` | Project metadata + dependencies (PEP 621) |
| Create | `uv.lock` | Generated lockfile (committed) |
| Create | `scripts/bump-pyproject.js` | `standard-version` custom updater for TOML |
| Create | `scripts/bump-pyproject.test.js` | Standalone Node test for the updater |
| Create | `.github/dependabot.yml` | Dependabot config (Python only) |
| Modify | `package.json` | Add `standard-version.bumpFiles` config |
| Modify | `README.md` | Replace pip+venv install steps with `uv sync` |
| Delete | `requirements.txt` | Superseded by `pyproject.toml` + `uv.lock` |
| Delete | `venv/` (working tree only) | Superseded by uv-managed `.venv/` |

The `.gitignore` already covers `.venv` and `venv/` — no changes needed there.

---

## Task 1: Add `pyproject.toml`

**Files:**
- Create: `pyproject.toml`

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[project]
name = "yt-sub-playlist"
version = "4.1.0"
description = "Automatically sync YouTube subscription uploads into a custom playlist"
readme = "README.md"
license = { file = "LICENSE" }
requires-python = ">=3.11"
dependencies = [
  "google-api-python-client==2.116.0",
  "google-auth==2.27.0",
  "google-auth-oauthlib==1.2.0",
  "google-auth-httplib2==0.2.0",
  "python-dotenv==1.0.1",
]

[project.optional-dependencies]
dashboard = [
  "Flask==3.0.0",
  "Flask-CORS==4.0.0",
  "Werkzeug==3.0.6",
]

[project.scripts]
yt-sub-playlist = "yt_sub_playlist.__main__:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["yt_sub_playlist"]
```

- [ ] **Step 2: Validate metadata parses**

Run: `uv lock --check 2>&1 || uv lock --dry-run`
Expected: uv reports it would generate a lockfile. If `uv lock --check` errors because no lockfile exists yet, that's expected — the dry-run fallback should succeed.

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "chore(build): add pyproject.toml for uv migration"
```

---

## Task 2: Generate and commit `uv.lock`, verify install

**Files:**
- Create: `uv.lock` (generated)

- [ ] **Step 1: Generate the lockfile**

Run: `uv lock`
Expected: `uv.lock` is created at repo root. Output ends with a resolution summary.

- [ ] **Step 2: Sync the core environment**

Run: `uv sync`
Expected: `.venv/` is created. Output lists installed packages including the five core deps. No Flask packages installed.

- [ ] **Step 3: Smoke-test the CLI**

Run: `uv run python -m yt_sub_playlist --help`
Expected: argparse help text prints without import errors. (If it requires `client_secrets.json` to even print help, treat that as a pre-existing issue and skip the runtime check — but the import chain must not error.)

- [ ] **Step 4: Sync with the dashboard extra**

Run: `uv sync --extra dashboard`
Expected: Output lists `Flask`, `Flask-Cors`, `Werkzeug` as newly installed.

If Werkzeug 3.0.6 fails to resolve against Flask 3.0.0, bump the pin in `pyproject.toml` to the next compatible 3.0.x (try `3.0.4`, then `3.0.3`, then `3.0.1`), re-run `uv lock`, and continue.

- [ ] **Step 5: Smoke-test dashboard import**

Run: `uv run python -c "from dashboard.backend import app; print('ok')"`
Expected: `ok`. If the import path differs, inspect `dashboard/backend/` and run the actual entry import — the goal is to confirm Flask deps resolve at runtime.

- [ ] **Step 6: Commit**

```bash
git add uv.lock
git commit -m "chore(build): add uv lockfile"
```

---

## Task 3: Remove legacy `requirements.txt` and `venv/`

**Files:**
- Delete: `requirements.txt`
- Delete: `venv/` (working-tree directory)

- [ ] **Step 1: Verify the uv environment is the only one needed**

Run: `ls -d venv .venv requirements.txt 2>/dev/null`
Expected: all three appear. (If `.venv` is missing, re-run `uv sync` first.)

- [ ] **Step 2: Delete `requirements.txt`**

Run: `git rm requirements.txt`
Expected: file staged for deletion.

- [ ] **Step 3: Delete the legacy `venv/` directory**

Run: `rm -rf venv/`
Expected: directory removed. `venv/` is gitignored so no `git rm` is needed.

- [ ] **Step 4: Commit**

```bash
git commit -m "chore(build): remove requirements.txt and legacy venv"
```

---

## Task 4: Write the `standard-version` TOML updater + its test

**Files:**
- Create: `scripts/bump-pyproject.js`
- Create: `scripts/bump-pyproject.test.js`

This task uses TDD: write the test first, watch it fail, then implement.

- [ ] **Step 1: Write the failing test**

Create `scripts/bump-pyproject.test.js`:

```js
const assert = require("node:assert/strict");
const updater = require("./bump-pyproject.js");

const SAMPLE = `[project]
name = "yt-sub-playlist"
version = "4.1.0"
description = "x"

[tool.something]
version = "9.9.9"
`;

// readVersion finds the [project] version, not other tables
assert.equal(updater.readVersion(SAMPLE), "4.1.0", "readVersion returns project version");

// writeVersion updates only the [project] version
const bumped = updater.writeVersion(SAMPLE, "4.2.0");
assert.match(bumped, /\[project\][\s\S]*?version = "4\.2\.0"/, "writeVersion bumps project version");
assert.match(bumped, /\[tool\.something\][\s\S]*?version = "9\.9\.9"/, "writeVersion leaves other tables alone");

// readVersion throws on missing [project] version
assert.throws(
  () => updater.readVersion(`[tool.x]\nversion = "1.0.0"\n`),
  /version not found/,
  "readVersion throws when [project] version is missing",
);

console.log("ok - bump-pyproject updater");
```

- [ ] **Step 2: Run the test to confirm it fails**

Run: `node scripts/bump-pyproject.test.js`
Expected: `Error: Cannot find module './bump-pyproject.js'` (the implementation doesn't exist yet).

- [ ] **Step 3: Implement the updater**

Create `scripts/bump-pyproject.js`:

```js
const VERSION_RE = /(\[project\][\s\S]*?\n\s*version\s*=\s*")([^"]+)(")/;

module.exports = {
  readVersion(contents) {
    const m = contents.match(VERSION_RE);
    if (!m) throw new Error("version not found under [project] in pyproject.toml");
    return m[2];
  },
  writeVersion(contents, version) {
    if (!VERSION_RE.test(contents)) {
      throw new Error("version not found under [project] in pyproject.toml");
    }
    return contents.replace(VERSION_RE, `$1${version}$3`);
  },
};
```

- [ ] **Step 4: Run the test to confirm it passes**

Run: `node scripts/bump-pyproject.test.js`
Expected: `ok - bump-pyproject updater`

- [ ] **Step 5: Commit**

```bash
git add scripts/bump-pyproject.js scripts/bump-pyproject.test.js
git commit -m "chore(release): add pyproject.toml version updater for standard-version"
```

---

## Task 5: Wire the updater into `standard-version` and verify a dry-run

**Files:**
- Modify: `package.json`

- [ ] **Step 1: Add `standard-version` config to `package.json`**

In `package.json`, after the existing `"devDependencies"` block (still inside the top-level object), add:

```json
,
"standard-version": {
  "bumpFiles": [
    { "filename": "package.json", "type": "json" },
    { "filename": "pyproject.toml", "updater": "scripts/bump-pyproject.js" }
  ]
}
```

The final file should validate as JSON (no trailing commas). If unsure, run `node -e "JSON.parse(require('fs').readFileSync('package.json','utf8'))"` — silence means valid.

- [ ] **Step 2: Run a release dry-run**

Run: `npm run release:dry-run`
Expected: Output shows projected bumps for both `package.json` and `pyproject.toml`. Both files report a version transition like `4.1.0 → 4.1.1` (patch) or similar based on commits since the last tag.

If the dry-run reports `pyproject.toml` unchanged, double-check the `bumpFiles` array — the `updater` field is a path relative to the project root and must resolve to a CommonJS module.

- [ ] **Step 3: Commit**

```bash
git add package.json
git commit -m "chore(release): wire pyproject.toml into standard-version bumpFiles"
```

---

## Task 6: Update `README.md` install + usage instructions

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Replace the Installation block**

Find the existing Installation section (begins with `## Installation` and contains the `python3 -m venv venv` snippet). Replace its code block with:

```bash
git clone https://github.com/yourusername/yt-sub-playlist.git
cd yt-sub-playlist
uv sync                       # CLI only
uv sync --extra dashboard     # CLI + Flask dashboard
```

- [ ] **Step 2: Update the Setup section's "Run Initial Auth Flow" command**

Find `python -m yt_sub_playlist.auth.oauth` in the Setup section and change it to:

```bash
uv run python -m yt_sub_playlist.auth.oauth
```

- [ ] **Step 3: Sanity-check there are no other lingering `pip install -r` references**

Run: `grep -nE "pip install -r|requirements\.txt|source venv/bin/activate" README.md`
Expected: no matches. If any appear, update them to the `uv sync` / `uv run` equivalents.

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: update install and usage instructions for uv"
```

---

## Task 7: Add `.github/dependabot.yml`

**Files:**
- Create: `.github/dependabot.yml`

- [ ] **Step 1: Create the Dependabot config**

```yaml
version: 2
updates:
  - package-ecosystem: "uv"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 5
    groups:
      google-auth:
        patterns:
          - "google-auth*"
          - "google-api-python-client"
      flask:
        patterns:
          - "Flask*"
          - "Werkzeug"
    commit-message:
      prefix: "chore(deps)"
      include: "scope"
    labels:
      - "dependencies"
```

- [ ] **Step 2: Validate YAML syntax**

Run: `uv run python -c "import yaml; yaml.safe_load(open('.github/dependabot.yml'))"`
Expected: no output (silent success). If `pyyaml` is not in the environment, fall back to: `python3 -c "import yaml; yaml.safe_load(open('.github/dependabot.yml'))"` from any environment that has it, or use any online YAML linter.

- [ ] **Step 3: Commit**

```bash
git add .github/dependabot.yml
git commit -m "ci: add dependabot config for uv ecosystem"
```

---

## Task 8: Post-merge verification (manual, after PR lands)

This task isn't a code change — it's a verification step the engineer performs after the PR merges to `main`. It's listed so the work isn't considered "done" prematurely.

- [ ] **Step 1: Confirm Dependabot accepts the config**

After the PR merges, visit GitHub → **Insights** → **Dependency graph** → **Dependabot**. Confirm the `uv` job is listed and shows a recent run timestamp.

- [ ] **Step 2: Confirm a future release bumps both manifests**

The next time `npm run release` runs (for any reason), confirm the resulting commit modifies both `package.json` and `pyproject.toml`. If only `package.json` changes, the `bumpFiles` config is misconfigured — revisit Task 5.

- [ ] **Step 3: If Dependabot's `uv` ecosystem fails**

If the Dependabot job errors with "unsupported ecosystem" or similar, the GitHub instance hasn't rolled out native `uv` support. Fall back: edit `.github/dependabot.yml` and change `package-ecosystem: "uv"` to `package-ecosystem: "pip"`. Re-commit. Pip-ecosystem Dependabot will read `pyproject.toml` but won't touch `uv.lock` — each merged Dependabot PR will then require a follow-up local `uv sync` before pushing.

---

## Done criteria

- [ ] `uv sync` resolves and installs core deps
- [ ] `uv sync --extra dashboard` resolves and installs Flask deps
- [ ] `uv run python -m yt_sub_playlist --help` runs without import errors
- [ ] `npm run release:dry-run` shows planned bumps in both `package.json` and `pyproject.toml`
- [ ] `node scripts/bump-pyproject.test.js` passes
- [ ] `requirements.txt` and `venv/` are gone
- [ ] `.github/dependabot.yml` exists and parses as YAML
- [ ] README's installation steps reference `uv sync`, not `pip install -r requirements.txt`
