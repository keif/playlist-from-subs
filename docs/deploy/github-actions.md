# Deploy: GitHub Actions cron

Run the daily YouTube sync as a scheduled GitHub Actions workflow in your fork. Free on Microsoft infra. No server to maintain.

---

## Prerequisites

Complete these in order before touching the workflow file.

### 1. Fork the repo

Fork `keif/yt-sub-playlist` to your own GitHub account. The workflow lives in your fork — you own the secrets and the cron schedule.

### 2. Bootstrap OAuth locally

Follow [docs/deploy/oauth-bootstrap.md](./oauth-bootstrap.md) to produce `client_secrets.json` and `token.json` on your laptop. You need both files before you can set the secrets below.

### 3. Set repo secrets

In your fork: **Settings → Secrets and variables → Actions → New repository secret**.

| Secret name | Value |
|---|---|
| `CLIENT_SECRETS_B64` | `base64 < client_secrets.json \| tr -d '\n'` |
| `TOKEN_B64` | `base64 < token.json \| tr -d '\n'` |
| `GH_PAT` | Personal Access Token — see below |

Run each command locally and paste the output as the secret value. The `tr -d '\n'` strips the trailing newline; leaving it in corrupts the base64 string.

### 4. Create a GH_PAT

**`GH_PAT` is mandatory. If it is missing, the first OAuth token refresh will succeed but the new token will never be written back. Every subsequent run will fail at `base64 -d` and the sync stops working permanently.**

To create the token:
1. GitHub → **Settings → Developer settings → Personal access tokens**
2. Choose **Fine-grained token** (recommended) or **Tokens (classic)**
3. Fine-grained: set **Repository access** to your fork, grant **Secrets** read/write under repository permissions
4. Classic: grant the `repo` scope
5. Copy the token and add it as the `GH_PAT` repo secret

---

## Setup

### Copy the workflow template

```bash
# In your fork's local clone:
mkdir -p .github/workflows
cp .github/workflows/cron-sync.example.yml .github/workflows/cron-sync.yml
```

Open `cron-sync.yml` and replace `<version>` in the image reference with a real release tag:

```yaml
ghcr.io/keif/yt-sub-playlist:v4.1.0   # pin to the version you want
```

Pinning to a version tag rather than `:latest` means you opt in to upgrades explicitly.

### Optionally adjust the schedule

The default cron fires daily at 06:00 UTC:

```yaml
schedule:
  - cron: "0 6 * * *"
```

Change it to any time that works for you. [crontab.guru](https://crontab.guru) is useful for testing expressions.

### Commit and push

```bash
git add .github/workflows/cron-sync.yml
git commit -m "chore: enable daily sync via Actions cron"
git push
```

GitHub enables the workflow as soon as the file lands on the default branch.

---

## Verification

### Trigger manually

Go to your fork → **Actions → Sync subscriptions** → **Run workflow**.

### Confirm the run succeeded

Click into the run. You should see:

- **Prepare data dir** — exit 0
- **Run sync** — sync output, no `ModuleNotFoundError`, no `401`
- **Reclaim ownership for runner** — exit 0
- **Round-trip refreshed token** — `✓ Set secret TOKEN_B64` (or similar `gh` CLI success output)

### Confirm the token was updated

Fork → **Settings → Secrets and variables → Actions**. The `TOKEN_B64` secret should show an **Updated** timestamp matching the workflow run.

### Confirm a follow-up run works

Wait for the next scheduled run (or trigger another `workflow_dispatch`). If the round-trip succeeded, the new token decodes and the sync completes cleanly. This is the proof that the refresh cycle is healthy.

---

## Re-auth

When the refresh token eventually expires (typically after ~6 months of disuse, or if you revoke access in your Google account), the sync starts failing with a `401` error.

Fix:
1. Re-run the local bootstrap: [docs/deploy/oauth-bootstrap.md](./oauth-bootstrap.md)
2. Re-upload the new `token.json`:
   ```bash
   gh secret set TOKEN_B64 \
     --body "$(base64 < token.json | tr -d '\n')" \
     --repo "<your-fork>"
   ```
3. Trigger a manual run to confirm the new token works.

---

## Troubleshooting

### Sync fails immediately with `base64: invalid input` or similar decode error

The `TOKEN_B64` secret contains a raw (non-base64) value, or it was uploaded with a trailing newline. Re-encode and re-upload:

```bash
base64 < token.json | tr -d '\n'   # copy this output
```

Set the `TOKEN_B64` secret to exactly this string.

### Round-trip step fails: `gh: command not found`

The `ubuntu-latest` runner includes `gh` by default. If the step fails here, check that the `GH_TOKEN` env var is set correctly in the step — it should reference `secrets.GH_PAT`, not `secrets.GITHUB_TOKEN` (the built-in token lacks write access to secrets).

### Missing `GH_PAT` — first refresh worked, subsequent runs fail

Symptom: run 1 syncs successfully, run 2 fails at `base64 -d`. Root cause: the refreshed token was never persisted back to the secret. Fix:
1. Add the `GH_PAT` secret (see [Prerequisites](#prerequisites) above)
2. Re-bootstrap locally and re-upload `TOKEN_B64`
3. Trigger a manual run to verify the round-trip now completes

### Workflow never appears in the Actions tab

The workflow file must live on the **default branch** of your fork. If you pushed to a feature branch, merge it first.

### `ModuleNotFoundError` in sync output

The image tag you specified doesn't match a published release, or the image wasn't pulled successfully. Confirm the tag exists at `ghcr.io/keif/yt-sub-playlist` and that the image reference in your workflow matches exactly.
