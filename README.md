<div align="center">
  <img src="static/logo.svg" alt="PlacePix Logo" width="200"/>
  
  # PlacePix

  A self-hosted placeholder image server inspired by [picsum.photos](https://picsum.photos) and [lorem-server](https://github.com/manasky/lorem-server).

  Serve random images with on-the-fly resizing, filtering, and formatting.

  **Live:** [placepix.net](https://placepix.net) · **Made by [RIADVICE](https://riadvice.com)**

  ---
</div>

## Features

✅ **Browser Cache Headers** - ETag, Last-Modified, 304 responses, HEAD support  
✅ **Usage Metrics** - SQLite-based tracking with password-protected admin dashboard  
✅ **Aspect Ratio Sizing** - `/ratio/16:9/1080` for responsive layouts  
✅ **Preset Dimensions** - Social media & ad sizes (Instagram, YouTube, etc.)  
✅ **Solid Color Placeholders** - `/solid/500/300/ff0000` with optional text  
✅ **Border & Padding** - Add borders and padding to images  
✅ **Image Effects** - Noise, pixelate, quality control, LQIP generation  
✅ **Srcset Generation** - API endpoint for responsive image sets  
✅ **Smart Crop** - OpenCV face detection for intelligent cropping  
✅ **Watermark Overlay** - Image or text watermarks with positioning

## Quick Start

### 🐳 Docker (Recommended)

```bash
# Build the Docker image
docker build -t placepix .

# Run the container
docker run -d \
  -p 3000:3000 \
  -v $(pwd)/images:/app/images \
  -v $(pwd)/.cache:/app/.cache \
  --name placepix \
  placepix

# Or use docker-compose
docker-compose up -d
```

Visit `http://localhost:3000` to browse the image catalog.

### 📦 Local Installation

```bash
# Install dependencies (includes OpenCV for smart crop)
pip install -e .

# Optional: Install dev dependencies for testing
pip install -e ".[dev]"

# Run server
python -m src.main
```

### 🔗 URL Builder

Visit `http://localhost:3000/url-builder` for an **interactive URL constructor** that lets you:
- Build URLs visually with all available parameters
- Preview images in real-time
- Copy generated URLs instantly
- Explore all features with live examples

## Testing

PlacePix includes comprehensive unit tests.

### Running Tests

```bash
# Install dev dependencies first
pip install -e ".[dev]"

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_image_effects.py

# Run with coverage report (shows missing lines)
pytest --cov=src --cov-report=term-missing

# Run with detailed coverage in console
pytest --cov=src --cov-report=term-missing -v

# Run with HTML coverage report (interactive)
pytest --cov=src --cov-report=html
# Open htmlcov/index.html in browser

# Show coverage for specific module
pytest --cov=src.image_processor --cov-report=term-missing
```

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
GET /solid/500/300/ff0000
GET /solid/500/300/3b82f6/ffffff?text=Hello
```

### Srcset Generation

```
GET /api/srcset/123?sizes=320,640,1024,1920&format=webp
```

Returns JSON with responsive image URLs for `<img srcset>`.

## API Endpoints

PlacePix provides RESTful API endpoints for developers:

### Get Categories

```bash
GET /api/categories
```

**Response:**
```json
{
  "categories": ["nature", "architecture", "animals", "abstract", "food"],
  "count": 5,
  "detailed": [
    {
      "name": "nature",
      "count": 15,
      "display_name": "Nature",
      "description": "Beautiful nature and landscapes",
      "author": "",
      "tags": []
    }
  ]
}
```

### Get Images Metadata

```bash
GET /api/images
```

**Response:**
```json
{
  "categories": [...],
  "total": 45
}
```

### Get Image Info by ID

```bash
GET /api/info/id/123
```

**Response:**
```json
{
  "id": 123,
  "category": "nature",
  "width": 1920,
  "height": 1080,
  "format": "jpeg",
  "path": "nature/image.jpg"
}
```

### Generate Srcset

```bash
GET /api/srcset?id=123&sizes=400,800,1200&format=webp
```

**Response:**
```json
{
  "srcset": "/id/123/400/300.webp 400w, /id/123/800/600.webp 800w, /id/123/1200/900.webp 1200w",
  "sizes": "(max-width: 400px) 400px, (max-width: 800px) 800px, 1200px"
}
```

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
| `WATERMARK_ENABLED`  | Enable watermark overlay             | `false`          |
| `WATERMARK_IMAGE`    | Path to watermark image              | —                |
| `WATERMARK_TEXT`     | Text watermark                       | —                |
| `WATERMARK_POSITION` | Position: `top-left`, `bottom-right` | `bottom-right`   |
| `WATERMARK_OPACITY`  | Watermark opacity (0.0-1.0)          | `0.5`            |

## Docker Deployment

### Building the Image

```bash
# Build from source
docker build -t placepix:latest .

# Build with custom tag
docker build -t placepix:v1.0.0 .
```

### Running the Container

**Basic run:**
```bash
docker run -d \
  -p 3000:3000 \
  -v $(pwd)/images:/app/images \
  --name placepix \
  placepix:latest
```

**With environment variables:**
```bash
docker run -d \
  -p 3000:3000 \
  -v $(pwd)/images:/app/images \
  -v $(pwd)/.cache:/app/.cache \
  -e WATERMARK_ENABLED=true \
  -e WATERMARK_TEXT="© MyCompany" \
  --name placepix \
  placepix:latest
```

**Using docker-compose:**
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Docker Hub

```bash
# Pull from Docker Hub
docker pull riadvice/placepix:latest

# Run from Docker Hub
docker run -d -p 3000:3000 -v $(pwd)/images:/app/images riadvice/placepix:latest
```

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

## Inspiration

PlacePix was inspired by these excellent services:

- **[picsum.photos](https://picsum.photos)** - The Lorem Ipsum for photos. A simple, elegant placeholder image service.
- **[lorem.space](https://lorem.space)** - Modern placeholder images with various categories and filters.
- **[lorem-server](https://github.com/manasky/lorem-server)** - Self-hosted placeholder image server in Go.

PlacePix combines the best ideas from these services while adding unique features like smart cropping, watermarks, comprehensive image effects, and a beautiful feature explorer interface.

## License

MIT — see [LICENSE](LICENSE).
