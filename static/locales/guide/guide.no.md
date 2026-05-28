---
title: PlacePix Utviklerguide — Selvhostet Placeholder Image API og Funksjonsreferanse
description: Komplett PlacePix utviklerguide og API-referanse. Lær å distribuere placeholder-bilder med Docker, generere gradienter og SVG, og bruke sosiale medie-forhåndsinnstillinger for Instagram, YouTube og mer.
keywords: API for placeholder-bilder self-hosted, smart crop med ansiktsgjenkjenning, generator for gradient-placeholder, Docker-tjeneste for placeholder-bilder, API for Instagram-story-placeholder, generator for SVG-placeholder, API for utviklerbilder
author: RIADVICE
robots: index, follow
og_title: PlacePix Utviklerguide — Selvhostet Placeholder Image API og Funksjonsreferanse
og_description: Komplett utviklerguide som dekker Docker-deployment, smart beskjæring, gradient-placeholdere, SVG-generering og sosiale medie-forhåndsinnstillinger.
twitter_title: PlacePix Utviklerguide — Selvhostet Placeholder Image API og Funksjonsreferanse
twitter_description: Komplett utviklerguide som dekker Docker-deployment, smart beskjæring, gradient-placeholdere, SVG-generering og sosiale medie-forhåndsinnstillinger.
jsonld_name: PlacePix Utviklerguide — Selvhostet Placeholder Image API og Funksjonsreferanse
jsonld_description: Komplett utviklerguide og API-referanse for PlacePix, en selvhostet tjeneste for placeholder-bilder. Dekker Docker-deployment, smart beskjæring med ansiktsgjenkjenning, gradient-placeholdere, SVG-generering og sosiale medie-forhåndsinnstillinger.
jsonld_proficiency: Expert
jsonld_dependencies: Docker, Python 3.12, FastAPI
header_title: PlacePix Utviklerguide
header_subtitle: Komplett API-referanse og funksjonsdokumentasjon for selvhostet placeholder-bildetjeneste. Dekker Docker-implementering, smart beskjæring, gradient-placeholdere, SVG-generering, bokstav-avatarer og sosiale medie-forhåndsinnstillinger.
author_label: Av
updated_label: "Sist oppdatert: mai 2026"
github_label: Åpen kildekode på GitHub
toc_title: Innholdsfortegnelse
---

## Hva er PlacePix?

PlacePix er en **selvhostet placeholder-bildetjeneste** bygget for utviklere og designteam. I motsetning til tredjeparts placeholder-tjenester som krever eksterne nettverkskall og kan forsvinne, kjører PlacePix helt på din egen infrastruktur. Slipp bilder i mapper, og få umiddelbart URL-endpoints som serverer bilder med endret størrelse, filtrert og formatert.

Tjenesten er skrevet i Python ved hjelp av FastAPI med bildebehandling drevet av Pillow og OpenCV. Den støtter Docker-implementering, og S3-kompatibel objektlagring.

### Funksjoner

- **Null konfigurasjon** — slipp bilder i mapper og kjør
- **Ansiktsbevisst beskjæring** — OpenCV oppdager og sentrerer ansikter
- **Gradient- og SVG-placeholdere** — ingen bilder kreves
- **Sosiale medier-forhåndsinnstillinger** — Instagram, YouTube, TikTok-størrelser innebygget
- **Fargesøk** — finn bilder som matcher merkepaletten din
- **Bokstav-avatarer** — deterministiske profilbilder fra navn

## Docker-implementeringsveiledning

Den raskeste måten å kjøre PlacePix på er med Docker. Én kommando implementerer hele tjenesten med smart skanning, fargeekstraksjon, og den innebygde URL-byggeren.

### Énlinjes-implementering

```bash
docker run -d -p 3000:3000 \
  -v ./images:/app/images \
  riadvice/placepix:latest
```

### Docker Compose (Anbefalt)

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

Monter både `/app/images` (biblioteket ditt) og `/app/data` (skanningcache og metadata) for å bevare tilstanden mellom container-restarts. Konfigurer oppførsel via miljøvariabler eller en `.env`-fil.

### OVHcloud S3-kompatibel lagring

PlacePix støtter alle S3-kompatible backends. For OVHcloud Object Storage, sett:

```
S3_ENABLED=true
S3_ENDPOINT=https://s3.rbx.io.cloud.ovh.net
S3_ACCESS_KEY=your-key
S3_SECRET_KEY=your-secret
S3_BUCKET=your-bucket
S3_REGION=rbx
```

## Smart beskjæring med ansiktsgjenkjenning

Standard senterbeskjæring kan skjære gjennom ansikter i portrettfotografi. PlacePix løser dette med **ansiktsbevisst smart beskjæring** drevet av OpenCV Haar-kaskader.

### Hvordan det fungerer

Når en forespørsel inkluderer `?fit=smart`, skanner PlacePix bildet for menneskelige ansikter ved hjelp av OpenCV. Hvis ansikter oppdages, flyttes beskjæringsvinduet slik at ansiktssentroiden ligger så nært som mulig de gyldne snittpunktene. Hvis ingen ansikter finnes, faller det tilbake til standard senterbeskjæring.

### API-eksempler

```
# Ansiktsbevisst beskjæring (oppdager og sentrerer ansikter)
/400/300/people?fit=smart

# Standard senterbeskjæring
/400/300/people?fit=crop

# Dekkfylling (kan strekke)
/400/300/people?fit=cover

# Innehold (letterboxing)
/400/300/people?fit=contain
```

### Når du skal bruke Smart Crop

- Portrettfotografi og headshots
- Teamsider der ansikter betyr noe
- Miniatyrbilder fra sosiale medier
- Ethvert scenario der geometrisk senterbeskjæring ødelegger komposisjonen

## API for gradient placeholder

Generer lineære og radiale gradient-bilder on-the-fly uten å laste opp noen ressurser. Perfekt for hero-bakgrunner, loading-tilstander og design-mockups.

### Endepunkt-syntaks

```
/gradient/{width}/{height}/{from_hex}/{to_hex}
```

### Eksempler

```
# Enkel lineær gradient (topp til bunn)
/gradient/800/400/3b82f6/10b981

# 45-graders vinklet gradient
/gradient/800/400/e11d48/f59e0b?angle=45

# Radiell gradient fra midten
/gradient/800/400/1e293b/64748b?gradient_type=radial

# Med utdataformat
/gradient/800/400/0ea5e9/ffffff?format=webp&quality=80
```

### Parameterreferanse

- `{from_hex}` / `{to_hex}` — hex-farger uten # prefikset
- `?angle=45` — lineær vinkel i grader (0-360)
- `?gradient_type=radial` — bytter til radiell gradient
- `?format=webp` — WebP-utdata (mindre filstørrelse)

## SVG-placeholder-generator

SVG-placeholdere krever null server-side bildebehandling. De genereres som inline SVG med tilpassbar bakgrunnsfarge, forgrunnsfarge og tekstetikett.

### Endepunkt

```
/svg/{width}/{height}?bg={hex}&fg={hex}&text={label}
```

### Eksempler

```
# Standard wireframe-placeholder
/svg/400/300

# Egne merkefarger
/svg/400/300?bg=1c1917&fg=0ea5e9

# Med egendefinert tekst
/svg/400/300?bg=0ea5e9&fg=ffffff&text=Hero+Section
```

### Hvorfor SVG?

- Filstørrelse under 500 bytes
- Uendelig skalerbar uten kvalitetstap
- Null serverbehandlingsoverhead
- Perfekt for wireframes og low-fidelity prototyper

## Sosiale medie-forhåndsinnstillinger

PlacePix inkluderer forhåndsdefinerte dimensjoner for populære sosiale plattformer og skjermstørrelser. Bruk disse for å generere perfekt størrelsestilpassede placeholder-bilder for Instagram, YouTube, TikTok, LinkedIn, X (Twitter) og standard skjermer.

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

### Skjermstørrelser

```
/preset/mobile/nature              # 375x812
/preset/tablet/nature              # 768x1024
/preset/desktop/nature             # 1920x1080
/preset/4k/nature                  # 3840x2160
```

### Spesielt brukstilfelle: Instagram Story API

Hvis du bygger et verktøy for administrasjon av sosiale medier og trenger **placeholder-bilder i Instagram story-størrelse**, bruk `/preset/instagram-story/{category}`. Kombiner med `?fit=smart` for porträttbilder og `?format=webp&quality=70` for optimalisert levering.

## Fargesøk-API

Hvert bilde i PlacePix skannes for sine 3 dominerende farger. Du kan søke i hele biblioteket etter hex-farge for å finne bilder som matcher merkepaletten din.

### Endepunkter

```
# Hent et bilde som matcher en spesifikk hex-farge
/color/0ea5e9/400/300

# Filtrer ethvert endepunkt etter dominerende farge
/400/300/nature?color=d97706

# List alle bilder som matcher en farge
/api/color/3b82f6
```

### Hvordan fargeskannning fungerer

Ved oppstart ekstraherer PlacePix de hyppigste fargene fra hvert bilde ved hjelp av k-means klynging i LAB-fargerom. Dette gir perceptuelt nøyaktige treff framfor rå RGB-gjennomsnitt. Palettsiden (`/palette`) visualiserer disse fargene og lar deg bla etter fargetonekategori.

## Filter og effekter

Bruk real-time filtre og effekter på ethvert bilde via spørreparametere. All behandling gjøres server-side og caches for påfølgende forespørsler.

### Fargejusteringer

```
?grayscale=1               # Svart-hvitt
?sepia=1                   # Varm sepia-tone
?tint=0ea5e9               # Hex-fargeoverlegg
?brightness=1.3            # 0,0 til 2,0
?contrast=1.2              # 0,0 til 2,0
?saturation=2.0            # 0,0 til 2,0
?invert=true               # Inverter farger
?posterize=4               # Fargenivåer (1-8)
?duotone=ff0000,0000ff     # Tokartfarge
```

### Bildeeffekter

```
?blur=2                    # Gaussisk uskarphet (1-10)
?sharpen=1.5               # Skarphetsgrad
?emboss=true               # 3D-relief
?edges=sobel               # Kantdeteksjon
?edges=canny               # Canny-kanter
?halftone=4                # Punktmønster
?oil_painting=true         # Oljemaleri-stil
?pencil_sketch=true        # Blyantskisse
?cartoon=true              # Tegnefilm-effekt
?vignette=0.5              # Mørkne kanter (0-1)
```

### Overlay-parametere

```
?text=Hello+World          # Tekstoverlegg
?border=4,ffffff           # Kantbredde og farge
?watermark=1               # Bruk konfigurert vannmerke
?padding=20                # Indre polstring
```

## Bokstav-avatar-generator

Generer deterministiske bokstav-baserte avatarer fra ethvert navn eller e-post. Perfekt for brukerprofil-placeholders, kommentarsystemer og teamkataloger. Hvert navn produserer alltid samme farge, så avatarer er konsistente på tvers av økter.

### Endepunkt

```
/avatar/{size}/{name}
/avatar/{size}/{name}.{ext}
```

### Parametere

- `size` — pikselstørrelse (f.eks. `64`, `128`, `256`)
- `name` — hvilken som helst streng; første bokstaver trekkes ut for avataren
- `circle` — beskjær til en sirkelform
- `border={width},{color}` — legg til en kant
- `bg={hex}` — overstyre bakgrunnsfarge
- `fg={hex}` — overstyre tekst-/forgrunnsfarge
- `single=true` — bruk kun første bokstav
- `uppercase=false` — behold små bokstaver
- `palette={name}` — velg fra `flatui`, `material`, `pastel` eller `neon`

### Eksempler

```
# Enkel 128px avatar
/avatar/128/John+Doe

# Sirkelavatar med tilpasset kant
/avatar/128/John+Doe?circle=true&border=2,ffffff

# Enkelt initial, pastellpalett
/avatar/64/Alice?single=true&palette=pastel

# SVG-utgang (skalerbar, under 500 bytes)
/avatar/128/John+Doe.svg
```

### Hvorfor bruke bokstavavatarer?

- Null eksterne avhengigheter — ingen Gravatar eller tredjeparts avatar-tjeneste
- Deterministisk — samme navn produserer alltid samme farge
- SVG-støtte — uendelig skalerbar, perfekt for HiDPI-skjermer
- Fire innebygde fargepaletter for enhver merkevare-estetikk

## REST API-hurtigreferanse

Alle endpoints støtter CORS og returnerer bilder med langtids cache-headere. Base64 JSON-output er tilgjengelig for små thumbnails.

### Bilde-endpoints

- `GET /{width}/{height}/{category}` — Tilfeldig bilde fra kategori
- `GET /{width}/{height}` — Tilfeldig bilde fra alle kategorier
- `GET /id/{id}/{width}/{height}` — Spesifikt bilde etter ID
- `GET /ratio/{ratio}/{width}/{category}` — Bilde med størrelsesforhold
- `GET /preset/{preset}/{category}` — Sosiale medier-preset
- `GET /color/{hex}/{width}/{height}` — Farge-matchende bilde
- `GET /gradient/{w}/{h}/{from}/{to}` — Gradientbilde
- `GET /svg/{width}/{height}` — SVG-placeholder
- `GET /avatar/{size}/{name}` — Bokstav-avatar (PNG/SVG)

### Metadata-endpoints

- `GET /api/images` — List kategorier og totalsummer
- `GET /api/info/id/{id}` — Bilde-metadata (dimensjoner, farger, format)
- `GET /api/color/{hex}` — Bilder som matcher en farge

### Health-endpoints

- `GET /health` — Liveness-sjekk (Docker/K8s)
- `GET /ready` — Readiness-sjekk (503 til bilder er lastet)

## Ekspertise og referanser

- Aktive bidragsytere til open-source-økosystemet siden 2008
- All kode er åpen kildekode under MIT-lisensen og kan revideres på <a href="https://github.com/riadvice/placepix" target="_blank" class="text-accent hover:underline">GitHub</a>

## Ofte stilte spørsmål

### Hvordan distribuerer jeg PlacePix med Docker?

Kjør `docker run -d -p 3000:3000 -v ./images:/app/images riadvice/placepix:latest`. Mount bildemappen din og tjenesten starter umiddelbart med smart skanning aktivert.

### Hva er smart beskjæring med ansiktsgjenkjenning?

PlacePix bruker OpenCV Haar-cascades for å oppdage ansikter i bilder. Når du legger til `?fit=smart` til en URL, forskyves beskjæringsregionen for å sentrere på oppdagede ansikter i stedet for å bruke geometrisk senter. Hvis intet ansikt blir funnet, faller det tilbake til standard sentrumsbeskjæring.

### Kan jeg generere gradient-placeholder-bilder uten å laste opp bilder?

Ja. Endepunktet `/gradient/{width}/{height}/{from}/{to}` genererer gradient-bilder helt fra URL-parametere. Ingen opplastede bilder kreves. Du kan også opprette SVG-placeholdere med `/svg/{width}/{height}`.

### Hvordan generer jeg Instagram story-størrelse placeholder-bilder via API?

Bruk preset-endepunktet: `/preset/instagram-story/{category}`. Dette returnerer et 1080x1920-bilde. Kombiner med `?format=webp&quality=70` for optimalisert levering og `?fit=smart` for portrett-sikker beskjæring.

### Støtter PlacePix S3-kompatibel objektlagring?

Ja. PlacePix fungerer med OVHcloud Object Storage, AWS S3, MinIO og enhver S3-kompatibel leverandør. Konfigurer endepunkt, bucket, tilgangsnøkkel og hemmelig nøkkel via miljøvariabler.

### Hvilke outputformater støttes?

WebP, AVIF, JPEG, PNG, SVG og base64 JSON. Bruk `.webp`, `.avif` eller `.png` som filtypen, eller legg til `?format=webp` som en query-parameter. AVIF produserer de minste filene; PNG er tapsfri.

### Er PlacePix gratis for kommersiell bruk?

Ja. PlacePix er utgitt under MIT-lisensen og er gratis for både personlig og kommersiell bruk. Fordi det er selvhostet, er det ingen bruksgrenser, ingen API-nøkler og ingen fakturering per forespørsel.
