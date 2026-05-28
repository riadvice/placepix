<div align="center">
  <img src="static/logo.svg" alt="PlacePix Logo" width="200"/>

  # PlacePix

  A self-hosted placeholder image server inspired by [picsum.photos](https://picsum.photos).

  Serve random images with on-the-fly resizing, filtering, and formatting.

  **Live:** [placepix.net](https://placepix.net) · **Guide:** [placepix.net/guide](https://placepix.net/guide) · **Made by [RIADVICE](https://riadvice.com)**

  ---
</div>

## Contents

- [Features](#features)
- [Get Started in 5 Steps](#get-started-in-5-steps)
- [URL Examples](#url-examples)
- [Developer Guide](https://placepix.net/guide) — full API reference & feature documentation
- [Environment Variables](#environment-variables)
- [API](#api)
- [Development](#development)
- [License](#license)

## Features

- **On-the-fly resizing** — `/300/200` with `crop`, `cover`, `scale`, `contain`, or `smart` (OpenCV face detection)
- **Filters & effects** — grayscale, blur, sepia, noise, pixelate, tint, brightness, contrast, saturation
- **Multiple formats** — JPEG, PNG, WebP, AVIF
- **Solid color placeholders** — `/solid/500/300/ff0000` with optional text overlay
- **Aspect ratio sizing** — `/ratio/16:9/1080`
- **Preset dimensions** — Instagram, YouTube, Facebook, and more
- **Watermark overlay** — image or text with positioning and opacity
- **Srcset generation** — responsive image sets via `/api/srcset`
- **Upload API** — add images via `POST /api/upload`
- **Admin dashboard** — password-protected usage metrics
- **Browser caching** — ETag, Last-Modified, 304 responses
- **S3 storage** — optional S3-compatible backend for images
- **AI generation (experimental)** — OVHcloud AI Endpoints integration

## Get Started in 5 Steps

1. **Install Docker**
   ```bash
   docker build -t placepix .
   ```

2. **Add your images**
   ```bash
   mkdir -p images/nature images/people
   cp ~/photos/*.jpg images/nature/
   ```

3. **Run the server**
   ```bash
   docker run -d -p 3000:3000 -v $(pwd)/images:/app/images --name placepix placepix
   ```
   Or use `docker-compose up -d`.

4. **Open the UI**
   Visit `http://localhost:3000` to browse and build URLs.

5. **Use it in your HTML**
   ```html
   <img src="http://localhost:3000/300/200/nature" />
   ```

## URL Examples

```
GET /300/200                    # Random image, 300x200
GET /300/200.webp               # WebP format
GET /300/200/nature             # From "nature" category
GET /300/200?grayscale=true     # With filter
GET /300/200?text=Hello         # With text overlay
GET /ratio/16:9/1080            # Aspect ratio sizing
GET /preset/instagram-square    # Preset dimensions
GET /solid/500/300/ff0000       # Solid color placeholder
```

**Full reference:** Visit `/url-builder` on your running instance for an interactive explorer.

## Environment Variables

Copy `.env.example` to `.env` and set what you need:

| Variable | Description | Default |
|----------|-------------|---------|
| `HOST` | Bind address | `127.0.0.1:3000` |
| `IMAGES_DIR` | Images folder | `./images` |
| `CACHE` | Enable file cache | `true` |
| `CDN` | CDN base URL | — |
| `MAX_WIDTH` / `MAX_HEIGHT` | Size limits | `2000` |
| `UPLOAD_ENABLED` | Allow API uploads | `true` |
| `WATERMARK_ENABLED` | Show watermark | `false` |
| `WATERMARK_TEXT` / `WATERMARK_IMAGE` | Watermark content | — |
| `WATERMARK_POSITION` | `top-left`, `bottom-right`, etc. | `bottom-right` |
| `GA_TRACKING_ID` | Google Analytics ID | — |
| `PRIVACY_POLICY_URL` | Legal link | — |
| `S3_ENABLED` | Use S3-compatible storage | `false` |
| `AI_GENERATION_ENABLED` | Auto-generate images via AI | `false` |

## API

| Endpoint | Description |
|----------|-------------|
| `GET /api/categories` | List categories |
| `GET /api/images` | List all images |
| `GET /api/info/id/{id}` | Image metadata |
| `GET /api/srcset?id={id}&sizes=...` | Responsive srcset JSON |
| `POST /api/upload` | Upload an image |

## Development

```bash
pip install -e ".[dev]"
pytest
```

Requires **Python 3.12+**. On Linux you may need OpenCV system libs:
```bash
sudo apt-get install libgl1 libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1
```

## License

MIT — see [LICENSE](LICENSE).
