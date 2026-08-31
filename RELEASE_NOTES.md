# Release Notes

## Released versions

- [v0.4 - 2026-08-31](#v04)
- [v0.3 - 2026-05-29](#v03)
- [v0.2 - 2026-05-26](#v02)
- [v0.1 - 2026-05-25](#v01)

## v0.4

### 🚀 Introduction

- **Version Number**: 0.4
- **Release Date**: 2026-08-31
- **General Overview**: Device mockups, wireframe placeholders, subject-aware focal points, responsive snippets, and a text-contrast toolkit.

### ✨ New Features

- **Device & browser mockups** — `/mockup/{device}/{width}` frames a placeholder in a phone, tablet, laptop or browser (`/api/mockups` lists frames)
- **Wireframe placeholders** — `/skeleton/{preset}/{width}/{height}` draws lo-fi grey-box / skeleton-loading blocks (`/api/skeletons` lists presets)
- **Subject-aware focal point** — smart crop auto-centres on the subject, with a `?focal=x,y` override
- **Responsive snippets** — `/api/snippet/{id}` returns copy-paste `srcset`/`<picture>` markup
- **Text contrast & scrim** — `?scrim=` overlays for legible text and `/api/contrast/{id}` for a per-region WCAG report

### 🔧 Improvements

- **URL builder** — surfaced the mockup, wireframe and scrim features in the UI
- **Dependency refresh** — OpenCV 5 and refreshed core packages
- **Testing** — Docker-based test runner plus `pytest-xdist` parallelism

## v0.3

### 🚀 Introduction

- **Version Number**: 0.3
- **Release Date**: 2026-05-29
- **General Overview**: Adds image orientation filtering, comprehensive SEO optimization with meta tags and structured data, multilingual sitemap infrastructure, and multiavatar integration for vector avatars.

### ✨ New Features

#### Image Orientation Filtering
- **`?orientation=landscape|portrait|squarish`** — Filter random images by native aspect ratio. Works on `/300/200`, `/ratio/`, `/preset/`, and `/color/` endpoints. Composes with `?seed` and `?color`. Squarish tolerance configurable via `ORIENTATION_SQUARISH_TOLERANCE` env var (default: `0.15`)

#### SEO & Discoverability
- **Complete SEO overhaul** — conditional meta tags, Open Graph / Twitter Cards, canonical URLs, JSON-LD Schema.org, semantic HTML, and Core Web Vitals optimizations; gated via `seo_enabled` / `site_url` settings
- **Conditional SEO file serving** — `/robots.txt`, `/llms.txt`, and `/sitemap/*` are gated by `seo_enabled`; when disabled, a minimal robots.txt is returned and llms.txt/sitemaps return 404
- **32 language XML sitemaps** with `sitemap-index.xml` master served at `/sitemap`, robots.txt points to the index, and valid `?lang=` hreflang alternates for `/guide` URLs

#### AI Model Discoverability
- **AI crawler coverage** — `robots.txt` allows 28 verified AI crawlers (OpenAI, Anthropic, Google, Apple, Meta, DeepSeek, Kimi, xAI, etc.); `llms.txt` expanded with URL patterns, integration examples, and FAQ

#### Developer Guide
- **New `/guide` page** — multilingual developer documentation with E-E-A-T signals, `TechArticle` structured data, and server-side rendering for 30+ languages with language switcher

#### Multiavatar Integration
- **`/avatar` endpoint now supports `type=multiavatar`** — deterministic multicultural vector avatars via `multiavatar-python`; `type=letter` remains the default


### 🐞 Bug Fixes

- **Avatar PNG fixes** — add transparency (RGBA), centered text with `anchor="mm"`, and fixed edge-quality drawing offsets

### 🔧 Improvements

#### Logging
- **Resource-aware logging** — new `ResourceFormatter` adds millisecond timestamps and per-process resource metrics (CPU time + RSS memory) to every log line

#### Code Quality
- **DeepSource cleanup** — resolved 9 analyzer issues (PYL-W1203, W0612, F821, W0621, W0622, PTC-W0010, R1716, BAN-B607, PTC-W1003) across production and test code
- **Formatting pipeline** — added `format.sh` with `ruff format` and configured `pyproject.toml`

#### Infrastructure
- **Fixed `docker-publish.sh`** - Added explicit tag argument support, proper version sorting, and corrected `docker build` argument order to reliably update the `latest` tag on Docker Hub.

#### Open Source
- **Codecov & badges** - Added test coverage reporting via Codecov and enhanced README with clickable tech stack badges

## v0.2

### 🚀 Introduction

- **Version Number**: 0.2
- **Release Date**: Work In Progress
- **General Overview**: Performance improvements, new image effects, and revamped "URL Builder" UI.

### ✨ New Features

#### Image Processing
- **Rounded corners** - New `radius` parameter to apply rounded corners to images
- **Text overlay positioning** - Support for `text_pos` (top-left, top-right, bottom-left, bottom-right, center)
- **Custom text colors** - `text_color` and `text_bg` parameters for customizable text and background colors
- **Blurhash generation** - New `/api/blurhash/{image_id}` endpoint to generate blurhash strings
- **12 new computer vision filters** - Pencil sketch, cartoon, oil painting, halftone, emboss, sharpen, vignette, invert, brightness, contrast, saturation, duotone, posterize, solarize
- **Avatar generator** - New `/avatar/{size}/{name}` endpoint for letter-based avatars with 6 color palettes (flatui, material, pastel, neon, cool, warm), circle/square shapes, borders, and SVG/PNG output
- **Font loading improvements** - Removed hardcoded DejaVu font dependency; now uses any available system font (.ttf/.ttc) with fallback to PIL default
- **Custom font directory support** - New `FONT_DIR` setting allows users to mount custom fonts for text overlays

#### UI & UX
- **Enhanced URL builder** - Improved interactive URL constructor with real-time preview
- **URL builder sidebar redesign** - Replaced horizontal tabs with vertical icon sidebar styled like design apps, featuring floating fixed positioning, icon-only menu with tooltips, white vertical indicator for active item, and smooth transitions
- **Preview improvements** - Added size overlay badge showing actual dimensions when image is scaled, loading state with grayed image and fade transition, centered loader and image, and changed "Size" label to "Dimension"
- **Explorer improvements** - Better image browsing and filtering UI
- **GDPR compliance** - Added legal links to footer and cookie consent
- **Social network icons** - Added Font Awesome icons to preset dimension capsules for Instagram, YouTube, Facebook, X, LinkedIn, TikTok, and Screens
- **Expanded localization** - Added 5 new languages: Danish, Malay, Hungarian, Bulgarian, and Romanian (total 31 languages)

### 🔧 Improvements

#### Performance & Reliability
- **S3 client reuse** - Singleton S3 client reused across all operations
- **Cache size limit with LRU eviction** - New `cache_max_size_mb` setting with automatic LRU eviction
- **Processing concurrency control** - Asyncio semaphore limits concurrent image processing
- **Leader lock logging** - Defensive logging in lock release to handle closed streams
- **S3 scanning improvements** - All workers now scan S3 for consistency; images at root level are skipped

#### Infrastructure
- **Docker configuration** - Improved Docker build and configuration
- **Homepage layout** - Major improvements to main layout and homepage
- **README** - Improved with less but more focused content

### 🧪 Experimental

- **OVHcloud AI integration** - Generate images using OVHcloud AI Endpoints with rate limiting

### 🐞 Bug Fixes

- **Fixed undefined `is_random`** - Properly set `is_random=False` in `serve_by_id` endpoint
- **Social networks aspect ratio** - Fix aspect ratio in homepage

## v0.1

### 🚀 Introduction

- **Version Number**: 0.1
- **Release Date**: 2026-05-25
- **General Overview**: Initial release with core placeholder image server functionality

### ✨ New Features

#### Core Features
- **Browser Cache Headers** - ETag, Last-Modified, 304 responses, HEAD support
- **Usage Metrics** - SQLite-based tracking with CLI admin
- **Aspect Ratio Sizing** - `/ratio/16:9/1080` for responsive layouts
- **Preset Dimensions** - Social media & ad sizes (Instagram, YouTube, etc.)
- **Solid Color Placeholders** - `/solid/500/300/ff0000` with optional text
- **Border & Padding** - Add borders and padding to images
- **Image Effects** - Noise, pixelate, quality control, LQIP generation, sepia, tint
- **Srcset Generation** - API endpoint for responsive image sets
- **Smart Crop** - OpenCV face detection for intelligent cropping
- **Watermark Overlay** - Image or text watermarks with positioning
- **S3 integration** - Store and serve images from S3 buckets
- **Local file serving** - Serve images from local directories
- **Category support** - Organize images by categories
- **Color-based selection** - Pick images by dominant color
- **Localization** - Support for 26 languages

### 🔧 Improvements

#### Infrastructure
- **Docker support** - Multi-stage Docker build with docker-compose
- **Comprehensive test suite** - Unit tests for all major features with coverage reporting

### 📖 Documentation

- **README** - Complete setup and usage documentation with URL builder
