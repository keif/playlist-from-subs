# Deploy Your Own

`yt-sub-playlist` is intentionally not a hosted SaaS. Each user brings their own
Google Cloud project, OAuth client, and YouTube API quota. There is no central
infrastructure, no shared token store, no trust handoff. The tradeoff: you run
it yourself.

If you can put up with that, you get:

- A daily YouTube subscription sync running on your own infrastructure.
- Your own 10k-units-per-day YouTube API quota (not shared with other users).
- Full control over your OAuth credentials — nothing crosses a third-party server.

This document is an index. Every deploy path shares the same OAuth setup, then
diverges on where the daily cron actually runs.

## Step zero, no matter which path

Complete the shared OAuth bootstrap on your laptop: [`docs/deploy/oauth-bootstrap.md`](./deploy/oauth-bootstrap.md).

That produces two files, `client_secrets.json` and `token.json`, which every
deploy path uploads to its target.

## Pick your target

| Target | Runbook | Best if you… | Watch out for… |
|---|---|---|---|
| **Fly.io** | [`docs/deploy/fly.md`](./deploy/fly.md) | want it to Just Work with the least platform gymnastics. Fly's scheduled machines fit a cron job cleanly and the free tier covers it. | Fly volumes attach exclusively to a machine, so re-auth involves destroying and recreating the scheduled machine. |
| **GitHub Actions cron** | [`docs/deploy/github-actions.md`](./deploy/github-actions.md) | want it free (running on Microsoft's infrastructure) and are OK with a small GitHub Personal Access Token dance for the refresh-token round-trip. | Without the `GH_PAT` secret, the workflow works once and then permanently breaks after the first OAuth refresh. The runbook is emphatic. |
| **Raw Docker / VPS** | [`docs/deploy/docker.md`](./deploy/docker.md) | already have a Linux VPS and want the fewest platform-specific concepts. Works with host cron or systemd timers. | The most UID-1000 file-permission edge cases. Linux hosts where your login user is not UID 1000 need `sudo chown` before the container can read the mounted `./data/` directory. |

There is deliberately no wrong answer — pick whichever one you would rather
debug at 11 PM when something is broken.

## What is not in scope for v1

- **The Flask dashboard.** The image ships the CLI only. The dashboard runs
  locally with `uv run`. A future spec will cover dashboard deploy with an
  auth layer.
- **Multi-user SaaS.** Not happening in this repo. Each user brings their own
  everything.
- **Automated re-auth.** Refresh tokens expire; when they do, the runbooks
  describe a manual re-auth flow. If you want automation, a monitoring hook
  and a scripted re-auth are exercises for the reader.

## Design spec

The reasoning behind the shape of all of this lives in
[`docs/superpowers/specs/2026-06-28-deploy-your-own-design.md`](./superpowers/specs/2026-06-28-deploy-your-own-design.md).
Read it if you want to understand why the API quota drove us away from a hosted
model, or why the token is base64-encoded through env vars.
