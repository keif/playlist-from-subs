# Fly.io runbook

Run `yt-sub-playlist` as a daily scheduled machine on Fly.io. The machine wakes
once per day, syncs your playlist, and exits. Fits the Fly.io free tier.

> **No `fly deploy`** — this deploy path uses `fly machine run --schedule`,
> not `fly deploy`. Running `fly deploy` would create a separate always-on
> machine that you would be billed for indefinitely. If you ran it by accident,
> destroy the resulting machine with `fly machine destroy <id>` before
> continuing.

---

## Prerequisites

- A [Fly.io account](https://fly.io) with `flyctl` installed (`brew install flyctl` or see [fly.io/docs/flyctl/install](https://fly.io/docs/flyctl/install/))
- `fly auth login` completed
- `client_secrets.json` and `token.json` on your local machine

  See [docs/deploy/oauth-bootstrap.md](./oauth-bootstrap.md) for the one-time
  Google Cloud + OAuth setup that produces these two files.

---

## Steps

### 1. Create the app

Copy the example config and launch without deploying:

```bash
cp fly.toml.example fly.toml
fly launch --copy-config --no-deploy
```

`fly launch` registers the app name and region from `fly.toml` but does not
create any machines. Edit `fly.toml` first to set your preferred `app` name and
`primary_region`.

### 2. Create the persistent volume

```bash
fly volume create data --size 1
```

This creates a 1 GB volume named `data` in your app's primary region. The
volume persists `client_secrets.json`, `token.json`, and the app's runtime
state (cache, logs) between daily runs.

### 3. Fix volume ownership (one-time)

Fly volumes are created owned by `root`. The container runs as UID 1000 and
the entrypoint shim runs as that non-root user — it cannot write the initial
`client_secrets.json` / `token.json` to a root-owned volume, so the very first
scheduled run would fail before it could authenticate. Chown the volume by
running a throwaway one-shot machine that mounts it and fixes permissions
before the scheduled job ever runs:

```bash
fly machine run \
  --rm \
  --volume data:/data \
  alpine sh -c 'chown -R 1000:1000 /data'
```

`alpine` is used here rather than the project image because the project image
sets `USER app` (UID 1000) at build time — an override like `--entrypoint sh`
on the project image would still execute as the non-root user, and the chown
would fail. The `--rm` flag deletes the helper machine once the chown
completes. The scheduled machine in step 5 then attaches the same volume with
the corrected ownership.

### 4. Upload secrets

Base64-encode both credential files and push them as Fly secrets:

```bash
fly secrets set \
  CLIENT_SECRETS_B64="$(base64 < client_secrets.json)" \
  TOKEN_B64="$(base64 < token.json)"
```

The entrypoint shim decodes these to `/data/client_secrets.json` and
`/data/token.json` on each machine start, but only if the files are not already
present on the volume. After the first run the refreshed `token.json` lives on
the volume and the env-var copy is ignored.

### 5. Schedule the machine

```bash
fly machine run \
  --schedule daily \
  --restart no \
  --volume data:/data \
  ghcr.io/keif/yt-sub-playlist:<version>
```

`--restart no` is important. Without it, Fly defaults to `on-failure` restart,
which means an expired refresh token or a transient API error would put the
machine into a tight retry loop (and possibly burn through your YouTube API
quota) instead of staying stopped until the next daily schedule.

Replace `<version>` with the image tag you want to pin (e.g. `v4.1.0`). See
[releases](https://github.com/keif/yt-sub-playlist/releases) for available
tags. Pinning to a specific version means you opt in to upgrades explicitly.

> The image is published to `ghcr.io/keif/yt-sub-playlist` via issue #13. Until
> that workflow is live, build and push the image manually or use a locally
> pushed image reference.

---

## Verification

**Confirm the scheduled machine registered:**

```bash
fly machine list
```

You should see one machine with state `stopped` and schedule `daily`.

**Watch the first scheduled run:**

```bash
fly logs
```

A successful run ends with the playlist manager logging the number of videos
added and then exiting 0. Look for a line like:

```
Processing complete: N/M videos added successfully
```

That log line is the verification. Fly volumes stay attached to the scheduled
machine even while it is stopped, so a separate throwaway `fly machine run
--volume data:/data ...` cannot mount `data` to inspect it — attempting so
fails with "volume already attached." If the sync log shows successful video
adds AND no `RefreshError` / 401 warnings, the token refresh round-trip
worked. Actual inspection of `/data` requires destroying and recreating the
scheduled machine (see the re-auth section for that pattern).

---

## Re-authentication

OAuth refresh tokens can expire after months of disuse or when your GCP
project's OAuth policy changes. When the sync starts failing with `401
Unauthorized` or `invalid_grant`, the refresh token has expired.

Re-auth is the same local bootstrap flow repeated:

1. On your laptop, re-run the OAuth flow:

   ```bash
   uv run python -m yt_sub_playlist.auth.oauth
   ```

   A browser window opens for you to re-authorize. This overwrites `token.json`
   locally.

2. Upload the new token:

   ```bash
   fly secrets set TOKEN_B64="$(base64 < token.json)"
   ```

3. Remove the stale token from the volume and rebuild the scheduled machine.
   The entrypoint shim writes the env-var token to `/data/token.json` only if
   the file does not exist, so the old token has to go first. Fly attaches
   the volume exclusively to the scheduled machine (even when stopped), so
   you have to destroy that machine before a throwaway can mount the volume:

   ```bash
   # Find the scheduled machine's ID:
   fly machine list

   # Destroy it. The volume detaches automatically.
   fly machine destroy <machine-id>

   # Use a throwaway alpine to remove the stale token file.
   fly machine run \
     --rm \
     --volume data:/data \
     alpine sh -c 'rm -f /data/token.json'

   # Recreate the scheduled machine (same command as step 5). The entrypoint
   # will hydrate the new TOKEN_B64 secret into /data/token.json on next
   # scheduled start.
   fly machine run \
     --schedule daily \
     --restart no \
     --volume data:/data \
     ghcr.io/keif/yt-sub-playlist:<version>
   ```
