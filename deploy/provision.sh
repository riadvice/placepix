#!/usr/bin/env bash
# Provision a host to run PlacePix. Idempotent: safe to re-run.
#
# Produces a deployment directory holding nothing but configuration and state:
#
#   /opt/placepix/
#   ├── .env
#   ├── docker-compose.yml
#   ├── data/
#   └── images/
#
# No source code is installed. The image comes from Docker Hub.
#
# Usage:
#   ./deploy/provision.sh --domain placepix.net
#   curl -fsSL https://raw.githubusercontent.com/riadvice/placepix/master/deploy/provision.sh | bash -s -- --domain placepix.net
#
# Options:
#   --domain NAME    Domain to serve (default: $(hostname))
#   --dir PATH       Deployment directory (default: /opt/placepix)
#   --port N         Port the app listens on (default: 3000)
#   --tag TAG        Image tag to deploy (default: latest)
#   --ref REF        Git ref to fetch deploy files from (default: master)
#   --skip-docker    Do not install Docker
#   --skip-nginx     Do not install or configure nginx
#   --skip-start     Prepare everything but do not start the container
#   --help           Show this help

set -Eeuo pipefail

DOMAIN=""
DEPLOY_DIR="/opt/placepix"
PORT="3000"
TAG="latest"
REF="master"
SKIP_DOCKER=false
SKIP_NGINX=false
SKIP_START=false

RAW_BASE="https://raw.githubusercontent.com/riadvice/placepix"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd || echo "")"

log()  { printf '\033[34m[placepix]\033[0m %s\n' "$*"; }
ok()   { printf '\033[32m[ ok ]\033[0m %s\n' "$*"; }
warn() { printf '\033[33m[warn]\033[0m %s\n' "$*"; }
die()  { printf '\033[31m[fail]\033[0m %s\n' "$*" >&2; exit 1; }

while [[ $# -gt 0 ]]; do
    case "$1" in
        --domain) DOMAIN="${2:-}"; shift 2 ;;
        --dir)    DEPLOY_DIR="${2:-}"; shift 2 ;;
        --port)   PORT="${2:-}"; shift 2 ;;
        --tag)    TAG="${2:-}"; shift 2 ;;
        --ref)    REF="${2:-}"; shift 2 ;;
        --skip-docker) SKIP_DOCKER=true; shift ;;
        --skip-nginx)  SKIP_NGINX=true; shift ;;
        --skip-start)  SKIP_START=true; shift ;;
        -h|--help) sed -n '2,28p' "$0" | sed 's/^# \?//'; exit 0 ;;
        *) die "Unknown option: $1" ;;
    esac
done

DOMAIN="${DOMAIN:-$(hostname)}"
case "$PORT" in ''|*[!0-9]*) die "Port '$PORT' is not numeric" ;; esac

SUDO=""
if [[ "$(id -u)" -ne 0 ]]; then
    command -v sudo >/dev/null 2>&1 || die "Not root and sudo is not available"
    SUDO="sudo"
fi

# Escalate for the deployment directory only when it is not already writable.
DSUDO="$SUDO"
if [[ -d "$DEPLOY_DIR" && -w "$DEPLOY_DIR" ]] || \
   [[ ! -d "$DEPLOY_DIR" && -w "$(dirname "$DEPLOY_DIR")" ]]; then
    DSUDO=""
fi

# Fetch a deploy file: use the local checkout when present, else GitHub.
fetch() {
    local name="$1" dest="$2"
    if [[ -n "$SCRIPT_DIR" && -f "$SCRIPT_DIR/$name" ]]; then
        $DSUDO cp "$SCRIPT_DIR/$name" "$dest"
    else
        log "Downloading $name from $REF"
        $DSUDO curl -fsSL "$RAW_BASE/$REF/deploy/$name" -o "$dest" \
            || die "Could not download $name"
    fi
}

log "Provisioning PlacePix"
log "  domain:    $DOMAIN"
log "  directory: $DEPLOY_DIR"
log "  port:      $PORT"
log "  image tag: $TAG"

# ── 1. Docker ───────────────────────────────────────────────────────
if [[ "$SKIP_DOCKER" == false ]]; then
    if command -v docker >/dev/null 2>&1; then
        ok "Docker already installed ($(docker --version))"
    else
        log "Installing Docker..."
        TMP_SCRIPT=$(mktemp)
        curl -fsSL https://get.docker.com -o "$TMP_SCRIPT"
        $SUDO sh "$TMP_SCRIPT"
        rm -f "$TMP_SCRIPT"
        ok "Docker installed"
    fi

    if ! docker compose version >/dev/null 2>&1; then
        die "The Docker Compose plugin is missing; install docker-compose-plugin"
    fi

    # Let the invoking user run docker without sudo. Note this is
    # root-equivalent access - only do it for an administrator account.
    if [[ -n "${SUDO_USER:-$USER}" ]] && ! id -nG "${SUDO_USER:-$USER}" | tr ' ' '\n' | grep -qx docker; then
        $SUDO usermod -aG docker "${SUDO_USER:-$USER}"
        warn "Added ${SUDO_USER:-$USER} to the docker group; log out and back in for it to apply"
    fi
fi

# ── 2. Deployment directory ─────────────────────────────────────────
log "Preparing $DEPLOY_DIR"
$DSUDO mkdir -p "$DEPLOY_DIR/data" "$DEPLOY_DIR/images"
fetch "docker-compose.yml" "$DEPLOY_DIR/docker-compose.yml"

if [[ -f "$DEPLOY_DIR/.env" ]]; then
    ok "Keeping the existing .env (never overwritten)"
else
    fetch "env.example" "$DEPLOY_DIR/.env"
    $DSUDO sed -i "s/^PORT=.*/PORT=$PORT/; s/^PLACEPIX_TAG=.*/PLACEPIX_TAG=$TAG/" "$DEPLOY_DIR/.env"
    $DSUDO chmod 600 "$DEPLOY_DIR/.env"
    warn "Created $DEPLOY_DIR/.env from the template - edit it before going live"
fi
ok "Deployment directory ready"

# ── 3. nginx ────────────────────────────────────────────────────────
if [[ "$SKIP_NGINX" == false ]]; then
    if ! command -v nginx >/dev/null 2>&1; then
        log "Installing nginx..."
        $SUDO apt-get update -qq && $SUDO apt-get install -y -qq nginx
    fi
    $SUDO mkdir -p /var/www/certbot

    # nginx-setup.sh resolves its templates relative to itself, so when running
    # standalone fetch the whole set into one temporary directory.
    NGINX_SETUP="$SCRIPT_DIR/nginx-setup.sh"
    if [[ ! -f "$NGINX_SETUP" ]]; then
        NGINX_TMP=$(mktemp -d)
        for f in nginx-setup.sh nginx-bootstrap.conf.template nginx-placepix.conf.template; do
            curl -fsSL "$RAW_BASE/$REF/deploy/$f" -o "$NGINX_TMP/$f" \
                || die "Could not download $f"
        done
        NGINX_SETUP="$NGINX_TMP/nginx-setup.sh"
        chmod +x "$NGINX_SETUP"
    fi

    if [[ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]]; then
        log "Certificate found; installing the TLS vhost"
        "$NGINX_SETUP" --domain "$DOMAIN" --env-file "$DEPLOY_DIR/.env" --install
    else
        log "No certificate yet; installing the HTTP-only vhost"
        "$NGINX_SETUP" --domain "$DOMAIN" --env-file "$DEPLOY_DIR/.env" --bootstrap --install
        warn "Obtain a certificate, then re-run this script to switch to TLS:"
        warn "  sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN --agree-tos -m devops@riadvice.com --redirect -n"
    fi
fi

# ── 4. Start ────────────────────────────────────────────────────────
if [[ "$SKIP_START" == false ]]; then
    log "Pulling and starting the container..."
    ( cd "$DEPLOY_DIR" && $SUDO docker compose up -d )
    ok "PlacePix is running on 127.0.0.1:$PORT"
else
    log "Skipping start; run: cd $DEPLOY_DIR && docker compose up -d"
fi

cat <<EOF

$(ok "Provisioning complete")

  Deploy an update:  cd $DEPLOY_DIR && docker compose up -d
  Logs:              cd $DEPLOY_DIR && docker compose logs -f
  Roll back:         set PLACEPIX_TAG in $DEPLOY_DIR/.env, then up -d again

  Back up: $DEPLOY_DIR/.env, $DEPLOY_DIR/data, $DEPLOY_DIR/images
  Do not back up the cache; it is a Docker volume and rebuilds itself.
EOF
