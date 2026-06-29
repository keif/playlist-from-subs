#!/bin/sh
# Hydrate env-var-driven secrets to /data so the Python app can read them.
# If a file already exists on disk (bind-mounted or persisted-volume case),
# leave it alone so refreshed tokens survive restarts.

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

    printf '%s' "$var_value" > "$file_path"
    chmod 600 "$file_path"
}

write_secret CLIENT_SECRETS_JSON client_secrets.json
write_secret TOKEN_JSON token.json

exec "$@"
