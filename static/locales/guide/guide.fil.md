---
title: Gabay sa Developer ng PlacePix — Self-Hosted Placeholder Image API at Feature Reference
description: Kumpletong gabay sa developer ng PlacePix at reference sa API. Matuto kung paano i-deploy ang mga placeholder na larawan gamit ang Docker, bumuo ng gradient at SVG, at gumamit ng mga preset sa social media para sa Instagram, YouTube, at higit pa.
keywords: API ng placeholder na larawan self-hosted, placeholder sa pag-crop na face-aware, generator ng gradient placeholder, serbisyo sa placeholder na larawan ng Docker, API ng Instagram story placeholder, generator ng SVG placeholder, API ng larawan para sa developer
author: RIADVICE
robots: index, follow
og_title: Gabay sa Developer ng PlacePix — Self-Hosted Placeholder Image API at Feature Reference
og_description: Kumpletong gabay sa developer na sumasaklaw sa Docker deployment, smart crop, gradient placeholder, paggawa ng SVG, at mga preset sa social media.
twitter_title: Gabay sa Developer ng PlacePix — Self-Hosted Placeholder Image API at Feature Reference
twitter_description: Kumpletong gabay sa developer na sumasaklaw sa Docker deployment, smart crop, gradient placeholder, paggawa ng SVG, at mga preset sa social media.
jsonld_name: Gabay sa Developer ng PlacePix — Self-Hosted Placeholder Image API at Feature Reference
jsonld_description: Kumpletong gabay sa developer at reference sa API para sa PlacePix, isang self-hosted na serbisyo ng placeholder na larawan. Sumasaklaw sa Docker deployment, smart crop na may face detection, gradient placeholder, paggawa ng SVG, at mga preset sa social media.
jsonld_proficiency: Expert
jsonld_dependencies: Docker, Python 3.12, FastAPI
header_title: Gabay sa Developer ng PlacePix
header_subtitle: Kumpletong reference sa API at dokumentasyon ng mga tampok para sa self-hosted na serbisyo ng placeholder na larawan. Saklaw ang pag-deploy gamit ang Docker, smart crop, gradient placeholder, paggawa ng SVG, avatar na letra, at mga preset sa social media.
author_label: Ni
updated_label: "Huling na-update: Mayo 2026"
github_label: Open Source sa GitHub
toc_title: Talaan ng Nilalaman
---

## Ano ang PlacePix?

Ang PlacePix ay isang **self-hosted na serbisyo ng placeholder na larawan** na ginawa para sa mga developer at design team. Hindi tulad ng mga serbisyo ng placeholder ng third-party na nangangailangan ng external network calls at maaaring mawala, ang PlacePix ay tumatakbo nang buo sa iyong sariling imprastraktura. Ilagay ang mga larawan sa mga folder, at agad na makakakuha ng URL endpoints na naglilingkod ng mga resized, filtered, at formatted na larawan.

Ang serbisyo ay isinulat sa Python gamit ang FastAPI na may image processing na pinapagana ng Pillow at OpenCV. Sumusuporta ito sa Docker deployment, at S3-compatible na object storage.

### Mga Tampok

- **Zero configuration** — ilagay ang mga larawan sa mga folder at go
- **Face-aware cropping** — Ang OpenCV ay nagdedetect at nagce-center ng mga mukha
- **Gradient at SVG placeholder** — hindi kailangan ng mga larawan
- **Mga preset sa social media** — Instagram, YouTube, TikTok sizes built-in
- **Color search** — hanapin ang mga larawang tumutugma sa palette ng iyong brand
- **Avatar na letra** — deterministic na profile images mula sa mga pangalan

## Gabay sa Pag-deploy ng Docker

Ang pinakamabilis na paraan para patakbuhin ang PlacePix ay gamit ang Docker. Isang command lang ang nagde-deploy ng buong serbisyo na may smart scanning, color extraction, at ang embedded URL builder.

### Isang Linya na Deployment

```bash
docker run -d -p 3000:3000 \
  -v ./images:/app/images \
  riadvice/placepix:latest
```

### Docker Compose (Inirerekomenda)

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

### Matibay na Data at Kapaligiran

I-mount pareho ang `/app/images` (iyong library ng larawan) at `/app/data` (scan cache at metadata) para mapreserba ang estado sa mga container restart. I-configure ang pag-uugali sa pamamagitan ng mga environment variable o isang `.env` file.

### OVHcloud S3-Compatible na Storage

Sinusuportahan ng PlacePix ang anumang S3-compatible na backend. Para sa OVHcloud Object Storage, itakda ang:

```
S3_ENABLED=true
S3_ENDPOINT=https://s3.rbx.io.cloud.ovh.net
S3_ACCESS_KEY=your-key
S3_SECRET_KEY=your-secret
S3_BUCKET=your-bucket
S3_REGION=rbx
```

## Smart Cropping na may Face Awareness

Ang standard na center cropping ay maaaring hiwaan ang mga mukha sa portrait photography. Inaayos ito ng PlacePix sa pamamagitan ng **smart cropping na may face awareness** na pinapagana ng OpenCV Haar cascades.

### Paano ito Gumagana

Kapag ang isang request ay may `?fit=smart`, ini-scan ng PlacePix ang larawan para sa mga human face gamit ang OpenCV. Kung may mga mukhang nadetect, ang crop window ay inilipat para ang face centroid ay malapit sa golden-ratio intersection points. Kung walang mukhang nahanap, bumabalik ito sa standard na center cropping.

### Mga Halimbawa ng API

```
# Face-aware crop (nagde-detect at nagce-center ng mga mukha)
/400/300/people?fit=smart

# Standard na center crop
/400/300/people?fit=crop

# Cover fill (maaaring mastretch)
/400/300/people?fit=cover

# Contain (letterboxing)
/400/300/people?fit=contain
```

### Kailangang Gamitin ang Smart Crop

- Portrait photography at headshots
- Mga team page kung saan mahalaga ang mga mukha
- Mga thumbnail sa social media
- Anumang scenario kung saan ang geometric center cropping ay sumisira sa composition

## API ng Gradient Placeholder

Bumuo ng mga linear at radial gradient na larawan on-the-fly nang hindi nag-uupload ng anumang assets. Perpekto para sa hero backgrounds, loading states, at design mockups.

### Syntaks ng Endpoint

```
/gradient/{width}/{height}/{from_hex}/{to_hex}
```

### Mga Halimbawa

```
# Simpleng linear gradient (mula taas pababa)
/gradient/800/400/3b82f6/10b981

# 45-degree na angled gradient
/gradient/800/400/e11d48/f59e0b?angle=45

# Radial gradient mula sa gitna
/gradient/800/400/1e293b/64748b?gradient_type=radial

# May output format
/gradient/800/400/0ea5e9/ffffff?format=webp&quality=80
```

### Sanggunian sa Parameter

- `{from_hex}` / `{to_hex}` — hex colors nang walang # prefix
- `?angle=45` — linear angle sa degrees (0-360)
- `?gradient_type=radial` — lumilipat sa radial gradient
- `?format=webp` — WebP output (mas maliit na file size)

## Tagabuo ng SVG Placeholder

Ang mga SVG placeholder ay hindi nangangailangan ng server-side image processing. Sila ay generated bilang inline SVG na may customizable background color, foreground color, at text label.

### Endpoint

```
/svg/{width}/{height}?bg={hex}&fg={hex}&text={label}
```

### Mga Halimbawa

```
# Default na wireframe placeholder
/svg/400/300

# Custom brand colors
/svg/400/300?bg=1c1917&fg=0ea5e9

# May custom text
/svg/400/300?bg=0ea5e9&fg=ffffff&text=Hero+Section
```

### Bakit SVG?

- File size sa ilalim ng 500 bytes
- Infinitely scalable nang walang quality loss
- Zero server processing overhead
- Perpekto para sa wireframes at low-fidelity prototypes

## Mga Preset sa Social Media

Ang PlacePix ay may mga predefined dimensions para sa mga popular na social platform at screen sizes. Gamitin ang mga ito para mag-generate ng perfectly-sized placeholder images para sa Instagram, YouTube, TikTok, LinkedIn, X (Twitter), at standard displays.

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

### Mga Laki ng Screen

```
/preset/mobile/nature              # 375x812
/preset/tablet/nature              # 768x1024
/preset/desktop/nature             # 1920x1080
/preset/4k/nature                  # 3840x2160
```

### Long-Tail Use Case: Instagram Story API

Kung gumagawa ka ng social media management tool at kailangan mo ng **Instagram story size placeholder images**, gamitin ang `/preset/instagram-story/{category}`. I-combine with `?fit=smart` para sa portrait photos at `?format=webp&quality=70` para sa optimized delivery.

## Color Search API

Bawat larawan sa PlacePix ay ini-scan para sa 3 dominant colors nito. Maaari mong i-search ang buong library gamit ang hex color para makahanap ng mga larawang tumutugma sa palette ng iyong brand.

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

Sa startup, ang PlacePix ay kumukuha ng pinakamadalas na mga kulay mula sa bawat larawan gamit ang k-means clustering sa LAB color space. Ito ay gumagawa ng perceptually accurate matches sa halip na raw RGB averages. Ang palette page (`/palette`) ay nag-visualize ng mga kulay na ito at nagbibigay-daan sa pag-browse ayon sa kategorya ng hue.

## Mga Filter at Epekto

Ilapat ang mga real-time filter at epekto sa anumang larawan sa pamamagitan ng query parameters. Lahat ng processing ay ginagawa sa server-side at naka-cache para sa mga susunod na kahilingan.

### Mga Pag-aayos ng Kulay

```
?grayscale=1               # Black & white
?sepia=1                   # Warm na sepia tone
?tint=0ea5e9               # Hex color overlay
?brightness=1.3            # 0.0 hanggang 2.0
?contrast=1.2              # 0.0 hanggang 2.0
?saturation=2.0            # 0.0 hanggang 2.0
?invert=true               # Invert colors
?posterize=4               # Mga antas ng kulay (1-8)
?duotone=ff0000,0000ff     # Two-color map
```

### Mga Epekto ng Larawan

```
?blur=2                    # Gaussian blur (1-10)
?sharpen=1.5               # Halaga ng sharpen
?emboss=true               # 3D relief
?edges=sobel               # Edge detection
?edges=canny               # Canny edges
?halftone=4                # Dot pattern
?oil_painting=true         # Oil painting style
?pencil_sketch=true        # Pencil sketch
?cartoon=true              # Cartoon effect
?vignette=0.5              # Darken edges (0-1)
```

### Mga Parameter ng Overlay

```
?text=Hello+World          # Text overlay
?border=4,ffffff           # Lapad at kulay ng border
?watermark=1               # Ilapat ang naka-configure na watermark
?padding=20                # Internal padding
```

## Tagabuo ng Avatar na Letra

Bumuo ng mga deterministic na avatar na nakabase sa letra mula sa anumang pangalan o email. Perpekto para sa user profile placeholders, comment systems, at team directories. Ang bawat pangalan ay laging nagpuproduce ng parehong kulay, kaya ang mga avatar ay consistent sa lahat ng session.

### Endpoint

```
/avatar/{size}/{name}
/avatar/{size}/{name}.{ext}
```

### Mga Parameter

- `size` — pixel size (e.g. `64`, `128`, `256`)
- `name` — any string; first letters are extracted for the avatar
- `circle` — crop to a circle shape
- `border={width},{color}` — add a border
- `bg={hex}` — override background color
- `fg={hex}` — override text/foreground color
- `single=true` — use only the first letter
- `uppercase=false` — preserve lowercase letters
- `palette={name}` — choose from `flatui`, `material`, `pastel`, or `neon`

### Mga Halimbawa

```
# Simpleng 128px avatar
/avatar/128/John+Doe

# Circle avatar na may custom border
/avatar/128/John+Doe?circle=true&border=2,ffffff

# Single initial, pastel palette
/avatar/64/Alice?single=true&palette=pastel

# SVG output (scalable, under 500 bytes)
/avatar/128/John+Doe.svg
```

### Bakit Gumamit ng Avatar na Letra?

- Zero external dependencies — walang Gravatar o avatar service ng third-party
- Deterministic — ang parehong pangalan ay laging nagpuproduce ng parehong kulay
- SVG support — infinitely scalable, perpekto para sa HiDPI displays
- Four built-in color palettes para sa anumang brand aesthetic

## Mabilis na Sanggunian sa REST API

Lahat ng endpoints ay sumusuporta sa CORS at nagre-return ng mga larawan na may long-term cache headers. Base64 JSON output ay available para sa mga maliit na thumbnail.

### Mga Endpoint ng Larawan

- `GET /{width}/{height}/{category}` — Random na larawan mula sa kategorya
- `GET /{width}/{height}` — Random na larawan mula sa lahat ng kategorya
- `GET /id/{id}/{width}/{height}` — Tiyak na larawan ayon sa ID
- `GET /ratio/{ratio}/{width}/{category}` — Aspect ratio na larawan
- `GET /preset/{preset}/{category}` — Social media preset
- `GET /color/{hex}/{width}/{height}` — Color-matched na larawan
- `GET /gradient/{w}/{h}/{from}/{to}` — Gradient na larawan
- `GET /svg/{width}/{height}` — SVG placeholder
- `GET /avatar/{size}/{name}` — Avatar na letra (PNG/SVG)

### Mga Endpoint ng Metadata

- `GET /api/images` — Listahan ng mga kategorya at total
- `GET /api/info/id/{id}` — Metadata ng larawan (dimension, kulay, format)
- `GET /api/color/{hex}` — Mga larawang tumutugma sa kulay

### Mga Health Endpoint

- `GET /health` — Liveness probe (Docker/K8s)
- `GET /ready` — Readiness probe (503 hanggang ma-load ang mga larawan)

## Kasanayan at Kredensyal

- Mga aktibong contributor sa open-source ecosystem mula 2008
- Lahat ng code ay open source sa ilalim ng MIT License at naaudit sa <a href="https://github.com/riadvice/placepix" target="_blank" class="text-accent hover:underline">GitHub</a>

## Mga Madalas na Tanong

### Paano ko ide-deploy ang PlacePix gamit ang Docker?

I-run `docker run -d -p 3000:3000 -v ./images:/app/images riadvice/placepix:latest`. I-mount ang iyong image folder at ang serbisyo ay agad na mag-start na may smart scanning na naka-enable.

### Ano ang smart cropping na may face awareness?

Ang PlacePix ay gumagamit ng OpenCV Haar cascades para ma-detect ang mga mukha sa mga larawan. Kapag nagdagdag ka ng `?fit=smart` sa anumang URL, ang crop region ay inilipat para mag-center sa mga detected na mukha sa halip na gumamit ng geometric center. Kung walang mukha na nahanap, bumabalik ito sa standard na center cropping.

### Maaari ba akong gumawa ng mga gradient placeholder na larawan nang hindi nag-a-upload ng mga larawan?

Oo. Ang `/gradient/{width}/{height}/{from}/{to}` endpoint ay gumagawa ng mga gradient na larawan nang buo mula sa URL parameters. Walang kailangang mga uploaded na larawan. Maaari ka ring gumawa ng mga SVG placeholder gamit ang `/svg/{width}/{height}`.

### Paano ako gumagawa ng mga Instagram story size placeholder na larawan sa pamamagitan ng API?

Gamitin ang preset endpoint: `/preset/instagram-story/{category}`. Ito ay nagre-return ng 1080x1920 na larawan. I-combine with `?format=webp&quality=70` para sa optimized delivery at `?fit=smart` para sa portrait-safe cropping.

### Sinusuportahan ba ng PlacePix ang S3-compatible na object storage?

Oo. Ang PlacePix ay gumagana kasama ang OVHcloud Object Storage, AWS S3, MinIO, at anumang S3-compatible provider. I-configure ang endpoint, bucket, access key, at secret key sa pamamagitan ng mga environment variable.

### Ano ang mga suportadong format ng output?

WebP, AVIF, JPEG, PNG, SVG, at base64 JSON. Gamitin ang `.webp`, `.avif`, o `.png` bilang file extension, o magdagdag ng `?format=webp` bilang query parameter. Ang AVIF ay nagpuproduce ng pinakamaliit na mga file; ang PNG ay lossless.

### Libre ba ang PlacePix para sa komersyal na paggamit?

Oo. Ang PlacePix ay inilabas sa ilalim ng MIT License at libre para sa parehong personal at komersyal na paggamit. Dahil ito ay self-hosted, walang mga limitasyon sa paggamit, walang API keys, at walang per-request billing.
