# OAuth Bootstrap

One-time setup required before any deploy path. You'll end up with two files:

- `client_secrets.json` — your GCP OAuth client credentials
- `token.json` — a serialized credential object with access + refresh tokens

Both files go to your deploy target. How they get there (env vars, bind mounts, fly secrets) is covered in the target-specific runbooks. This doc covers getting them.

---

## 1. Create a Google Cloud project

Visit [https://console.cloud.google.com](https://console.cloud.google.com).

Top nav → project picker → **New Project**. Name it whatever — `yt-sub-playlist` works. Note the project ID; you'll need it if you ever want to manage quota via the CLI.

---

## 2. Enable YouTube Data API v3

With your project selected:

**APIs & Services → Library → search "YouTube Data API v3" → Enable.**

---

## 3. Configure the OAuth consent screen

**APIs & Services → OAuth consent screen.**

- **User type: External.** Choose this even for personal use. "Internal" requires a Google Workspace organization. External with Testing status is the right choice for self-hosted deployments.
- Fill in the required fields (app name, support email). The values don't matter — this screen is only shown to you.
- **Scopes:** skip for now — the app requests scopes at runtime.
- **Test users:** add your own Google account email. This is the account you'll authorize in step 5.

**Publishing status: leave it as Testing.** Testing mode caps the app at 100 authorized users and skips Google's OAuth verification process entirely — no review queue, no branding review, no wait. Since you're the only user (you are the test user you just added), this is the correct configuration. Do not click "Publish" — that triggers the verification process and offers nothing in return for a personal deployment.

---

## 4. Create an OAuth 2.0 client

**APIs & Services → Credentials → Create Credentials → OAuth client ID.**

- **Application type: Desktop app.** Not "Web application" — the local browser flow used by the bootstrap script requires Desktop type.
- Name it anything.

After creation, click **Download JSON**. Rename the downloaded file to `client_secrets.json`.

---

## 5. Run the local bootstrap

You need the repo on your laptop and `uv` installed ([https://docs.astral.sh/uv/](https://docs.astral.sh/uv/)).

```bash
git clone https://github.com/keif/yt-sub-playlist.git
cd yt-sub-playlist
uv sync
```

Place `client_secrets.json` at the repo root (the same directory as `pyproject.toml`):

```bash
mv ~/Downloads/client_secrets.json .
```

Run the auth bootstrap:

```bash
uv run python -m yt_sub_playlist.auth.oauth
```

A browser window opens to Google's consent screen. Sign in with the test user account you added in step 3. Grant the requested YouTube permissions. The browser will show a "The authentication flow has completed" page — you can close it.

Back in the terminal you'll see:

```
Authentication successful for channel: <your channel name>
```

A `token.json` file is now written to the repo root.

---

## 6. What you have

Two files at the repo root:

```
client_secrets.json   ← OAuth client ID + secret (from GCP)
token.json            ← serialized access + refresh token (from step 5)
```

**Do not commit either file.** Both are in `.gitignore`. The deploy runbooks walk you through uploading them to your chosen target.

---

## 7. Encoding for env-var targets

Fly.io and GitHub Actions store these as secrets via environment variables. `token.json` despite its `.json` extension is a binary credentials serialization — raw env-var transit corrupts it on binary content. Both files are base64-encoded by convention so the contract is consistent.

When a runbook tells you to set a secret, use:

```bash
base64 < client_secrets.json
base64 < token.json
```

The deploy target's entrypoint shim decodes them back to disk before the app starts.

> Raw Docker / VPS: you copy the files directly into the bind-mounted data directory — no base64 needed. See `docs/deploy/docker.md`.

---

## 8. Re-auth when tokens expire

Google revokes refresh tokens after approximately 6 months of inactivity, or when the OAuth client configuration changes. When this happens, syncs start failing with `RefreshError` or HTTP 401.

To recover:

1. On your laptop, in the repo clone from step 5:
   ```bash
   rm token.json
   uv run python -m yt_sub_playlist.auth.oauth
   ```
2. Complete the consent flow again (same browser step as above).
3. Re-upload the new `token.json` to your deploy target per that target's runbook (re-encode with `base64 < token.json` first if the target uses env-var secrets).

The re-auth process is identical to the initial bootstrap. No GCP changes needed — the OAuth client and consent screen configuration persist.
