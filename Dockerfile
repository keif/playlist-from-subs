# syntax=docker/dockerfile:1.7

# --- builder ---------------------------------------------------------------
# Resolves and installs the project into /app/.venv using `uv`. The final
# stage copies the venv but not `uv` itself, keeping the runtime image lean.
FROM python:3.11-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app

# Layer 1: resolve and install dependencies only. Cached unless uv.lock changes.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Layer 2: install the project itself. LICENSE and README.md are referenced by
# pyproject.toml ([project].license and [project].readme), so hatchling needs
# them present at build time.
COPY LICENSE README.md ./
COPY yt_sub_playlist ./yt_sub_playlist
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# --- runtime ---------------------------------------------------------------
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

# Non-root user. UID 1000 is conventional and matches typical desktop bind
# mounts. Fly volumes are root-owned at creation — see docs/deploy/fly.md
# for the one-time `fly ssh console` chown step.
RUN groupadd --system --gid 1000 app \
    && useradd --system --uid 1000 --gid app --shell /usr/sbin/nologin --home /app app

WORKDIR /app
COPY --from=builder --chown=app:app /app /app

COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# /data is where client_secrets.json and token.json live at runtime. Platforms
# either bind-mount it (raw Docker) or attach a volume (Fly). For ephemeral
# runs (GitHub Actions) the shim writes the env-var secrets here on startup.
RUN mkdir -p /data && chown app:app /data
WORKDIR /data
VOLUME ["/data"]

USER app

# ENTRYPOINT bakes in the CLI invocation so `docker run <image> --help` works.
# Override --entrypoint to launch the dashboard or any other module.
ENTRYPOINT ["/usr/local/bin/entrypoint.sh", "yt-sub-playlist"]
