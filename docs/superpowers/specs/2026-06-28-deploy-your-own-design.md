# Deploy-Your-Own — Design Spec

**Date:** 2026-06-28
**Status:** Approved

## Summary

Make `yt-sub-playlist` reusable by others without turning it into a SaaS. Ship a single Docker image, three documented deploy paths (Fly.io, GitHub Actions cron, raw Docker / VPS), and a shared OAuth-bootstrap doc. Each user brings their own Google Cloud project, OAuth client, and YouTube API quota — there is no central infrastructure to operate and no token-trust handoff.

## Goals

- A user can go from "saw this repo" to "running a daily YouTube sync on their own infra" in under an hour, picking the deploy target that matches their constraints.
- The published Docker image (`ghcr.io/keif/yt-sub-playlist:<version>`) is the unit of distribution. Build-from-source remains supported as a fallback.
- The OAuth bootstrap is a one-time act on the user's laptop. Re-auth (when refresh tokens fail) is the same act repeated. No headless OAuth code path to maintain.
- The Flask dashboard is explicitly **local-only** in v1. The runbooks document Tailscale / Cloudflare Access as the path to reach it remotely.

## Non-goals

- Multi-tenant SaaS. No shared quota, no central token storage, no user accounts.
- OAuth device flow or web-callback rework. A future spec can add it if user demand surfaces.
- A public-internet dashboard. The Flask app has no auth and is not in v1 deploy scope.
- Automated re-auth. Token refresh failures require a manual local bootstrap + secrets re-upload.
- Backup / disaster recovery for the user's `token.json`, `config.json`, or `data/`. Out of scope; mentioned in docs but not solved.

## Why this shape

YouTube Data API v3 quota is 10k units/day per *application*, not per user. A SaaS would hit the cap with a few hundred users and would need a Google-granted increase that is unlikely for a tool wrapping native YouTube functionality. Local-per-person sidesteps the quota cap, the OAuth verification process, the trust-handoff of users granting a third-party access to their YouTube account, and the operational burden of running shared infrastructure.

## Architecture

```
                       ┌─────────────────────────────┐
                       │  ghcr.io/keif/              │
                       │   yt-sub-playlist:<version> │  ← built + pushed by GHA on v* tag
                       └──────────────┬──────────────┘
                                      │ pulled by
            ┌─────────────────────────┼──────────────────────────┐
            ▼                         ▼                          ▼
    Fly.io machine             GitHub Actions cron        Raw Docker / VPS
    (scheduled-machines)       (workflow_dispatch +       (docker compose +
                                schedule trigger)         host cron / systemd)
```

**One image, one entrypoint.** `ENTRYPOINT ["python", "-m", "yt_sub_playlist"]` with the cron sync as the default `CMD`. The dashboard is launchable via `CMD ["python", "-m", "yt_sub_playlist.dashboard"]` for users who want it, but v1 documentation does not recommend exposing it publicly.

**Entrypoint shim** unifies env-var-driven and file-mounted secrets handling. If `CLIENT_SECRETS_B64` and `TOKEN_B64` env vars are set, the shim base64-decodes them to `/data/*.json` before launching the CLI. If the files already exist (raw Docker bind mount, or persisted Fly volume after first run), the shim leaves them alone. No code branching in the Python app.

Both secrets are base64-encoded by contract. `token.json` despite its name is a binary credentials serialization (not JSON), so raw env vars would corrupt it on NUL bytes; `client_secrets.json` is genuine JSON and would survive raw transit, but encoding both keeps the contract consistent. A follow-up spec should migrate the project's token format to JSON (via `google.oauth2.credentials.Credentials.to_json()`); doing so would let users skip the base64 step but requires existing users to re-bootstrap their `token.json`. Out of scope for v1.

## Files added to the repo

| Path | Purpose |
|---|---|
| `Dockerfile` | Python 3.11-slim base + uv + `uv sync --no-dev`. Entry point and CMD as described above. |
| `.dockerignore` | Exclude `.venv/`, `venv/`, `node_modules/`, `_notes/`, `reports/`, `secrets/`, `data/`, `logs/`, `client_secrets.json`, `token.json`. |
| `docker/entrypoint.sh` | Shim that hydrates env-var secrets to `/data/`, then `exec "$@"`. |
| `docker-compose.yml` | Raw Docker target: `sync` service with mounts, commented-out `dashboard` service. |
| `fly.toml.example` | Fly.io machine config: 256MB shared-cpu-1x, `/data` volume, image pin, secrets references. |
| `.github/workflows/docker-publish.yml` | Build + push to `ghcr.io` on `v*` tag (matches existing `standard-version` tag pattern). |
| `.github/workflows/cron-sync.example.yml` | Template the user copies into their fork to enable the Actions cron path. |
| `docs/DEPLOY.md` | Index. "Pick a target" decision tree linking the three runbooks. |
| `docs/deploy/oauth-bootstrap.md` | Shared GCP + OAuth + `token.json` setup. Linked from every runbook. |
| `docs/deploy/fly.md` | Fly.io runbook. |
| `docs/deploy/github-actions.md` | GitHub Actions cron runbook (with the `GH_PAT` footgun documented prominently). |
| `docs/deploy/docker.md` | Raw Docker / VPS runbook. |
| `README.md` | Add "Deploy your own" section linking `docs/DEPLOY.md`. |

## Secrets handling per target

The shared bootstrap produces two files: `client_secrets.json` (from GCP) and `token.json` (from running `uv run python -m yt_sub_playlist.auth.oauth` on the user's laptop). Both files are now what gets pushed to the chosen target.

| Target | `client_secrets.json` | `token.json` | Refresh persistence |
|---|---|---|---|
| **Fly.io** | `fly secrets set CLIENT_SECRETS_B64="$(base64 < client_secrets.json)"` | `fly secrets set TOKEN_B64="$(base64 < token.json)"` | Volume mount at `/data`. Refreshed `token.json` is written back to disk, survives machine restarts. |
| **GitHub Actions** | Repo secret `CLIENT_SECRETS_B64` | Repo secret `TOKEN_B64` | Workflow round-trips via `gh secret set TOKEN_B64` using a `GH_PAT` (`repo` scope) stored as a third secret. **Without `GH_PAT`, the token works once and then expires permanently.** Documented as the path's primary footgun. |
| **Raw Docker / VPS** | `./data/client_secrets.json` (in the bind-mounted data dir) | `./data/token.json` (in the bind-mounted data dir) | Native filesystem. Refreshed token persists via the bind mount. |

The GitHub Actions round-trip is the one piece of friction that doesn't have a clean alternative. Considered and rejected: committing the refreshed token back to a private repo file (worse than encrypted-at-rest secrets, even if the repo is private).

## Deploy paths

### Path 1: Fly.io (recommended default)

```bash
fly launch --copy-config --no-deploy        # uses fly.toml.example, creates the app only
fly volume create data --size 1
fly secrets set CLIENT_SECRETS_B64="$(base64 < client_secrets.json)" \
                TOKEN_B64="$(base64 < token.json)"
fly machine run --schedule daily \
   --volume data:/data \
   ghcr.io/keif/yt-sub-playlist:<version>
```

Fits the free tier. Note the absence of `fly deploy` — a scheduled machine is the entire compute footprint; running `fly deploy` would create a separate always-on machine the user would be billed for. `fly.toml.example` is the app-level config (name, region, volume declaration); the schedule and image pin live on the machine.

### Path 2: GitHub Actions cron

User forks the repo, copies `cron-sync.example.yml` to `.github/workflows/cron-sync.yml`, sets three repo secrets (`CLIENT_SECRETS_B64`, `TOKEN_B64`, `GH_PAT`). Workflow runs on cron + `workflow_dispatch`, pulls the published image, runs the sync, round-trips the refreshed token back into repo secrets.

```yaml
on:
  schedule: [{ cron: "0 6 * * *" }]
  workflow_dispatch:
jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - name: Prepare data dir
        # The container runs as UID 1000 (non-root). The runner creates the
        # workspace as a different user, so chmod before mounting.
        run: |
          mkdir -p ${{ github.workspace }}/data
          sudo chown -R 1000:1000 ${{ github.workspace }}/data
      - name: Run sync
        run: |
          docker run --rm \
            -v ${{ github.workspace }}/data:/data \
            -e CLIENT_SECRETS_B64="${{ secrets.CLIENT_SECRETS_B64 }}" \
            -e TOKEN_B64="${{ secrets.TOKEN_B64 }}" \
            ghcr.io/keif/yt-sub-playlist:<version>
      - name: Reclaim ownership for runner
        # The container's UID 1000 wrote the refreshed token; the round-trip
        # step runs as the runner user and needs to read it.
        run: sudo chown -R $(id -u):$(id -g) ${{ github.workspace }}/data
      - name: Round-trip refreshed token
        env: { GH_TOKEN: ${{ secrets.GH_PAT }} }
        run: |
          gh secret set TOKEN_B64 \
            --body "$(base64 < ${{ github.workspace }}/data/token.json | tr -d '\n')" \
            --repo "$GITHUB_REPOSITORY"
```

Free if the user is OK with running on Microsoft infra. Runbook is explicit about `GH_PAT`.

Note the explicit `docker run` (not `uses: docker://...`) so the workflow controls the volume mount — the refreshed `token.json` needs to land on the runner's filesystem so the round-trip step can read it. The round-trip step re-encodes the binary token as base64 before writing it back to the secret; without that, the next run's entrypoint would fail at `base64 -d`.

### Path 3: Raw Docker / VPS

```bash
mkdir -p ./data
chmod 700 ./data
cp /path/to/client_secrets.json ./data/
cp /path/to/token.json ./data/
docker compose pull        # or `docker compose build` for build-from-source
# Then trigger via host cron or systemd timer:
docker compose run --rm sync
```

`docker-compose.yml` defines a one-shot `sync` service with a single `./data:/data` bind mount. Both `client_secrets.json` and `token.json` live in `./data/` alongside the app's runtime state (cache, API log). Host cron / systemd handles scheduling — there is no `restart` policy because the container exits after each sync.

## OAuth bootstrap

Documented once in `docs/deploy/oauth-bootstrap.md`, linked from every runbook.

1. **GCP project** — Create one. Enable YouTube Data API v3.
2. **OAuth consent screen** — External + Testing mode. Add your own Google account as a test user. (Testing mode = 100-user cap, no Google verification needed. Perfect for deploy-your-own.)
3. **OAuth client** — Type: Desktop. Download `client_secrets.json`.
4. **Local bootstrap** — From a repo clone on your laptop: `uv run python -m yt_sub_playlist.auth.oauth`. Produces `token.json`.

Re-auth (months later when the refresh token fails) is the same flow, repeated.

## Image publishing

`.github/workflows/docker-publish.yml` triggers on `v*` tag push (matches `standard-version`'s existing tagging behavior, so no extra release-process steps). Builds the image, tags both `:<version>` and `:latest`, pushes to `ghcr.io/keif/yt-sub-playlist`.

The image is public. Pinning to `:<version>` rather than `:latest` is the recommendation in all three runbooks so users opt in to upgrades explicitly.

## Verification

Each runbook ends with a verification block:

- Confirm a sync run completes with no `ModuleNotFoundError`.
- Confirm `data/` (or the platform's persistence layer) shows updated state.
- Confirm a follow-up run uses the rotated `token.json` (i.e., refresh worked).

## Risks & mitigations

- **GitHub Actions `GH_PAT` footgun.** The workflow fails closed on first refresh if the secret is missing. Mitigation: runbook puts this in the prereq checklist, not buried in troubleshooting.
- **Token expiry while user is on vacation.** Refresh tokens can expire after ~6 months of disuse or when the OAuth client's policy changes. Mitigation: document expected re-auth cadence and the symptom (sync starts failing with 401). No code mitigation in v1.
- **GCP project quota exhaustion.** Even a single user can hit 10k/day if they sync many times. Mitigation: existing quota-tracking + the project's batched API design already minimize this. Documented as "if you hit quota, request an increase from Google or reduce sync frequency."
- **Image consumers pinning `:latest`.** Surprises on upgrade. Mitigation: docs steer toward `:<version>` pins explicitly.
- **`fly.toml.example` drifts from Fly's evolving config schema.** Mitigation: keep the example minimal (size, volume, image, secrets) and link to Fly's current docs for the rest.

## Implementation chunks (input to issue generation)

Each chunk is sized to produce a working, testable deliverable. Roughly ordered by dependency.

1. **`Dockerfile` + `.dockerignore` + entrypoint shim.** Image builds, runs, and writes env-var secrets to disk. Smoke test: `docker run -e CLIENT_SECRETS_B64=... -e TOKEN_B64=... <image> --help` prints CLI help.
2. **`docker-compose.yml`.** Raw Docker path works end-to-end against a locally-built image. Verification: `docker compose run --rm sync --dry-run` succeeds.
3. **`.github/workflows/docker-publish.yml`.** Image publishes to ghcr.io on `v*` tag. Verification: tag a test version, confirm the image appears at the expected URL.
4. **`fly.toml.example` + `docs/deploy/fly.md`.** Fly path documented and tested by the maintainer at least once.
5. **`.github/workflows/cron-sync.example.yml` + `docs/deploy/github-actions.md`.** Actions path documented. `GH_PAT` setup is in the prereq section, not in troubleshooting.
6. **`docs/deploy/docker.md`.** Raw Docker / VPS path documented.
7. **`docs/deploy/oauth-bootstrap.md` + `docs/DEPLOY.md` + README link.** Index + shared bootstrap doc + entry point. Closes the loop.

## Out of scope (v1) — explicit

- Multi-tenant SaaS path.
- OAuth device flow (`--device-flow`) or web-callback rework.
- Public-internet dashboard deploy. v1 documents Tailscale / Cloudflare Access as the recommended pattern; a future spec can add a built-in auth layer or a separate dashboard-deploy spec.
- Backups for user-owned files (`token.json`, `config.json`, `data/`).
- Image signing / SBOM. Worth doing later but doesn't block v1.

## Follow-up specs (likely candidates)

- Dashboard deploy with built-in auth (basic auth toggle, or Tailscale-only mode docs).
- OAuth device flow for less painful headless re-auth.
- Multi-arch image builds (arm64 alongside amd64) once a real user asks.
