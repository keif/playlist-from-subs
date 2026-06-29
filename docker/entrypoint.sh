#!/bin/sh
# Hydrate base64-encoded secrets from env vars to /data so the Python app can
# read them. If a file already exists on disk (bind-mounted or persisted-volume
# case), leave it alone so refreshed tokens survive restarts.
#
# Base64 is used because `token.json` is actually a binary credentials
# serialization (not JSON), despite the filename. Raw env vars would corrupt
# binary content with NUL bytes. `client_secrets.json` is genuine JSON and
# would survive raw transit, but we base64 both so the contract is consistent.
#
# Encode files on the user's laptop with: base64 -w0 < token.json
# (macOS: `base64 < token.json | tr -d '\n'`)

set -eu

DATA_DIR="${YT_SUB_PLAYLIST_DATA_DIR:-/data}"

write_secret() {
    var_name="$1"
    file_name="$2"
    file_path="$DATA_DIR/$file_name"

    eval "var_value=\${$var_name:-}"

    if [ -z "$var_value" ]; then
        return 0
    fi

    if [ -f "$file_path" ]; then
        return 0
    fi

    printf '%s' "$var_value" | base64 -d > "$file_path"
    chmod 600 "$file_path"
}

write_secret CLIENT_SECRETS_B64 client_secrets.json
write_secret TOKEN_B64 token.json

# The app reads client_secrets.json / token.json as relative paths. The image's
# WORKDIR is /data, but platforms like GitHub Actions (`uses: docker://...`)
# override the container's working directory to the runner's checkout. Force
# cwd to the secrets directory so the CLI's relative reads find the hydrated
# files regardless of how the container was invoked.
cd "$DATA_DIR"

exec "$@"
