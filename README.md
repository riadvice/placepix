<div align="center">
  <img src="static/logo.svg" alt="PlacePix Logo" width="200"/>
  
  # PlacePix

  A self-hosted placeholder image server inspired by [picsum.photos](https://picsum.photos) and [lorem-server](https://github.com/manasky/lorem-server).

  Serve random images with on-the-fly resizing, filtering, and formatting.

  **Made by [RIADVICE](https://riadvice.com)**

  ---
</div>

## Features

✅ **Browser Cache Headers** - ETag, Last-Modified, 304 responses, HEAD support  
✅ **Usage Metrics** - SQLite-based tracking with password-protected admin dashboard  
✅ **Aspect Ratio Sizing** - `/ratio/16:9/1080` for responsive layouts  
✅ **Preset Dimensions** - Social media & ad sizes (Instagram, YouTube, etc.)  
✅ **Solid Color Placeholders** - `/solid/500x300/ff0000` with optional text  
✅ **Border & Padding** - Add borders and padding to images  
✅ **Image Effects** - Noise, pixelate, quality control, LQIP generation  
✅ **Srcset Generation** - API endpoint for responsive image sets  
✅ **Smart Crop** - OpenCV face detection for intelligent cropping  
✅ **Watermark Overlay** - Image or text watermarks with positioning

## Quick Start

```bash
# Install dependencies (includes OpenCV for smart crop)
pip install -e .

# Optional: Install dev dependencies for testing
pip install -e ".[dev]"

# Run server
python -m src.main
```

Visit `http://localhost:3000` to browse the image catalog.

### 🎨 Feature Explorer

Visit `http://localhost:3000/features` for an **interactive URL constructor** that lets you:
- Build URLs visually with all available parameters
- Preview images in real-time
- Copy generated URLs instantly
- Explore all features with live examples

## Dependencies

### Python Packages
- **FastAPI** - Web framework
- **Pillow** - Image processing
- **NumPy** - Noise/grain effects
- **OpenCV** (`opencv-python`) - Smart crop with face detection
- **pillow-avif** - AVIF format support (optional)
- **uvicorn** - ASGI server

### System Requirements

**Python**: 3.10 or higher

**Linux System Libraries** (for OpenCV):
```bash
# Debian/Ubuntu
sudo apt-get install libgl1 libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1

# Alpine (Docker)
apk add --no-cache libgomp libglib2.0 libsm libxext libxrender
```

**macOS**: No additional system dependencies required

**Windows**: No additional system dependencies required

All Python dependencies are automatically installed via `pip install -e .`

## Usage

### Get a random image

```
GET /300/200
```

### With filters

```
GET /300/200?grayscale=true&blur=5&text=Hello&fit=cover
```

### From a category

```
GET /300/200/nature
```

### Change format

```
GET /300/200.webp
GET /300/200?format=png
```

### Aspect Ratio Sizing

```
GET /ratio/16:9/1080
GET /ratio/4:3/768
```

### Preset Dimensions

```
GET /preset/instagram-square
GET /preset/youtube-thumbnail
GET /preset/facebook-cover
```

Available presets: `instagram-square`, `instagram-portrait`, `youtube-thumbnail`, `facebook-cover`, `twitter-header`, `leaderboard`, `banner`, `skyscraper`, `rectangle`, `mobile`, `tablet`, `desktop`, `4k`

### Solid Color Placeholders

```
GET /solid/500x300/ff0000
GET /solid/500x300/3b82f6/ffffff?text=Hello
```

### Srcset Generation

```
GET /api/srcset/123?sizes=320,640,1024,1920&format=webp
```

Returns JSON with responsive image URLs for `<img srcset>`.

### Upload an image

```bash
curl -F "file=@photo.jpg" http://localhost:3000/api/upload
```

## Query Parameters

### Basic Parameters
| Param       | Description                               | Default |
|-------------|-------------------------------------------|---------|
| `width`     | Image width (8–2000)                      | —       |
| `height`    | Image height (8–2000)                     | —       |
| `format`    | `jpeg`, `png`, `webp`, `avif`             | `jpeg`  |
| `seed`      | Deterministic image selection             | random  |
| `quality`   | JPEG/WebP quality (1-100)                 | `85`    |

### Filters & Effects
| Param        | Description                              | Default |
|--------------|------------------------------------------|---------|
| `grayscale`  | Convert to grayscale                     | `false` |
| `blur`       | Gaussian blur radius (1–10)              | `0`     |
| `sepia`      | Apply sepia tone                         | `false` |
| `noise`      | Add grain/noise (0-100)                  | `0`     |
| `pixelate`   | Pixelate effect size                     | `0`     |
| `tint`       | Hex color tint overlay                   | —       |
| `brightness` | Brightness adjustment (0.0-2.0)          | `1.0`   |
| `contrast`   | Contrast adjustment (0.0-2.0)            | `1.0`   |
| `saturation` | Saturation adjustment (0.0-2.0)          | `1.0`   |

### Layout & Sizing
| Param      | Description                                | Default |
|------------|-------------------------------------------|---------|
| `fit`      | `crop`, `scale`, `contain`, `cover`, `smart` | `crop`  |
| `border`   | Border width or `width,color` (e.g., `10,ff0000`) | —       |
| `padding`  | Padding in pixels                         | `0`     |

### Overlays
| Param       | Description                              | Default |
|-------------|------------------------------------------|---------|
| `text`      | Overlay text on image                    | —       |
| `watermark` | Watermark position or `true` for default | —       |

### Special
| Param  | Description                                    | Default |
|--------|------------------------------------------------|---------|
| `lqip` | Generate Low Quality Image Placeholder         | `false` |

## Configuration

Copy `.env.example` to `.env` and adjust:

| Variable             | Description                          | Default          |
|----------------------|--------------------------------------|------------------|
| `HOST`               | Server bind address                  | `127.0.0.1:3000` |
| `DIR`                | Images directory                     | `./images`       |
| `CACHE`              | Enable file caching                  | `true`           |
| `CDN`                | CDN base URL (optional)              | —                |
| `MAX_WIDTH`          | Maximum allowed width                | `2000`           |
| `MAX_HEIGHT`         | Maximum allowed height               | `2000`           |
| `ADMIN_PASSWORD`     | Enable metrics & admin dashboard     | —                |
| `WATERMARK_ENABLED`  | Enable watermark overlay             | `false`          |
| `WATERMARK_IMAGE`    | Path to watermark image              | —                |
| `WATERMARK_TEXT`     | Text watermark                       | —                |
| `WATERMARK_POSITION` | Position: `top-left`, `bottom-right` | `bottom-right`   |
| `WATERMARK_OPACITY`  | Watermark opacity (0.0-1.0)          | `0.5`            |

## Admin Dashboard

Set `ADMIN_PASSWORD` in your `.env` to enable usage metrics:

```bash
# View dashboard
curl -H "X-Admin-Password: your-password" http://localhost:3000/admin/stats

# Get JSON stats
curl -H "X-Admin-Password: your-password" http://localhost:3000/api/admin/stats
```

Tracks:
- Total requests
- Cache hit rate
- Average response time
- Popular sizes, categories, and formats

## Categories

Place images in folders under `./images/`. Each folder is a category.

Add a `category.json` for metadata:

```json
{
  "name": "Nature",
  "description": "Landscapes and wildlife",
  "author": "You",
  "tags": ["outdoor", "green"]
}
```

## License

MIT — see [LICENSE](LICENSE).
