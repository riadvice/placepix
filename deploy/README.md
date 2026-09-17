# Deploying PlacePix

Production runs a prebuilt image from Docker Hub. The server holds no source
code, no virtualenv and no build toolchain — only configuration and state:

```
/opt/placepix/
├── .env                 settings and secrets (the only copy — back it up)
├── docker-compose.yml   from deploy/docker-compose.yml
├── data/                metrics database and manifests
└── images/              the image library
```

The render cache lives in a Docker volume (`placepix-cache`), not in this
directory. It is derived data: deleting it costs a little CPU, nothing more.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/riadvice/placepix/master/deploy/provision.sh | bash
```

That installs Docker if missing, creates the directory layout, writes a starter
`.env`, pulls the image and starts the container on `127.0.0.1:3000`.

To read the script before running it as root — a good habit for any `curl | bash`:

```bash
curl -fsSL https://raw.githubusercontent.com/riadvice/placepix/master/deploy/provision.sh -o provision.sh
less provision.sh && bash provision.sh
```

Useful flags:

| Flag | Purpose |
|---|---|
| `--port N` | Port to listen on (default `3000`) |
| `--tag TAG` | Image tag to run (default `latest`) |
| `--dir PATH` | Deployment directory (default `/opt/placepix`) |
| `--with-nginx` | Also install and configure nginx (off by default) |
| `--skip-docker` | Docker is already installed and managed elsewhere |
| `--skip-start` | Set everything up without starting the container |

Re-running is safe. An existing `.env` is **never** overwritten, so your
credentials survive an upgrade of the compose file.

Then edit `/opt/placepix/.env` — at minimum `SITE_URL`, and `UPLOAD_ENABLED=false`
for a public instance — and apply it with `docker compose up -d`.

## Web server

The container publishes on `127.0.0.1` only, so something must proxy to it.

If nginx already serves this host, add to your existing vhost:

```nginx
location / {
    proxy_pass http://127.0.0.1:3000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

For a complete vhost with TLS, security headers and asset caching, render one
from the template — it reads the port back out of `.env`, so the two can never
disagree:

```bash
./deploy/nginx-setup.sh --domain placepix.net                # print it
./deploy/nginx-setup.sh --domain placepix.net --install      # install and reload
```

On a bare host with no certificate yet, install the HTTP-only vhost first,
obtain a certificate, then install the TLS one:

```bash
./deploy/nginx-setup.sh --domain placepix.net --bootstrap --install
sudo certbot --nginx -d placepix.net -d www.placepix.net --agree-tos -m devops@riadvice.com --redirect -n
./deploy/nginx-setup.sh --domain placepix.net --install
```

## Deploy an update

Releases are built and pushed by CI when a version tag is pushed. Deploying is
a pull — never a build:

```bash
cd /opt/placepix && docker compose up -d
```

There is no `git pull`, no `--build`, and no `docker system prune` afterwards.

**Roll back** by pinning the previous version in `.env`:

```bash
PLACEPIX_TAG=0.3
```

then `docker compose up -d` again.

## Migrating to a new host

**Check first whether images live in S3.** If `S3_ENABLED=true`, the library is
in the bucket and `images/` may be nearly empty:

```bash
grep -E '^(S3_ENABLED|S3_BUCKET|UPLOAD_ENABLED)=' /opt/placepix/.env
```

What moves, and what deliberately does not:

| Path | Move? | Why |
|---|---|---|
| `.env` | **Yes** | The only copy of your S3 and OVH credentials |
| `images/` | Yes, unless in S3 | The image library |
| `data/` | **Yes** | Metrics database; the manifests rebuild but copying skips a rescan |
| Docker cache volume | **No** | Derived renders, TTL'd anyway — copying wastes the whole transfer |
| `/etc/nginx/...` | Yes | Copy the *live* files; they are usually hand-edited |
| `/etc/letsencrypt/` | Recommended | Avoids a certificate gap at cutover |

Steps:

1. **Lower the DNS TTL** to 300s a day or two ahead, so you can roll back fast.
2. **Provision the new host** with the one-liner above, then copy the state
   across while the old host keeps serving:

   ```bash
   sudo rsync -avz old-host:/opt/placepix/.env    /opt/placepix/.env
   sudo rsync -avz old-host:/opt/placepix/images/ /opt/placepix/images/
   sudo rsync -avz old-host:/opt/placepix/data/   /opt/placepix/data/
   ```

3. **Test before cutting over**, by pointing your own machine at the new IP:

   ```bash
   # in /etc/hosts on your laptop
   <new-ip>  placepix.net
   ```

   Check `/health` and that a real image renders.
4. **Final sync.** Stop the container on the old host first, so the metrics
   SQLite database is copied at rest:

   ```bash
   ssh old-host 'cd /opt/placepix && docker compose stop'
   sudo rsync -avz old-host:/opt/placepix/data/ /opt/placepix/data/
   ```

5. **Cut over DNS**, then keep the old host powered off but intact for ~48h
   before decommissioning.

## Backups

Back up `/opt/placepix/.env`, `data/` and `images/`. Skip the cache volume.

```bash
tar czf placepix-$(date +%F).tar.gz -C /opt/placepix .env data images
```

## Troubleshooting

| Symptom | Check |
|---|---|
| 502 from nginx | Is the port in `.env` the one in `proxy_pass`? `docker compose ps` |
| Container restarting | `docker compose logs --tail=50` |
| Reachable on `:3000` from outside | `BIND_ADDR` should be `127.0.0.1` when nginx fronts it |
| Disk filling | Logs are capped at 10M×3; check image layers with `docker system df` |
| Version shows `dev` | The image was built locally without `GIT_VERSION`; deploy a CI-built tag |
