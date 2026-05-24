# PlacePix

A self-hosted placeholder image server inspired by [picsum.photos](https://picsum.photos) and [lorem-server](https://github.com/manasky/lorem-server).

Serve random images with on-the-fly resizing, filtering, and formatting.

## Quick Start

```bash
# Install dependencies
pip install -e .

# Run server
python -m src.main
```

Visit `http://localhost:3000` to browse the image catalog.

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

### Upload an image

```bash
curl -F "file=@photo.jpg" http://localhost:3000/api/upload
```

## Query Parameters

| Param       | Description                               | Default |
|-------------|-------------------------------------------|---------|
| `width`     | Image width (8–2000)                      | —       |
| `height`    | Image height (8–2000)                     | —       |
| `grayscale` | Convert to grayscale                      | `false` |
| `blur`      | Gaussian blur radius (1–10)               | `0`     |
| `text`      | Overlay text on image                     | —       |
| `fit`       | `crop`, `scale`, `contain`, `cover`         | `crop`  |
| `format`    | `jpeg`, `png`, `webp`                       | `jpeg`  |
| `seed`      | Deterministic image selection               | random  |

## Configuration

Copy `.env.example` to `.env` and adjust:

| Variable      | Description                    | Default       |
|---------------|--------------------------------|---------------|
| `HOST`        | Server bind address            | `127.0.0.1:3000` |
| `DIR`         | Images directory               | `./images`    |
| `CACHE`       | Enable file caching            | `true`        |
| `CDN`         | CDN base URL (optional)        | —             |
| `MAX_WIDTH`   | Maximum allowed width          | `2000`        |
| `MAX_HEIGHT`  | Maximum allowed height         | `2000`        |

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
