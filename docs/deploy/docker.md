# Raw Docker / VPS Runbook

Self-host `yt-sub-playlist` on any Linux VPS (or local machine) with Docker installed. The sync job runs as a one-shot container triggered by host cron or a systemd timer. No daemon, no restart policy.

---

## Prerequisites

- **Docker 24+** (ships Compose v2 as `docker compose`). Check: `docker compose version`.
- `make` — optional shortcut layer; not required.
- A checkout of this repo on the server (or at least `docker-compose.yml` and `Dockerfile`):
  ```bash
  git clone https://github.com/keif/yt-sub-playlist.git /srv/yt-sub-playlist
  cd /srv/yt-sub-playlist
  ```

**OAuth credentials** — complete the one-time bootstrap on your laptop first:  
→ [docs/deploy/oauth-bootstrap.md](./oauth-bootstrap.md)

That process produces `client_secrets.json` and `token.json`. You will copy both to the server in the Setup section below.

---

## Setup

### Directory layout

All credentials and runtime state live in `./data/`. The compose file mounts it as `./data:/data`. The container writes the refreshed `token.json` back to this directory on every run, so it must be writable by the container's UID.

```
/srv/yt-sub-playlist/
├── docker-compose.yml
├── Dockerfile
└── data/                  ← bind-mounted at /data inside the container
    ├── client_secrets.json
    ├── token.json
    ├── config.json        (optional)
    ├── .env               (optional)
    └── ...                (runtime: processed_videos.json, playlist_cache/, api_call_log.json)
```

### Create and lock down the data directory

```bash
mkdir -p ./data

# Linux hosts: the container runs as UID 1000. Give that UID write access.
# macOS Docker Desktop / OrbStack: UID translation is handled automatically —
# you can skip the chown step, but it won't hurt to run it.
sudo chown -R 1000:1000 ./data

# Restrict access — this directory holds a live OAuth refresh token.
chmod 700 ./data
```

### Drop credentials into ./data/

```bash
# From your laptop (adjust paths):
scp /path/to/client_secrets.json user@your-server:/srv/yt-sub-playlist/data/
scp /path/to/token.json          user@your-server:/srv/yt-sub-playlist/data/
```

### Optional: app configuration

The entrypoint forces the container's working directory to `/data`, so the app reads `config.json` and `.env` from that directory automatically. Drop them in if you want to override defaults (playlist name, duration filters, lookback window, etc.):

```bash
scp /path/to/config.json user@your-server:/srv/yt-sub-playlist/data/   # optional
scp /path/to/.env        user@your-server:/srv/yt-sub-playlist/data/   # optional
```

See the [README](../../README.md) for the full list of supported env vars and config keys.

---

## Build vs. pull

### Now: build locally

Image publishing to `ghcr.io` is in-flight (#13). Until it lands, build the image from source:

```bash
docker compose build
```

### Later: pull from ghcr.io

Once #13 ships, swap the compose file's `build: .` for an image pin and pull instead of building:

1. In `docker-compose.yml`, replace:
   ```yaml
   services:
     sync:
       build: .
       image: yt-sub-playlist:local
   ```
   with:
   ```yaml
   services:
     sync:
       image: ghcr.io/keif/yt-sub-playlist:<version>
   ```
2. Pull the published image:
   ```bash
   docker compose pull
   ```

Pin to a specific version tag rather than `:latest` so you opt in to upgrades explicitly.

---

## Verification: first run

Do a dry run before scheduling anything:

```bash
docker compose run --rm sync --dry-run
```

Expected: the sync logic runs, no videos are added to the playlist, no errors. If you see `ModuleNotFoundError` or a credentials failure, check that both JSON files landed in `./data/` with correct permissions.

---

## Scheduling

The `sync` service is intentionally one-shot — no `restart` policy. Pick whichever scheduler fits your server.

### Option A: host cron

```bash
crontab -e
```

Add a line (runs daily at 06:00):

```cron
0 6 * * *  cd /srv/yt-sub-playlist && /usr/bin/docker compose run --rm sync >> /var/log/yt-sub-playlist.log 2>&1
```

Use the full path to `docker` (`which docker`) if your cron environment doesn't include it.

### Option B: systemd timer

Create two unit files. Replace `/srv/yt-sub-playlist` with your actual checkout path.

**/etc/systemd/system/yt-sub-playlist-sync.service**

```ini
[Unit]
Description=yt-sub-playlist sync
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
WorkingDirectory=/srv/yt-sub-playlist
ExecStart=/usr/bin/docker compose run --rm sync
StandardOutput=journal
StandardError=journal
```

**/etc/systemd/system/yt-sub-playlist-sync.timer**

```ini
[Unit]
Description=Run yt-sub-playlist sync daily at 06:00

[Timer]
OnCalendar=*-*-* 06:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now yt-sub-playlist-sync.timer

# Verify the timer is active:
systemctl list-timers yt-sub-playlist-sync.timer

# Trigger a manual run immediately (bypasses the timer schedule):
sudo systemctl start yt-sub-playlist-sync.service
```

**Note:** cron *inside* the container is out of scope. The container exits after each sync; scheduling is the host's job.

---

## Logs

- **Host cron path:** logs land in whatever file you redirect to (the example above uses `/var/log/yt-sub-playlist.log`). Rotate with `logrotate` if needed.
- **systemd timer path:** logs go to the journal. Read them with:
  ```bash
  journalctl -u yt-sub-playlist-sync.service
  journalctl -u yt-sub-playlist-sync.service --since "1 hour ago"
  ```

After a real run (not `--dry-run`), confirm the token was refreshed:

```bash
# The mtime should reflect the most recent run:
ls -la ./data/token.json
```

If the mtime updates, the OAuth refresh cycle is working and the token will continue to be renewed on each run.

---

## Dashboard

The dashboard is **out of scope for v1** on raw Docker. It is intentionally commented out of `docker-compose.yml`.

Recommended pattern for accessing server state locally:

1. Mount the server's `./data/` directory to your laptop via **sshfs** or **Tailscale**:
   ```bash
   sshfs user@your-server:/srv/yt-sub-playlist/data /mnt/yt-data
   ```
2. Run the dashboard locally, pointed at the mounted directory:
   ```bash
   cd dashboard/backend
   YT_SUB_PLAYLIST_DATA_DIR=/mnt/yt-data uv run python app.py
   # Open http://localhost:5001
   ```

A future spec will cover dashboard deploy with a proper auth layer.

---

## Re-authentication

Google refresh tokens can expire after roughly **6 months of disuse** or if the OAuth client's policy changes. When the sync starts failing with a `401` / `invalid_grant` error, you need to re-run the OAuth bootstrap.

1. On your laptop, re-run the bootstrap to produce a fresh `token.json`:
   ```bash
   uv run python -m yt_sub_playlist.auth.oauth
   ```
   See [docs/deploy/oauth-bootstrap.md](./oauth-bootstrap.md) for the full flow.

2. Copy the new token to the server:
   ```bash
   scp /path/to/token.json user@your-server:/srv/yt-sub-playlist/data/
   ```
   Or using rsync:
   ```bash
   rsync -av /path/to/token.json user@your-server:/srv/yt-sub-playlist/data/
   ```

3. If a sync container is currently running, stop it:
   ```bash
   docker stop yt-sub-playlist-sync
   ```
   The next scheduled run will pick up the new token automatically.

Re-auth is also required if you rotate your GCP OAuth client credentials — in that case replace both `client_secrets.json` and `token.json`.
