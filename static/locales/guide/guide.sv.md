---
title: PlacePix Utvecklarguide — Självdvärd Placeholder Image API och Funktionsreferens
description: Komplett PlacePix utvecklarguide och API-referens. Lär dig att distribuera placeholder-bilder med Docker, generera gradienter och SVG, och använda förinställningar för sociala medier för Instagram, YouTube och mer.
keywords: API för placeholder-bilder self-hosted, placeholder med ansiktsigenkänning beskärning, generator för gradient-placeholder, Docker-tjänst för placeholder-bilder, API för Instagram story-placeholder, generator för SVG-placeholder, API för utvecklarbilder
author: RIADVICE
robots: index, follow
og_title: PlacePix Utvecklarguide — Självdvärd Placeholder Image API och Funktionsreferens
og_description: Komplett utvecklarguide som täcker Docker-implementering, smart beskärning, gradient-placeholders, SVG-generering och förinställningar för sociala medier.
twitter_title: PlacePix Utvecklarguide — Självdvärd Placeholder Image API och Funktionsreferens
twitter_description: Komplett utvecklarguide som täcker Docker-implementering, smart beskärning, gradient-placeholders, SVG-generering och förinställningar för sociala medier.
jsonld_name: PlacePix Utvecklarguide — Självdvärd Placeholder Image API och Funktionsreferens
jsonld_description: Komplett utvecklarguide och API-referens för PlacePix, en självdvärd placeholder-bildtjänst. Täcker Docker-implementering, ansiktsigenkännande smart beskärning, gradient-placeholders, SVG-generering och förinställningar för sociala medier.
jsonld_proficiency: Expert
jsonld_dependencies: Docker, Python 3.12, FastAPI
header_title: PlacePix Utvecklarguide
header_subtitle: Komplett API-referens och funktionsdokumentation för självdvärd placeholder-bildtjänst. Täcker Docker-implementering, smart beskärning, gradient-placeholders, SVG-generering, bokstavsavatarer och förinställningar för sociala medier.
author_label: Av
updated_label: "Senast uppdaterad: maj 2026"
github_label: Öppen källkod på GitHub
toc_title: Innehållsförteckning
---

## Vad är PlacePix?

PlacePix är en **självdvärd placeholder-bildtjänst** byggd för utvecklare och designteam. Till skillnad från tredjeparts placeholder-tjänster som kräver externa nätverksanrop och kan försvinna, körs PlacePix helt på din egen infrastruktur. Släpp bilder i mappar och få direkt URL-endpoints som serverar storleksändrade, filtrerade och formaterade bilder.

Tjänsten är skriven i Python med FastAPI med bildbehandling driven av Pillow och OpenCV. Den stöder Docker-implementering och S3-kompatibel objektlagring.

### Funktioner

- **Zero konfiguration** — släpp bilder i mappar och kör
- **Ansiktsigenkännande beskärning** — OpenCV detekterar och centrerar ansikten
- **Gradient- och SVG-placeholders** — inga bilder krävs
- **Förinställningar för sociala medier** — Instagram, YouTube, TikTok-storlekar inbyggda
- **Färgsökning** — hitta bilder som matchar ditt varumärkespalett
- **Bokstavsavatarer** — deterministiska profilbilder från namn

## Docker-implementeringsguide

Det snabbaste sättet att köra PlacePix är med Docker. Ett enda kommando distribuerar hela tjänsten med smart skanning, färgekstraktion och den inbyggda URL-byggaren.

### Enrads-implementering

```bash
docker run -d -p 3000:3000 \
  -v ./images:/app/images \
  riadvice/placepix:latest
```

### Docker Compose (Rekommenderat)

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

### Beständiga data och miljö

Montera både `/app/images` (ditt bildbibliotek) och `/app/data` (skanningscache och metadata) för att bevara tillstånd över containrarstarter. Konfigurera beteende via miljövariabler eller en `.env`-fil.

### OVHcloud S3-kompatibel lagring

PlacePix stöder alla S3-kompatibla backends. För OVHcloud Object Storage, ställ in:

```
S3_ENABLED=true
S3_ENDPOINT=https://s3.rbx.io.cloud.ovh.net
S3_ACCESS_KEY=your-key
S3_SECRET_KEY=your-secret
S3_BUCKET=your-bucket
S3_REGION=rbx
```

## Smart beskärning med ansiktsigenkänning

Standard centrum-beskärning kan skära igenom ansikten i porträttfotografi. PlacePix löser detta med **ansiktsigenkännande smart beskärning** driven av OpenCV Haar-kaskader.

### Hur det fungerar

När en begäran inkluderar `?fit=smart`, skannar PlacePix bilden efter mänskliga ansikten med OpenCV. Om ansikten upptäcks, flyttas beskärningsfönstret så att ansiktets centroid ligger så nära som möjligt till gylle-snittpunkterna. Om inga ansikten hittas, återgår det till standard centrum-beskärning.

### API-exempel

```
# Ansiktsigenkännande beskärning (detekterar och centrerar ansikten)
/400/300/people?fit=smart

# Standard centrum-beskärning
/400/300/people?fit=crop

# Omslagsfyllning (kan töja)
/400/300/people?fit=cover

# Innehåll (letterboxing)
/400/300/people?fit=contain
```

### När du ska använda Smart Crop

- Porträttfotografi och headshots
- Teamsidor där ansikten betyder något
- Sociala media-thumbnails
- Varje scenario där geometrisk centrum-beskärning förstör kompositionen

## Gradient placeholder API

Generera linjära och radiala gradientbilder i farten utan att ladda upp tillgångar. Perfekt för hero-bakgrunder, laddningstillstånd och design-mockups.

### Endpoint-syntax

```
/gradient/{width}/{height}/{from_hex}/{to_hex}
```

### Exempel

```
# Enkel linjär gradient (uppifrån och ner)
/gradient/800/400/3b82f6/10b981

# 45-graders vinklad gradient
/gradient/800/400/e11d48/f59e0b?angle=45

# Radial gradient från centrum
/gradient/800/400/1e293b/64748b?gradient_type=radial

# Med utdataformat
/gradient/800/400/0ea5e9/ffffff?format=webp&quality=80
```

### Parameterreferens

- `{from_hex}` / `{to_hex}` — hex-färger utan # prefix
- `?angle=45` — linjär vinkel i grader (0-360)
- `?gradient_type=radial` — växlar till radial gradient
- `?format=webp` — WebP-utdata (mindre filstorlek)

## SVG-placeholder-generator

SVG-placeholders kräver ingen server-side bildbehandling. De genereras som inline SVG med anpassningsbar bakgrundsfärg, förgrundsfärg och textetikett.

### Endpoint

```
/svg/{width}/{height}?bg={hex}&fg={hex}&text={label}
```

### Exempel

```
# Default wireframe placeholder
/svg/400/300

# Custom brand colors
/svg/400/300?bg=1c1917&fg=0ea5e9

# With custom text
/svg/400/300?bg=0ea5e9&fg=ffffff&text=Hero+Section
```

### Varför SVG?

- Filstorlek under 500 bytes
- Oändligt skalbar utan kvalitetsförlust
- Noll serverbehandlings overhead
- Perfekt för wireframes och low-fidelity prototyper

## Förinställningar för sociala medier

PlacePix inkluderar fördefinierade dimensioner för populära sociala plattformar och skärmstorlekar. Använd dessa för att generera perfekt storleksanpassade placeholder-bilder för Instagram, YouTube, TikTok, LinkedIn, X (Twitter) och standarddisplayer.

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

### Skärmstorlekar

```
/preset/mobile/nature              # 375x812
/preset/tablet/nature              # 768x1024
/preset/desktop/nature             # 1920x1080
/preset/4k/nature                  # 3840x2160
```

### Long-Tail Användningsfall: Instagram Story API

Om du bygger ett sociala media-hanteringsverktyg och behöver **Instagram story-storlek placeholder-bilder**, använd `/preset/instagram-story/{category}`. Kombinera med `?fit=smart` för porträttfoton och `?format=webp&quality=70` för optimerad leverans.


## Orienteringsfilter

Filtrera slumpmässiga bilder efter deras ursprungliga bildförhållande före urval. Detta är användbart när du behöver bilder som naturligt passar in i en layout — landskap för rubriker, porträtt för kort eller kvadratisk för miniatyrbilder.

### Slutpunkter

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

### Konfiguration

`squarish`-toleransen kan konfigureras via miljövariabeln `ORIENTATION_SQUARISH_TOLERANCE` (standard: `0.15`). Ett värde på `0.15` innebär att bilder med ett bildförhållande mellan `0.85` och `1.15` betraktas som kvadratiska. Ställ in på `0.0` för exakt 1:1.

### Hur det fungerar

PlacePix läser bilddimensioner från filhuvuden under den initiala skanningen (lokala filer) och under bakgrundsskanningen av metadata (S3-bilder). Dimensionerna lagras i minnet och används för att filtrera kandidatpoolen före slumpmässigt eller seed-baserat urval. Om en orientering begärs men inga bilder matchar, returneras en `404`.
## Filter och effekter

Tillämpa realtidsfilter och effekter på vilken bild som helst via query-parametrar. All bearbetning sker server-side och cachelagras för efterföljande begäranden.

### Färganpassningar

```
?grayscale=1               # Svartvit
?sepia=1                   # Varm sepia-ton
?tint=0ea5e9               # Hex-färg overlay
?brightness=1.3            # 0,0 till 2,0
?contrast=1.2              # 0,0 till 2,0
?saturation=2.0            # 0,0 till 2,0
?invert=true               # Invertera färger
?posterize=4               # Färgnivåer (1-8)
?duotone=ff0000,0000ff     # Två-färgskarta
```

### Bildeffekter

```
?blur=2                    # Gaussisk oskärpa (1-10)
?sharpen=1.5               # Skärpningsmängd
?emboss=true               # 3D-relief
?edges=sobel               # Kantdetektion
?edges=canny               # Canny-kanter
?halftone=4                # Prickmönster
?oil_painting=true         # Oljemålningsstil
?pencil_sketch=true        # Penn-skiss
?cartoon=true              # Cartoon-effekt
?vignette=0.5              # Mörkna kanter (0-1)
```

### Overlay-parametrar

```
?text=Hello+World          # Text-overlay
?border=4,ffffff           # Kantbredd & färg
?watermark=1               # Tillämpa konfigurerat vattenstämpel
?padding=20                # Intern utfyllnad
```

## Avatar Generator

Generera deterministiska avatarer från vilket namn eller e-post som helst. PlacePix stöder två avatar-typer: **Bokstavsavatar** (färgade initialer) och **Multiavatar** (multikulturella vektor-avatarer).

### Endpoint

```
/avatar/{size}/{name}
/avatar/{size}/{name}.{ext}
```

### Parametrar

- `type` — avatar type: `letter` (default) or `multiavatar`
- `size` — pixel size (e.g. `64`, `128`, `256`)
- `name` — any string; used as seed for the avatar

#### Bokstavsavatar (`type=letter`)

- `circle` — crop to a circle shape
- `border={width}` — lägg till en kantlinje
- `border_color={hex}` — kantlinjefärg
- `bg={hex}` — override background color
- `fg={hex}` — override text/foreground color
- `single=true` — use only the first letter
- `uppercase=false` — preserve lowercase letters
- `palette={name}` — choose from `flatui`, `material`, `pastel`, `neon`, `cool`, `warm`

#### Multiavatar (`type=multiavatar`)

- `env` — include environment background (`true` by default, `false` to omit)
- `part` — specific part code (optional, e.g. `11`)
- `theme` — specific theme code (optional, e.g. `C`)

### Exempel

```
# Simple 128px letter avatar
/avatar/128/John+Doe

# Circle letter avatar with custom border
/avatar/128/John+Doe?circle=true&border=2&border_color=ffffff

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

### Varför använda bokstavsavatarer?

- Noll externa beroenden — ingen Gravatar eller avatar-tjänst från tredje part
- Deterministisk — samma namn producerar alltid samma färg
- SVG-stöd — oändligt skalbar, perfekt för HiDPI-skärmar
- Sex inbyggda färgpaletter för alla varumärkesestetiker

### Varför använda Multiavatar?

- 12 miljarder unika multikulturella avatarer
- Deterministisk — samma namn producerar alltid samma avatar
- Ren SVG-utdata — liten filstorlek, oändligt skalbar
- Inga externa API-anrop krävs

## REST API-snabbreferens

Alla endpoints stöder CORS och returnerar bilder med långsiktiga cache-headers. Base64 JSON-utdata är tillgänglig för små thumbnails.

### Bild-endpoints

- `GET /{width}/{height}/{category}` — Slumpmässig bild från kategori
- `GET /{width}/{height}` — Slumpmässig bild från alla kategorier
- `GET /id/{id}/{width}/{height}` — Specifik bild efter ID
- `GET /ratio/{ratio}/{width}/{category}` — Bildförhållandebild
- `GET /preset/{preset}/{category}` — Sociala media-preset
- `GET /color/{hex}/{width}/{height}` — Färgmatchad bild
- `GET /gradient/{w}/{h}/{from}/{to}` — Gradient-bild
- `GET /svg/{width}/{height}` — SVG-placeholder
- `GET /avatar/{size}/{name}` — Bokstavsavatar (PNG/SVG)

### Metadata-endpoints

- `GET /api/images` — Lista kategorier och totaler
- `GET /api/info/id/{id}` — Bild-metadata (dimensioner, färger, format)
- `GET /api/color/{hex}` — Bilder som matchar en färg

### Hälsa-endpoints

- `GET /health` — Liveness probe (Docker/K8s)
- `GET /ready` — Readiness probe (503 tills bilder laddade)

## Kompetens och referenser

- Aktiva bidragsgivare till open-source-ekosystemet sedan 2008
- All kod är open source under MIT-licensen och kan granskas på <a href="https://github.com/riadvice/placepix" target="_blank" class="text-accent hover:underline">GitHub</a>

## Vanliga frågor

### Hur distribuerar jag PlacePix med Docker?

Kör `docker run -d -p 3000:3000 -v ./images:/app/images riadvice/placepix:latest`. Montera din bildmapp och tjänsten startar omedelbart med smart skanning aktiverad.

### Vad är smart beskärning med ansiktsigenkänning?

PlacePix använder OpenCV Haar-kaskader för att upptäcka ansikten i bilder. När du lägger till `?fit=smart` till vilken URL som helst, flyttas beskärningsområdet för att centrera på upptäckta ansikten istället för att använda geometriskt centrum. Om inget ansikte hittas, återgår det till standard centrum-beskärning.

### Kan jag generera gradient-placeholder-bilder utan att ladda upp foton?

Ja. `/gradient/{width}/{height}/{from}/{to}`-endpointen genererar gradient-bilder helt från URL-parametrar. Inga uppladdade bilder krävs. Du kan också skapa SVG-placeholders med `/svg/{width}/{height}`.

### Hur genererar jag Instagram story-storlek placeholder-bilder via API?

Använd preset-endpointen: `/preset/instagram-story/{category}`. Detta returnerar en 1080x1920-bild. Kombinera med `?format=webp&quality=70` för optimerad leverans och `?fit=smart` för porträtt-säker beskärning.

### Stöder PlacePix S3-kompatibel objektlagring?

Ja. PlacePix fungerar med OVHcloud Object Storage, AWS S3, MinIO och alla S3-kompatibla leverantörer. Konfigurera endpoint, bucket, åtkomstnyckel och hemlig nyckel via miljövariabler.

### Vilka utdataformat stöds?

WebP, AVIF, JPEG, PNG, SVG och base64 JSON. Använd `.webp`, `.avif` eller `.png` som filändelse, eller lägg till `?format=webp` som query-parameter. AVIF producerar de minsta filerna; PNG är förlustfri.

## Är PlacePix gratis för kommersiell användning?

Ja. PlacePix släpps under MIT-licensen och är gratis för både personligt och kommersiellt bruk. Eftersom det är självdvärt finns det inga användningsgränser, inga API-nycklar och ingen fakturering per begäran.