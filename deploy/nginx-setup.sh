#!/usr/bin/env bash
# Render the PlacePix nginx vhost from a template, substituting the domain and
# the port the app actually listens on.
#
# The port is read from the deployment's .env (PORT, falling back to the port in
# HOST, then 3000), so nginx and the container can never disagree.
#
# Usage:
#   ./deploy/nginx-setup.sh --domain placepix.net                 # print to stdout
#   ./deploy/nginx-setup.sh --domain placepix.net --bootstrap     # HTTP-only (pre-certbot)
#   ./deploy/nginx-setup.sh --domain placepix.net --install       # write, test, reload
#
# Options:
#   --domain NAME    Domain to serve (default: $(hostname))
#   --port N         Override the port discovered from .env
#   --env-file PATH  .env to read PORT from (default: /opt/placepix/.env, then ./.env)
#   --bootstrap      Render the HTTP-only template used before certificates exist
#   --install        Write to sites-available, enable it, run nginx -t, reload
#   --output PATH    Write here instead of /etc/nginx/sites-available/placepix

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

DOMAIN=""
PORT_OVERRIDE=""
ENV_FILE=""
BOOTSTRAP=false
INSTALL=false
OUTPUT=""

die() { echo "[placepix] ERROR: $*" >&2; exit 1; }
log() { echo "[placepix] $*"; }

while [[ $# -gt 0 ]]; do
    case "$1" in
        --domain)   DOMAIN="${2:-}"; shift 2 ;;
        --port)     PORT_OVERRIDE="${2:-}"; shift 2 ;;
        --env-file) ENV_FILE="${2:-}"; shift 2 ;;
        --output)   OUTPUT="${2:-}"; shift 2 ;;
        --bootstrap) BOOTSTRAP=true; shift ;;
        --install)  INSTALL=true; shift ;;
        -h|--help)  sed -n '2,25p' "$0" | sed 's/^# \?//'; exit 0 ;;
        *)          die "Unknown option: $1" ;;
    esac
done

# ── Domain ──────────────────────────────────────────────────────────
DOMAIN="${DOMAIN:-$(hostname)}"
[[ -n "$DOMAIN" ]] || die "Could not determine a domain; pass --domain NAME"

# ── Port: --port > .env PORT > .env HOST > 3000 ─────────────────────
if [[ -z "$ENV_FILE" ]]; then
    for candidate in /opt/placepix/.env "$SCRIPT_DIR/../.env"; do
        [[ -f "$candidate" ]] && { ENV_FILE="$candidate"; break; }
    done
fi

PORT=""
if [[ -n "$PORT_OVERRIDE" ]]; then
    PORT="$PORT_OVERRIDE"
elif [[ -n "$ENV_FILE" && -f "$ENV_FILE" ]]; then
    PORT=$(grep -E '^[[:space:]]*PORT=' "$ENV_FILE" 2>/dev/null | tail -n 1 | cut -d '=' -f2 | tr -d '[:space:]"' || true)
    if [[ -z "$PORT" ]]; then
        # Fall back to the port carried by HOST=addr:port
        HOST_LINE=$(grep -E '^[[:space:]]*HOST=' "$ENV_FILE" 2>/dev/null | tail -n 1 | cut -d '=' -f2 | tr -d '[:space:]"' || true)
        [[ "$HOST_LINE" == *:* ]] && PORT="${HOST_LINE##*:}"
    fi
    [[ -n "$PORT" ]] && log "Read port $PORT from $ENV_FILE"
fi
PORT="${PORT:-3000}"

case "$PORT" in
    ''|*[!0-9]*) die "Resolved port '$PORT' is not numeric" ;;
esac
(( PORT > 0 && PORT < 65536 )) || die "Port $PORT is out of range"

# ── Render ──────────────────────────────────────────────────────────
if [[ "$BOOTSTRAP" == true ]]; then
    TEMPLATE="$SCRIPT_DIR/nginx-bootstrap.conf.template"
else
    TEMPLATE="$SCRIPT_DIR/nginx-placepix.conf.template"
fi
[[ -f "$TEMPLATE" ]] || die "Template not found: $TEMPLATE"

RENDERED=$(sed -e "s|__DOMAIN__|$DOMAIN|g" -e "s|__PORT__|$PORT|g" "$TEMPLATE")

if grep -q '__DOMAIN__\|__PORT__' <<<"$RENDERED"; then
    die "Template still contains unsubstituted placeholders"
fi

if [[ "$INSTALL" != true ]]; then
    if [[ -n "$OUTPUT" ]]; then
        printf '%s\n' "$RENDERED" > "$OUTPUT"
        log "Wrote $OUTPUT (domain: $DOMAIN, port: $PORT)"
    else
        printf '%s\n' "$RENDERED"
    fi
    exit 0
fi

# ── Install ─────────────────────────────────────────────────────────
TARGET="${OUTPUT:-/etc/nginx/sites-available/placepix}"
SUDO=""
[[ -w "$(dirname "$TARGET")" ]] || SUDO="sudo"

if [[ ! "$BOOTSTRAP" == true ]]; then
    CERT="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
    if [[ ! -f "$CERT" ]]; then
        die "No certificate at $CERT. Install the bootstrap config first, run certbot, then re-run without --bootstrap."
    fi
fi

log "Installing vhost for $DOMAIN -> 127.0.0.1:$PORT"
printf '%s\n' "$RENDERED" | $SUDO tee "$TARGET" >/dev/null

if [[ -d /etc/nginx/sites-enabled ]]; then
    $SUDO ln -sfn "$TARGET" /etc/nginx/sites-enabled/placepix
fi

log "Validating nginx configuration..."
$SUDO nginx -t

log "Reloading nginx..."
$SUDO systemctl reload nginx 2>/dev/null || $SUDO service nginx reload

log "Done. $DOMAIN is proxying to 127.0.0.1:$PORT"
