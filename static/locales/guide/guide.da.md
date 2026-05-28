---
title: PlacePix Udviklerguide — Selvhostet Placeholder Image API og Funktionsreference
description: Komplet PlacePix udviklerguide og API-reference. Lær at implementere placeholder-billeder med Docker, generere gradienter og SVG, og bruge sociale medie-forudindstillinger til Instagram, YouTube og mere.
keywords: API til placeholder-billeder self-hosted, placeholder med ansigtsgenkendelse beskæring, generator til gradient-placeholder, Docker-tjeneste til placeholder-billeder, API til Instagram story-placeholder, generator til SVG-placeholder, API til udviklerbilleder
author: RIADVICE
robots: index, follow
og_title: PlacePix Udviklerguide — Selvhostet Placeholder Image API og Funktionsreference
og_description: Komplet udviklerguide dækker Docker-implementering, smart beskæring, gradient-placeholdere, SVG-generering og sociale medie-forudindstillinger.
twitter_title: PlacePix Udviklerguide — Selvhostet Placeholder Image API og Funktionsreference
twitter_description: Komplet udviklerguide dækker Docker-implementering, smart beskæring, gradient-placeholdere, SVG-generering og sociale medie-forudindstillinger.
jsonld_name: PlacePix Udviklerguide — Selvhostet Placeholder Image API og Funktionsreference
jsonld_description: Komplet udviklerguide og API-reference for PlacePix, en selvhostet placeholder-billedtjeneste. Dækker Docker-implementering, ansigtsgenkendende smart beskæring, gradient-placeholdere, SVG-generering og sociale medie-forudindstillinger.
jsonld_proficiency: Expert
jsonld_dependencies: Docker, Python 3.12, FastAPI
header_title: PlacePix Udviklerguide
header_subtitle: Komplet API-reference og funktionsdokumentation for selvhostet placeholder-billedtjeneste. Dækker Docker-implementering, smart beskæring, gradient-placeholdere, SVG-generering, bogstav-avatarer og sociale medie-forudindstillinger.
author_label: Af
updated_label: "Sidst opdateret: maj 2026"
github_label: Open Source på GitHub
toc_title: Indholdsfortegnelse
---

## Hvad er PlacePix?

PlacePix er en **selvhostet placeholder-billedtjeneste** bygget til udviklere og designteams. I modsætning til third-party placeholder-tjenester, der kræver eksterne netværkskald og kan forsvinde, kører PlacePix helt på din egen infrastruktur. Smid billeder i mapper, og få øjeblikkeligt URL-endpoints, der serverer størrelsesændrede, filtrerede og formaterede billeder.

Tjenesten er skrevet i Python med FastAPI med billedbehandling drevet af Pillow og OpenCV. Den understøtter Docker-implementering og S3-kompatibel objekt-lagring.

### Funktioner

- **Zero konfiguration** — smid billeder i mapper og kør
- **Ansigtsgenkendende beskæring** — OpenCV detekterer og centrerer ansigter
- **Gradient- og SVG-placeholdere** — ingen billeder krævet
- **Sociale medie-forudindstillinger** — Instagram, YouTube, TikTok-størrelser indbyggede
- **Farvesøgning** — find billeder, der matcher dit brand-palet
- **Bogstav-avatarer** — deterministiske profilbilleder fra navne

## Docker-implementeringsguide

Den hurtigste måde at køre PlacePix på er med Docker. En enkelt kommando implementerer hele tjenesten med smart scanning, farve-ekstraktion og den indbyggede URL-builder.

### Enlinjes-implementering

```bash
docker run -d -p 3000:3000 \
  -v ./images:/app/images \
  riadvice/placepix:latest
```

### Docker Compose (Anbefalet)

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

### Vedvarende data og miljø

Mount både `/app/images` (dit billedbibliotek) og `/app/data` (scan-cache og metadata) for at bevare tilstanden på tværs af container-genstarter. Konfigurer adfærd via miljøvariabler eller en `.env`-fil.

### OVHcloud S3-kompatibel lagring

PlacePix understøtter ethvert S3-kompatibelt backend. For OVHcloud Object Storage, sæt:

```
S3_ENABLED=true
S3_ENDPOINT=https://s3.rbx.io.cloud.ovh.net
S3_ACCESS_KEY=your-key
S3_SECRET_KEY=your-secret
S3_BUCKET=your-bucket
S3_REGION=rbx
```

## Ansigtsbevidst smart beskæring

Standard center-beskæring kan skære gennem ansigter i portrætfotografering. PlacePix løser dette med **ansigtsbevidst smart beskæring** drevet af OpenCV Haar-kaskader.

### Sådan fungerer det

Når en forespørgsel inkluderer `?fit=smart`, skanner PlacePix billedet for menneskelige ansigter ved hjælp af OpenCV. Hvis ansigter opdages, flyttes beskæringsvinduet, så ansigtscentroiden ligger så tæt som muligt på gylle-snittets skæringspunkter. Hvis ingen ansigter findes, falder det tilbage til standard center-beskæring.

### API-eksempler

```
# Ansigtsbevidst beskæring (opdager og centrerer ansigter)
/400/300/people?fit=smart

# Standard center-beskæring
/400/300/people?fit=crop

# Cover-udfyldning (kan strække)
/400/300/people?fit=cover

# Indehold (letterboxing)
/400/300/people?fit=contain
```

### Hvornår man skal bruge Smart Crop

- Portrætfotografering og headshots
- Teamsider hvor ansigter betyder noget
- Sociale media-thumbnails
- Ethvert scenarie hvor geometrisk center-beskæring ødelægger kompositionen

## API for gradient placeholder

Generer lineære og radiale gradient-billeder on-the-fly uden at uploade aktiver. Perfekt til hero-baggrunde, loading-tilstande og design-mockups.

### Endepunkt-syntaks

```
/gradient/{width}/{height}/{from_hex}/{to_hex}
```

### Eksempler

```
# Enkel lineær gradient (oppefra og ned)
/gradient/800/400/3b82f6/10b981

# 45-graders vinklet gradient
/gradient/800/400/e11d48/f59e0b?angle=45

# Radial gradient fra centrum
/gradient/800/400/1e293b/64748b?gradient_type=radial

# Med output-format
/gradient/800/400/0ea5e9/ffffff?format=webp&quality=80
```

### Parameterreference

- `{from_hex}` / `{to_hex}` — hex-farver uden # præfikset
- `?angle=45` — lineær vinkel i grader (0-360)
- `?gradient_type=radial` — skifter til radial gradient
- `?format=webp` — WebP-output (mindre filstørrelse)

## SVG-placeholder-generator

SVG-placeholdere kræver nul server-side billedbehandling. De genereres som inline SVG med tilpasselig baggrundsfarve, forgrundsfarve og tekstmærkat.

### Endepunkt

```
/svg/{width}/{height}?bg={hex}&fg={hex}&text={label}
```

### Eksempler

```
# Standard wireframe-placeholder
/svg/400/300

# Tilpassede brandfarver
/svg/400/300?bg=1c1917&fg=0ea5e9

# Med tilpasset tekst
/svg/400/300?bg=0ea5e9&fg=ffffff&text=Hero+Section
```

### Hvorfor SVG?

- Filstørrelse under 500 bytes
- Uendeligt skalerbar uden kvalitetstab
- Nul serverbehandlingsoverhead
- Perfekt til wireframes og low-fidelity prototyper

## Sociale medie-forudindstillinger

PlacePix inkluderer foruddefinerede dimensioner for populære sociale platforme og skærmstørrelser. Brug disse til at generere perfekt dimensionerede placeholder-billeder til Instagram, YouTube, TikTok, LinkedIn, X (Twitter) og standarddisplays.

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

### Skærmstørrelser

```
/preset/mobile/nature              # 375x812
/preset/tablet/nature              # 768x1024
/preset/desktop/nature             # 1920x1080
/preset/4k/nature                  # 3840x2160
```

### Long-Tail Brugsscenarie: Instagram Story API

Hvis du bygger et social media-managementværktøj og har brug for **Instagram story-størrelse placeholder-billeder**, brug `/preset/instagram-story/{category}`. Kombiner med `?fit=smart` til portrætfotos og `?format=webp&quality=70` for optimeret levering.

## Farvesøgnings-API

Hvert billede i PlacePix skannes for dets 3 dominerende farver. Du kan søge i hele biblioteket efter hex-farve for at finde billeder, der matcher dit brand-palet.

### Endepunkts

```
# Get an image matching a specific hex color
/color/0ea5e9/400/300

# Filter any endpoint by dominant color
/400/300/nature?color=d97706

# List all images matching a color
/api/color/3b82f6
```

### How Color Scanning Works

Ved opstart ekstraherer PlacePix de mest hyppige farver fra hvert billede ved hjælp af k-means clustering i LAB-farverum. Dette producerer perceptuelt nøjagtige matches snarere end rå RGB-gennemsnit. Palettesiden (`/palette`) visualiserer disse farver og lader dig bladre efter farvetonekategori.

## Filtre og effekter

Anvend real-time filtre og effekter på ethvert billede via query-parametre. Al behandling sker server-side og caches for efterfølgende anmodninger.

### Farvejusteringer

```
?grayscale=1               # Sort-hvid
?sepia=1                   # Varm sepia-tone
?tint=0ea5e9               # Hex-farve overlay
?brightness=1.3            # 0,0 til 2,0
?contrast=1.2              # 0,0 til 2,0
?saturation=2.0            # 0,0 til 2,0
?invert=true               # Inverter farver
?posterize=4               # Farveniveauer (1-8)
?duotone=ff0000,0000ff     # To-farvekort
```

### Billed-effekter

```
?blur=2                    # Gaussisk sløring (1-10)
?sharpen=1.5               # Skærpningsmængde
?emboss=true               # 3D-relief
?edges=sobel               # Kantdetektion
?edges=canny               # Canny-kanter
?halftone=4                # Prik-mønster
?oil_painting=true         # Oliemaleri-stil
?pencil_sketch=true        # Blyantsketch
?cartoon=true              # Cartoon-effekt
?vignette=0.5              # Mørkne kanter (0-1)
```

### Overlay-parametre

```
?text=Hello+World          # Tekst-overlay
?border=4,ffffff           # Kantbredde & farve
?watermark=1               # Anvend konfigureret vandmærke
?padding=20                # Intern padding
```

## Bogstav-avatar-generator

Generer deterministiske bogstav-baserede avatarer fra ethvert navn eller e-mail. Perfekt til brugerprofil-placeholders, kommentarsystemer og teamkataloger. Hvert navn producerer altid samme farve, så avatarer er konsistente på tværs af sessioner.

### Endepunkt

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

### Eksempler

```
# Enkel 128px avatar
/avatar/128/John+Doe

# Cirkelavatar med tilpasset kant
/avatar/128/John+Doe?circle=true&border=2,ffffff

# Enkelt initial, pastelpalet
/avatar/64/Alice?single=true&palette=pastel

# SVG-output (skalerbar, under 500 bytes)
/avatar/128/John+Doe.svg
```

### Hvorfor bruge bogstav-avatarer?

- Nul eksterne afhængigheder — ingen Gravatar eller avatar-tjeneste fra tredjepart
- Deterministisk — samme navn producerer altid samme farve
- SVG-understøttelse — uendeligt skalerbar, perfekt til HiDPI-skærme
- Fire indbyggede farvepaletter til enhver brandæstetik

## Hurtigreference til REST API

Alle endpoints understøtter CORS og returnerer billeder med langsigtede cache-headers. Base64 JSON-output er tilgængelig for små thumbnails.

### Billed-endpoints

- `GET /{width}/{height}/{category}` — Tilfældigt billede fra kategori
- `GET /{width}/{height}` — Tilfældigt billede fra alle kategorier
- `GET /id/{id}/{width}/{height}` — Specifikt billede efter ID
- `GET /ratio/{ratio}/{width}/{category}` — Billedformat-billede
- `GET /preset/{preset}/{category}` — Social media-preset
- `GET /color/{hex}/{width}/{height}` — Farve-matchende billede
- `GET /gradient/{w}/{h}/{from}/{to}` — Gradient-billede
- `GET /svg/{width}/{height}` — SVG-placeholder
- `GET /avatar/{size}/{name}` — Bogstav-avatar (PNG/SVG)

### Metadata-endpoints

- `GET /api/images` — Liste kategorier og totaler
- `GET /api/info/id/{id}` — Billed-metadata (dimensioner, farver, format)
- `GET /api/color/{hex}` — Billeder der matcher en farve

### Health-endpoints

- `GET /health` — Liveness probe (Docker/K8s)
- `GET /ready` — Readiness probe (503 indtil billeder indlæst)

## Ekspertise og legitimationsoplysninger

- Aktive bidragydere til open-source-økosystemet siden 2008
- Al kode er open source under MIT-licensen og kan granskes på <a href="https://github.com/riadvice/placepix" target="_blank" class="text-accent hover:underline">GitHub</a>

## Ofte stillede spørgsmål

### Hvordan implementerer jeg PlacePix med Docker?

Kør `docker run -d -p 3000:3000 -v ./images:/app/images riadvice/placepix:latest`. Mount din billedmappe og tjenesten starter øjeblikkeligt med smart scanning aktiveret.

### Hvad er ansigtsbevidst smart beskæring?

PlacePix bruger OpenCV Haar-kaskader til at detektere ansigter i billeder. Når du tilføjer `?fit=smart` til enhver URL, flyttes beskæringsområdet for at centrere på detekterede ansigter i stedet for at bruge geometrisk centrum. Hvis der ikke findes noget ansigt, falder det tilbage til standard center-beskæring.

### Kan jeg generere gradient placeholder-billeder uden at uploade fotos?

Ja. `/gradient/{width}/{height}/{from}/{to}`-endpointen genererer gradient-billeder helt fra URL-parametre. Der kræves ingen uploadede billeder. Du kan også oprette SVG-placeholders med `/svg/{width}/{height}`.

### Hvordan generer jeg Instagram story-størrelse placeholder-billeder via API?

Brug preset-endpointen: `/preset/instagram-story/{category}`. Dette returnerer et 1080x1920-billede. Kombiner med `?format=webp&quality=70` for optimeret levering og `?fit=smart` for portræt-sikker beskæring.

### Understøtter PlacePix S3-kompatibel objektlagring?

Ja. PlacePix fungerer med OVHcloud Object Storage, AWS S3, MinIO og enhver S3-kompatibel udbyder. Konfigurer endpoint, bucket, adgangsnøgle og hemmelig nøgle via miljøvariabler.

### Hvilke outputformater understøttes?

WebP, AVIF, JPEG, PNG, SVG og base64 JSON. Brug `.webp`, `.avif` eller `.png` som filtypenavn, eller tilføj `?format=webp` som query-parameter. AVIF producerer de mindste filer; PNG er tabsfri.

### Er PlacePix gratis til kommerciel brug?

Ja. PlacePix er udgivet under MIT-licensen og er gratis til både personlig og kommerciel brug. Fordi det er self-hosted, er der ingen forbrugsgrænser, ingen API-nøgler og ingen fakturering per anmodning.
