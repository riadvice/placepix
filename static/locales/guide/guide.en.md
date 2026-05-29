---
title: PlacePix Developer Guide — Self-Hosted Placeholder Image API & Feature Reference
description: Complete PlacePix developer guide and API reference. Learn how to deploy face-aware cropped placeholder images with Docker, generate gradient and SVG placeholders, and use social media presets for Instagram, YouTube, and more.
keywords: self-hosted placeholder image API, face-aware crop placeholder, gradient placeholder generator, Docker placeholder image service, Instagram story placeholder API, SVG placeholder generator, developer image API
author: RIADVICE
robots: index, follow
og_title: PlacePix Developer Guide — Self-Hosted Placeholder Image API & Feature Reference
og_description: Complete developer guide covering Docker deployment, smart crop, gradient placeholders, SVG generation, and social media presets.
twitter_title: PlacePix Developer Guide — Self-Hosted Placeholder Image API & Feature Reference
twitter_description: Complete developer guide covering Docker deployment, smart crop, gradient placeholders, SVG generation, and social media presets.
jsonld_name: PlacePix Developer Guide — Self-Hosted Placeholder Image API & Feature Reference
jsonld_description: Complete developer guide and API reference for PlacePix, a self-hosted placeholder image service. Covers Docker deployment, face-aware smart crop, gradient placeholders, SVG generation, and social media presets.
jsonld_proficiency: Expert
jsonld_dependencies: Docker, Python 3.12, FastAPI
header_title: PlacePix Developer Guide
header_subtitle: Complete API reference and feature documentation for the self-hosted placeholder image service. Covers Docker deployment, smart crop, gradient placeholders, SVG generation, letter avatars, and social media presets.
author_label: By
updated_label: "Last updated: May 2026"
github_label: Open Source on GitHub
toc_title: Table of Contents
---

## What is PlacePix?

PlacePix is a **self-hosted placeholder image service** built for developers and design teams. Unlike third-party placeholder services that require external network calls and may disappear, PlacePix runs entirely on your own infrastructure. Drop images into folders, and instantly get URL endpoints that serve resized, filtered, and formatted images.

The service is written in Python using FastAPI with image processing powered by Pillow and OpenCV. It supports Docker deployment, and S3-compatible object storage.

### Features

- **Zero configuration** — drop images in folders and go
- **Face-aware cropping** — OpenCV detects and centers faces
- **Gradient & SVG placeholders** — no images required
- **Social media presets** — Instagram, YouTube, TikTok sizes built-in
- **Color search** — find images matching your brand palette
- **Letter avatars** — deterministic profile images from names

## Docker Deployment Guide

The fastest way to run PlacePix is with Docker. A single command deploys the entire service with smart scanning, color extraction, and the embedded URL builder.

### One-Line Deployment

```bash
docker run -d -p 3000:3000 \
  -v ./images:/app/images \
  riadvice/placepix:latest
```

### Docker Compose (Recommended)

```yaml
services:
  placepix:
    image: riadvice/placepix:latest
    ports:
      - "3000:3000"
    volumes:
      - ./images:/app/images
      - ./data:/app/data
    environment:
      - HOST=0.0.0.0:3000
      - UPLOAD_ENABLED=true
      - WATERMARK_ENABLED=false
    restart: unless-stopped
```

### Persistent Data & Environment

Mount both `/app/images` (your image library) and `/app/data` (scan cache and metadata) to preserve state across container restarts. Configure behavior via environment variables or a `.env` file.

### OVHcloud S3-Compatible Storage

PlacePix supports any S3-compatible backend. For OVHcloud Object Storage, set:

```
S3_ENABLED=true
S3_ENDPOINT=https://s3.rbx.io.cloud.ovh.net
S3_ACCESS_KEY=your-key
S3_SECRET_KEY=your-secret
S3_BUCKET=your-bucket
S3_REGION=rbx
```

## Face-Aware Smart Cropping

Standard center cropping can slice through faces in portrait photography. PlacePix solves this with **face-aware smart cropping** powered by OpenCV Haar cascades.

### How It Works

When a request includes `?fit=smart`, PlacePix scans the image for human faces using OpenCV. If faces are detected, the crop window is shifted so that the face centroid lies as close as possible to the golden-ratio intersection points. If no faces are found, it falls back to standard center cropping.

### API Examples

```
# Face-aware crop (detects and centers faces)
/400/300/people?fit=smart

# Standard center crop
/400/300/people?fit=crop

# Cover fill (may stretch)
/400/300/people?fit=cover

# Contain (letterboxing)
/400/300/people?fit=contain
```

### When to Use Smart Crop

- Portrait photography and headshots
- Team pages where faces matter
- Social media thumbnails
- Any scenario where geometric center cropping ruins composition

## Gradient Placeholder API

Generate linear and radial gradient images on the fly without uploading any assets. Perfect for hero backgrounds, loading states, and design mockups.

### Endpoint Syntax

```
/gradient/{width}/{height}/{from_hex}/{to_hex}
```

### Examples

```
# Simple linear gradient (top to bottom)
/gradient/800/400/3b82f6/10b981

# 45-degree angled gradient
/gradient/800/400/e11d48/f59e0b?angle=45

# Radial gradient from center
/gradient/800/400/1e293b/64748b?gradient_type=radial

# With output format
/gradient/800/400/0ea5e9/ffffff?format=webp&quality=80
```

### Parameter Reference

- `{from_hex}` / `{to_hex}` — hex colors without the # prefix
- `?angle=45` — linear angle in degrees (0-360)
- `?gradient_type=radial` — switches to radial gradient
- `?format=webp` — WebP output (smaller file size)

## SVG Placeholder Generator

SVG placeholders require zero server-side image processing. They are generated as inline SVG with customizable background color, foreground color, and text label.

### Endpoint

```
/svg/{width}/{height}?bg={hex}&fg={hex}&text={label}
```

### Examples

```
# Default wireframe placeholder
/svg/400/300

# Custom brand colors
/svg/400/300?bg=1c1917&fg=0ea5e9

# With custom text
/svg/400/300?bg=0ea5e9&fg=ffffff&text=Hero+Section
```

### Why SVG?

- File size under 500 bytes
- Infinitely scalable without quality loss
- Zero server processing overhead
- Perfect for wireframes and low-fidelity prototypes

## Social Media Presets

PlacePix includes predefined dimensions for popular social platforms and screen sizes. Use these to generate perfectly-sized placeholder images for Instagram, YouTube, TikTok, LinkedIn, X (Twitter), and standard displays.

### Instagram

```
/preset/instagram-square/nature     # 1080x1080
/preset/instagram-portrait/nature  # 1080x1350
/preset/instagram-story/nature     # 1080x1920
```

### YouTube

```
/preset/youtube-thumbnail/nature   # 1280x720
/preset/youtube-banner/nature      # 2560x423
```

### TikTok

```
/preset/tiktok-video/nature        # 1080x1920 (9:16)
```

### LinkedIn

```
/preset/linkedin-post/nature       # 1200x627
```

### X (Twitter)

```
/preset/twitter-header/nature      # 1500x500
```

### Screen Sizes

```
/preset/mobile/nature              # 375x812
/preset/tablet/nature              # 768x1024
/preset/desktop/nature             # 1920x1080
/preset/4k/nature                  # 3840x2160
```

### Long-Tail Use Case: Instagram Story API

If you are building a social media management tool and need **Instagram story size placeholder images**, use `/preset/instagram-story/{category}`. Combine with `?fit=smart` for portrait photos and `?format=webp&quality=70` for optimized delivery.

## Color Search API

Every image in PlacePix is scanned for its top 3 dominant colors. You can search the entire library by hex color to find images that match your brand palette.

### Endpoints

```
# Get an image matching a specific hex color
/color/0ea5e9/400/300

# Filter any endpoint by dominant color
/400/300/nature?color=d97706

# List all images matching a color
/api/color/3b82f6
```

### How Color Scanning Works

On startup, PlacePix extracts the most frequent colors from each image using k-means clustering in LAB color space. This produces perceptually accurate matches rather than raw RGB averages. The palette page (`/palette`) visualizes these colors and lets you browse by hue category.

## Orientation Filtering

Filter random images by their native aspect ratio before selection. This is useful when you need images that naturally fit a layout — landscape for headers, portrait for cards, or squarish for thumbnails.

### Endpoints

```
# Landscape images (width > height)
/400/300?orientation=landscape

# Portrait images (height > width)
/400/300?orientation=portrait

# Squarish images (within 15% of 1:1 by default)
/400/300?orientation=squarish

# Combined with other filters
/400/300/nature?orientation=landscape&seed=spring
/color/0ea5e9/400/300?orientation=portrait
/api/color/3b82f6?orientation=landscape
```

### Configuration

The `squarish` tolerance is configurable via the `ORIENTATION_SQUARISH_TOLERANCE` environment variable (default: `0.15`). A value of `0.15` means images with an aspect ratio between `0.85` and `1.15` are considered squarish. Set to `0.0` for exact 1:1 only.

### How It Works

PlacePix reads image dimensions from file headers during the initial scan (local files) and during the background metadata scan (S3 images). The dimensions are stored in memory and used to filter the candidate pool before random or seeded selection. If orientation is requested but no images match, a `404` is returned.

## Filters & Effects

Apply real-time filters and effects to any image via query parameters. All processing is done server-side and cached for subsequent requests.

### Color Adjustments

```
?grayscale=1               # Black & white
?sepia=1                   # Warm sepia tone
?tint=0ea5e9               # Hex color overlay
?brightness=1.3            # 0.0 to 2.0
?contrast=1.2              # 0.0 to 2.0
?saturation=2.0            # 0.0 to 2.0
?invert=true               # Invert colors
?posterize=4               # Color levels (1-8)
?duotone=ff0000,0000ff     # Two-color map
```

### Image Effects

```
?blur=2                    # Gaussian blur (1-10)
?sharpen=1.5               # Sharpen amount
?emboss=true               # 3D relief
?edges=sobel               # Edge detection
?edges=canny               # Canny edges
?halftone=4                # Dot pattern
?oil_painting=true         # Oil painting style
?pencil_sketch=true        # Pencil sketch
?cartoon=true              # Cartoon effect
?vignette=0.5              # Darken edges (0-1)
```

### Overlay Parameters

```
?text=Hello+World          # Text overlay
?border=4,ffffff           # Border width & color
?watermark=1               # Apply configured watermark
?padding=20                # Internal padding
```

## Avatar Generator

Generate deterministic avatars from any name or email. PlacePix supports two avatar types: **Letter Avatar** (colored initials) and **Multiavatar** (multicultural vector avatars).

### Endpoint

```
/avatar/{size}/{name}
/avatar/{size}/{name}.{ext}
```

### Parameters

- `type` — avatar type: `letter` (default) or `multiavatar`
- `size` — pixel size (e.g. `64`, `128`, `256`)
- `name` — any string; used as seed for the avatar

#### Letter Avatar (`type=letter`)

- `circle` — crop to a circle shape
- `border={width},{color}` — add a border
- `bg={hex}` — override background color
- `fg={hex}` — override text/foreground color
- `single=true` — use only the first letter
- `uppercase=false` — preserve lowercase letters
- `palette={name}` — choose from `flatui`, `material`, `pastel`, `neon`, `cool`, `warm`

#### Multiavatar (`type=multiavatar`)

- `env` — include environment background (`true` by default, `false` to omit)
- `part` — specific part code (optional, e.g. `11`)
- `theme` — specific theme code (optional, e.g. `C`)

### Examples

```
# Simple 128px letter avatar
/avatar/128/John+Doe

# Circle letter avatar with custom border
/avatar/128/John+Doe?circle=true&border=2,ffffff

# Single initial, pastel palette
/avatar/64/Alice?single=true&palette=pastel

# SVG letter output (scalable, under 500 bytes)
/avatar/128/John+Doe.svg

# Multiavatar (multicultural vector avatar)
/avatar/128/Binx+Bond?type=multiavatar

# Multiavatar without environment background
/avatar/128/Binx+Bond?type=multiavatar&env=false

# Specific multiavatar version
/avatar/128/Binx+Bond?type=multiavatar&part=11&theme=C
```

### Why Use Letter Avatars?

- Zero external dependencies — no Gravatar or third-party avatar service
- Deterministic — the same name always produces the same color
- SVG support — infinitely scalable, perfect for HiDPI displays
- Six built-in color palettes for any brand aesthetic

### Why Use Multiavatar?

- 12 billion unique multicultural avatars
- Deterministic — the same name always produces the same avatar
- Pure SVG output — tiny file size, infinitely scalable
- No external API calls required

## REST API Quick Reference

All endpoints support CORS and return images with long-term cache headers. Base64 JSON output is available for small thumbnails.

### Image Endpoints

- `GET /{width}/{height}/{category}` — Random image from category
- `GET /{width}/{height}` — Random image from all categories
- `GET /id/{id}/{width}/{height}` — Specific image by ID
- `GET /ratio/{ratio}/{width}/{category}` — Aspect ratio image
- `GET /preset/{preset}/{category}` — Social media preset
- `GET /color/{hex}/{width}/{height}` — Color-matched image
- `GET /gradient/{w}/{h}/{from}/{to}` — Gradient image
- `GET /svg/{width}/{height}` — SVG placeholder
- `GET /avatar/{size}/{name}` — Avatar (letter PNG/SVG or multiavatar SVG)

### Metadata Endpoints

- `GET /api/images` — List categories and totals
- `GET /api/info/id/{id}` — Image metadata (dimensions, colors, format)
- `GET /api/color/{hex}` — Images matching a color

### Health Endpoints

- `GET /health` — Liveness probe (Docker/K8s)
- `GET /ready` — Readiness probe (503 until images loaded)

## Expertise & Credentials

- Active contributors to the open-source ecosystem since 2008
- All code is open source under the MIT License and auditable on <a href="https://github.com/riadvice/placepix" target="_blank" class="text-accent hover:underline">GitHub</a>

## Frequently Asked Questions

### How do I deploy PlacePix with Docker?

Run `docker run -d -p 3000:3000 -v ./images:/app/images riadvice/placepix:latest`. Mount your image folder and the service starts immediately with smart scanning enabled.

### What is face-aware smart cropping?

PlacePix uses OpenCV Haar cascades to detect faces in images. When you add `?fit=smart` to any URL, the crop region is shifted to center on detected faces rather than using geometric center. If no face is found, it falls back to standard center cropping.

### Can I generate gradient placeholder images without uploading photos?

Yes. The `/gradient/{width}/{height}/{from}/{to}` endpoint generates gradient images entirely from URL parameters. No uploaded images are required. You can also create SVG placeholders with `/svg/{width}/{height}`.

### How do I generate Instagram story size placeholder images via API?

Use the preset endpoint: `/preset/instagram-story/{category}`. This returns a 1080x1920 image. Combine with `?format=webp&quality=70` for optimized delivery and `?fit=smart` for portrait-safe cropping.

### Does PlacePix support S3-compatible object storage?

Yes. PlacePix works with OVHcloud Object Storage, AWS S3, MinIO, and any S3-compatible provider. Configure endpoint, bucket, access key, and secret key via environment variables.

### What output formats are supported?

WebP, AVIF, JPEG, PNG, SVG, and base64 JSON. Use `.webp`, `.avif`, or `.png` as the file extension, or add `?format=webp` as a query parameter. AVIF produces the smallest files; PNG is lossless.

### Is PlacePix free for commercial use?

Yes. PlacePix is released under the MIT License and is free for both personal and commercial use. Because it is self-hosted, there are no usage limits, no API keys, and no per-request billing.