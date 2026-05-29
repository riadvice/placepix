---
title: Ghidul Dezvoltatorului PlacePix — API de Imagini Placeholder Auto-găzduit și Referință Funcționalități
description: Ghid complet pentru dezvoltatori PlacePix și referință API. Aflați cum să implementați imagini placeholder cu Docker, să generați gradienti și SVG, și să utilizați presetări pentru rețele sociale pentru Instagram, YouTube și altele.
keywords: API imagini placeholder self-hosted, placeholder crop detectare facială, generator placeholder gradient, serviciu imagini placeholder Docker, API placeholder Instagram story, generator placeholder SVG, API imagini dezvoltator
author: RIADVICE
robots: index, follow
og_title: PlacePix Developer Guide — Self-Hosted Placeholder Image API & Feature Reference
og_description: Ghid complet pentru dezvoltatori care acoperă implementarea Docker, decuparea inteligentă, placeholder-ele gradient, generarea SVG și presetările pentru rețele sociale.
twitter_title: PlacePix Developer Guide — Self-Hosted Placeholder Image API & Feature Reference
twitter_description: Ghid complet pentru dezvoltatori care acoperă implementarea Docker, decuparea inteligentă, placeholder-ele gradient, generarea SVG și presetările pentru rețele sociale.
jsonld_name: PlacePix Developer Guide — Self-Hosted Placeholder Image API & Feature Reference
jsonld_description: Ghid complet pentru dezvoltatori și referință API pentru PlacePix, un serviciu self-hosted de imagini placeholder. Acoperă implementarea Docker, decuparea inteligentă cu recunoaștere facială, placeholder-ele gradient, generarea SVG și presetările pentru rețele sociale.
jsonld_proficiency: Expert
jsonld_dependencies: Docker, Python 3.12, FastAPI
header_title: Ghidul Dezvoltatorului PlacePix
header_subtitle: Referință API completă și documentație funcționalități pentru serviciul de imagini placeholder auto-găzduit. Acoperă implementare Docker, decupare inteligentă, placeholder gradient, generare SVG, avatare cu litere și presetări pentru rețele sociale.
author_label: De către
updated_label: "Last updated: May 2026"
github_label: Open Source pe GitHub
toc_title: Cuprins
---

## Ce este PlacePix?

PlacePix este un **serviciu de imagini placeholder auto-găzduit** construit pentru dezvoltatori și echipe de design. Spre deosebire de serviciile placeholder terțe care necesită apeluri de rețea externe și pot dispărea, PlacePix rulează în întregime pe propria infrastructură. Drop imagini în foldere, și obține instant endpoint-uri URL care servesc imagini redimensionate, filtrate și formatate.

Serviciul este scris în Python folosind FastAPI cu procesare de imagini alimentată de Pillow și OpenCV. Acesta acceptă implementare Docker, și stocare de obiecte compatibilă cu S3.

### Caracteristici

- **Configurație zero** — drop imagini în foldere și mergi
- **Decupare conștientă de fețe** — OpenCV detectează și centrează fețele
- **Placeholder gradient și SVG** — nu sunt necesare imagini
- **Presetări pentru rețele sociale** — dimensiuni Instagram, YouTube, TikTok integrate
- **Căutare după culoare** — găsește imagini care se potrivesc cu paleta mărcii tale
- **Avatare cu litere** — imagini de profil deterministe din nume

## Ghid de implementare Docker

Cel mai rapid mod de a rula PlacePix este cu Docker. O singură comandă implementează întregul serviciu cu scanare inteligentă, extracție de culoare, și constructorul de URL încorporat.

### Implementare într-o linie

```bash
docker run -d -p 3000:3000 \
  -v ./images:/app/images \
  riadvice/placepix:latest
```

### Docker Compose (Recomandat)

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

### Date persistente și mediu

Mount both `/app/images` (your image library) and `/app/data` (scan cache and metadata) to preserve state across container restarts. Configure behavior via environment variables or a `.env` file.

### Stocare compatibilă S3 OVHcloud

PlacePix supports any S3-compatible backend. For OVHcloud Object Storage, set:

```
S3_ENABLED=true
S3_ENDPOINT=https://s3.rbx.io.cloud.ovh.net
S3_ACCESS_KEY=your-key
S3_SECRET_KEY=your-secret
S3_BUCKET=your-bucket
S3_REGION=rbx
```

## Decupare inteligentă cu recunoaștere facială

Decuparea standardă de centru poate tăia fețele în fotografia de portret. PlacePix rezolvă acest lucru cu **decupare inteligentă conștientă de fețe** alimentată de cascadelor Haar OpenCV.

### Cum funcționează

Când o solicitare include `?fit=smart`, PlacePix scanează imaginea pentru fețe umane folosind OpenCV. Dacă fețele sunt detectate, fereastra de decupare este deplasată astfel încât centroidul feței să se afle cât mai aproape posibil de punctele de intersecție a raportului de aur. Dacă nu sunt găsite fețe, revine la decuparea standardă de centru.

### Exemple API

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

### Când să folosiți decuparea inteligentă

- Fotografie portret și headshot-uri
- Pagini de echipă unde fețele contează
- Miniaturi pentru social media
- Orice scenariu în care decuparea geometrică de centru strică compoziția

## API pentru placeholder gradient

Generați imagini gradient liniare și radiale on-the-fly fără a încărca nicio resursă. Perfect pentru fundalurile hero, stările de încărcare și mockup-urile de design.

### Sintaxa endpoint-ului

```
/gradient/{width}/{height}/{from_hex}/{to_hex}
```

### Exemple

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

### Referință parametri

- `{from_hex}` / `{to_hex}` — culori hex fără prefixul #
- `?angle=45` — unghi liniar în grade (0-360)
- `?gradient_type=radial` — switches to radial gradient
- `?format=webp` — WebP output (smaller file size)

## Generator de placeholder SVG

SVG placeholder-urile nu necesită procesare de imagini pe partea de server. Sunt generate ca inline SVG cu culoare de fundal, culoare de prim-plan și etichetă text personalizabile.

### Endpoint

```
/svg/{width}/{height}?bg={hex}&fg={hex}&text={label}
```

### Exemple

```
# Default wireframe placeholder
/svg/400/300

# Custom brand colors
/svg/400/300?bg=1c1917&fg=0ea5e9

# With custom text
/svg/400/300?bg=0ea5e9&fg=ffffff&text=Hero+Section
```

### De ce SVG?

- Dimensiune fișier sub 500 de bytes
- Infinit scalabil fără pierdere de calitate
- Zero overhead de procesare pe server
- Perfect pentru wireframe-uri și prototipuri low-fidelity

## Presetări pentru rețele sociale

PlacePix include dimensiuni predefinite pentru platformele sociale populare și dimensiuni de ecran. Folosiți-le pentru a genera imagini placeholder de dimensiuni perfecte pentru Instagram, YouTube, TikTok, LinkedIn, X (Twitter) și afișaje standard.

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

### Dimensiuni Ecran

```
/preset/mobile/nature              # 375x812
/preset/tablet/nature              # 768x1024
/preset/desktop/nature             # 1920x1080
/preset/4k/nature                  # 3840x2160
```

### Caz de Utilizare Long-Tail: Instagram Story API

Dacă construiți un instrument de management al rețelelor sociale și aveți nevoie de **imagini placeholder de dimensiune Instagram story**, utilizați `/preset/instagram-story/{category}`. Combinați cu `?fit=smart` pentru fotografii portret și `?format=webp&quality=70` pentru livrare optimizată.

## API de căutare după culoare

Fiecare imagine din PlacePix este scanată pentru primele 3 culori dominante. Puteți căuta întreaga bibliotecă după culoare hex pentru a găsi imagini care se potrivesc cu paleta mărcii dvs.

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

La pornire, PlacePix extrage cele mai frecvente culori din fiecare imagine folosind gruparea k-means în spațiul de culori LAB. Acest lucru produce potriviri perceptual exacte în loc de medii RGB brute. Pagina paletei (`/palette`) vizualizează aceste culori și vă permite să răsfoiți după categorie de nuanță.

## Filtrare după orientare

Filtrează imaginile aleatoare după raportul lor de aspect nativ înainte de selecție. Acest lucru este util când ai nevoie de imagini care se potrivesc natural într-un layout — peisaj pentru anteturi, portret pentru carduri sau pătrat pentru miniaturi.

### Endpoint-uri

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

### Configurare

Toleranța `squarish` este configurabilă prin variabila de mediu `ORIENTATION_SQUARISH_TOLERANCE` (implicit: `0.15`). O valoare de `0.15` înseamnă că imaginile cu un raport de aspect între `0.85` și `1.15` sunt considerate pătrate. Setează la `0.0` pentru 1:1 exact.

### Cum funcționează

PlacePix citește dimensiunile imaginilor din anteturile fișierelor în timpul scanării inițiale (fișiere locale) și în timpul scanării de metadate în fundal (imagini S3). Dimensiunile sunt stocate în memorie și utilizate pentru a filtra grupul de candidați înainte de selecția aleatoare sau deterministă. Dacă este solicitată o orientare dar nu există imagini potrivite, se returnează `404`.
## Filtre și efecte

Aplicați filtre și efecte real-time la orice imagine prin parametri de interogare. Toată procesarea se face pe partea de server și este cache-ată pentru cererile ulterioare.

### Ajustări de Culoare

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

### Efecte de Imagine

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

### Parametri Overlay

```
?text=Hello+World          # Text overlay
?border=4,ffffff           # Border width & color
?watermark=1               # Apply configured watermark
?padding=20                # Internal padding
```

## Generator de avatare cu litere

Generați avatare bazate pe litere deterministe din orice nume sau e-mail. Perfect pentru placeholder-e de profil utilizator, sisteme de comentarii și directoare de echipă. Fiecare nume produce întotdeauna aceeași culoare, deci avatarele sunt consistente în toate sesiunile.

### Endpoint

```
/avatar/{size}/{name}
/avatar/{size}/{name}.{ext}
```

### Parameters

- `size` — pixel size (e.g. `64`, `128`, `256`)
- `name` — any string; first letters are extracted for the avatar
- `circle` — crop to a circle shape
- `border={width},{color}` — add a border
- `bg={hex}` — override background color
- `fg={hex}` — override text/foreground color
- `single=true` — use only the first letter
- `uppercase=false` — preserve lowercase letters
- `palette={name}` — choose from `flatui`, `material`, `pastel`, or `neon`

### Exemple

```
# Simple 128px avatar
/avatar/128/John+Doe

# Circle avatar with custom border
/avatar/128/John+Doe?circle=true&border=2,ffffff

# Single initial, pastel palette
/avatar/64/Alice?single=true&palette=pastel

# SVG output (scalable, under 500 bytes)
/avatar/128/John+Doe.svg
```

### Why Use Letter Avatars?

- Zero dependențe externe — niciun Gravatar sau serviciu avatar terț
- Determinist — același nume produce întotdeauna aceeași culoare
- Suport SVG — infinit scalabil, perfect pentru afișaje HiDPI
- Patru palete de culori încorporate pentru orice estetică de brand

## Referință rapidă API REST

Toate endpoint-urile suportă CORS și returnează imagini cu headere de cache pe termen lung. Output-ul Base64 JSON este disponibil pentru thumbnails mici.

### Endpoint-uri de Imagini

- `GET /{width}/{height}/{category}` — Random image from category
- `GET /{width}/{height}` — Random image from all categories
- `GET /id/{id}/{width}/{height}` — Specific image by ID
- `GET /ratio/{ratio}/{width}/{category}` — Aspect ratio image
- `GET /preset/{preset}/{category}` — Social media preset
- `GET /color/{hex}/{width}/{height}` — Color-matched image
- `GET /gradient/{w}/{h}/{from}/{to}` — Gradient image
- `GET /svg/{width}/{height}` — SVG placeholder
- `GET /avatar/{size}/{name}` — Letter avatar (PNG/SVG)

### Endpoint-uri de Metadate

- `GET /api/images` — List categories and totals
- `GET /api/info/id/{id}` — Image metadata (dimensions, colors, format)
- `GET /api/color/{hex}` — Images matching a color

### Endpoint-uri de Health

- `GET /health` — Liveness probe (Docker/K8s)
- `GET /ready` — Readiness probe (503 until images loaded)

## Experiență și credențiale

- Active contributors to the open-source ecosystem since 2008
- All code is open source under the MIT License and auditable on <a href="https://github.com/riadvice/placepix" target="_blank" class="text-accent hover:underline">GitHub</a>

## Întrebări frecvente

### Cum implementez PlacePix cu Docker?

Run `docker run -d -p 3000:3000 -v ./images:/app/images riadvice/placepix:latest`. Mount your image folder and the service starts immediately with smart scanning enabled.

### Ce este decuparea inteligentă cu recunoaștere facială?

PlacePix uses OpenCV Haar cascades to detect faces in images. When you add `?fit=smart` to any URL, the crop region is shifted to center on detected faces rather than using geometric center. If no face is found, it falls back to standard center cropping.

### Can I generate gradient placeholder images without uploading photos?

Yes. The `/gradient/{width}/{height}/{from}/{to}` endpoint generates gradient images entirely from URL parameters. No uploaded images are required. You can also create SVG placeholders with `/svg/{width}/{height}`.

### How do I generate Instagram story size placeholder images via API?

Use the preset endpoint: `/preset/instagram-story/{category}`. This returns a 1080x1920 image. Combine with `?format=webp&quality=70` for optimized delivery and `?fit=smart` for portrait-safe cropping.

### PlacePix acceptă stocare de obiecte compatibilă S3?

Yes. PlacePix works with OVHcloud Object Storage, AWS S3, MinIO, and any S3-compatible provider. Configure endpoint, bucket, access key, and secret key via environment variables.

### Ce formate de ieșire sunt acceptate?

WebP, AVIF, JPEG, PNG, SVG, and base64 JSON. Use `.webp`, `.avif`, or `.png` as the file extension, or add `?format=webp` as a query parameter. AVIF produces the smallest files; PNG is lossless.

### PlacePix este gratuit pentru utilizare comercială?

Yes. PlacePix is released under the MIT License and is free for both personal and commercial use. Because it is self-hosted, there are no usage limits, no API keys, and no per-request billing.
