# Release Notes

## Released versions

- [v0.2 - Work In Progress](#v02)
- [v0.1 - 2026-05-25](#v01)

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
