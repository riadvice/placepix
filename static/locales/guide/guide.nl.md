---
title: PlacePix Ontwikkelaarsgids — Zelfgehoste Placeholder Image API en Functiereferentie
description: Complete PlacePix ontwikkelaarsgids en API-referentie. Leer placeholder-afbeeldingen implementeren met Docker, gradienten en SVG genereren, en social media-presets gebruiken voor Instagram, YouTube en meer.
keywords: API placeholder-afbeeldingen self-hosted, placeholder met gezichtsherkenning bijsnijden, generator gradient placeholder, Docker placeholder-afbeeldingenservice, API Instagram story placeholder, generator SVG placeholder, API ontwikkelaar afbeeldingen
author: RIADVICE
robots: index, follow
og_title: PlacePix Ontwikkelaarsgids — Zelfgehoste Placeholder Image API en Functiereferentie
og_description: Complete ontwikkelaarsgids met Docker-implementatie, slim bijsnijden, gradient-placeholders, SVG-generering en social media-presets.
twitter_title: PlacePix Ontwikkelaarsgids — Zelfgehoste Placeholder Image API en Functiereferentie
twitter_description: Complete ontwikkelaarsgids met Docker-implementatie, slim bijsnijden, gradient-placeholders, SVG-generering en social media-presets.
jsonld_name: PlacePix Ontwikkelaarsgids — Zelfgehoste Placeholder Image API en Functiereferentie
jsonld_description: Complete ontwikkelaarsgids en API-referentie voor PlacePix, een zelfgehoste placeholder-afbeeldingsservice. Bevat Docker-implementatie, gezichtsherkennend slim bijsnijden, gradient-placeholders, SVG-generering en social media-presets.
jsonld_proficiency: Expert
jsonld_dependencies: Docker, Python 3.12, FastAPI
header_title: PlacePix Ontwikkelaarsgids
header_subtitle: Complete API-referentie en functiedocumentatie voor de zelfgehoste placeholder-afbeeldingsservice. Bevat Docker-implementatie, slim bijsnijden, gradient-placeholders, SVG-generering, letter-avatars en social media-presets.
author_label: Door
updated_label: "Laatst bijgewerkt: mei 2026"
github_label: Open Source op GitHub
toc_title: Inhoudsopgave
---

## Wat is PlacePix?

PlacePix is een **zelfgehoste placeholder-afbeeldingsservice** gebouwd voor ontwikkelaars en designteams. In tegenstelling tot placeholder-services van derden die externe netwerkoproepen vereisen en kunnen verdwijnen, draait PlacePix volledig op uw eigen infrastructuur. Plaats afbeeldingen in mappen en krijg direct URL-endpoints die geschaalde, gefilterde en geformatteerde afbeeldingen serveren.

De service is geschreven in Python met FastAPI met beeldverwerking aangedreven door Pillow en OpenCV. Het ondersteunt Docker-implementatie en S3-compatibele objectopslag.

### Functies

- **Zero configuratie** — plaats afbeeldingen in mappen en ga aan de slag
- **Gezichtsherkennend bijsnijden** — OpenCV detecteert en centreert gezichten
- **Gradient- en SVG-placeholders** — geen afbeeldingen vereist
- **Social media-presets** — Instagram, YouTube, TikTok-formaten ingebouwd
- **Kleurzoeken** — vind afbeeldingen die bij uw merkpalet passen
- **Letter-avatars** — deterministische profielafbeeldingen uit namen

## Docker-implementatiegids

De snelste manier om PlacePix te draaien is met Docker. Eén enkel commando implementeert de hele service met slim scannen, kleurextractie en de ingebouwde URL-builder.

### Eénregel-implementatie

```bash
docker run -d -p 3000:3000 \
  -v ./images:/app/images \
  riadvice/placepix:latest
```

### Docker Compose (Aanbevolen)

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

### Persistente gegevens en omgeving

Mount zowel `/app/images` (uw afbeeldingenbibliotheek) als `/app/data` (scan-cache en metadata) om status te behouden tussen container-herstarts. Configureer gedrag via omgevingsvariabelen of een `.env`-bestand.

### OVHcloud S3-compatibele opslag

PlacePix ondersteunt elk S3-compatibel backend. Voor OVHcloud Object Storage, stel in:

```
S3_ENABLED=true
S3_ENDPOINT=https://s3.rbx.io.cloud.ovh.net
S3_ACCESS_KEY=your-key
S3_SECRET_KEY=your-secret
S3_BUCKET=your-bucket
S3_REGION=rbx
```

## Slim bijsnijden met gezichtsherkenning

Standaard centraal bijsnijden kan gezichten doorsnijden in portretfotografie. PlacePix lost dit op met **gezichtsherkennend slim bijsnijden** aangedreven door OpenCV Haar-cascades.

### Hoe het werkt

Wanneer een verzoek `?fit=smart` bevat, scant PlacePix de afbeelding op menselijke gezichten met OpenCV. Als gezichten worden gedetecteerd, wordt het bijsnijdvenster verschoven zodat het gezichtscentroid zo dicht mogelijk bij de snijpunten van de gulden snede ligt. Als geen gezichten worden gevonden, valt het terug op standaard centraal bijsnijden.

### API-voorbeelden

```
# Gezichtsherkennend bijsnijden (detecteert en centreert gezichten)
/400/300/people?fit=smart

# Standaard centraal bijsnijden
/400/300/people?fit=crop

# Cover-vulling (kan rekken)
/400/300/people?fit=cover

# Bevatten (letterboxing)
/400/300/people?fit=contain
```

### Wanneer slim bijsnijden gebruiken

- Portretfotografie en headshots
- Teampagina's waar gezichten belangrijk zijn
- Social media-thumbnails
- Elk scenario waar geometrisch centraal bijsnijden de compositie verpest

## Gradient placeholder API

Genereer lineaire en radiale gradient-afbeeldingen on-the-fly zonder assets te uploaden. Perfect voor hero-achtergronden, laadstatussen en design-mockups.

### Endpoint-syntaxis

```
/gradient/{width}/{height}/{from_hex}/{to_hex}
```

### Voorbeelden

```
# Eenvoudige lineaire gradient (van boven naar beneden)
/gradient/800/400/3b82f6/10b981

# 45-graden hoek-gradient
/gradient/800/400/e11d48/f59e0b?angle=45

# Radiale gradient vanuit centrum
/gradient/800/400/1e293b/64748b?gradient_type=radial

# Met uitvoerformaat
/gradient/800/400/0ea5e9/ffffff?format=webp&quality=80
```

### Parameterreferentie

- `{from_hex}` / `{to_hex}` — hex-kleuren zonder het # voorvoegsel
- `?angle=45` — lineaire hoek in graden (0-360)
- `?gradient_type=radial` — schakelt over naar radiale gradient
- `?format=webp` — WebP-uitvoer (kleinere bestandsgrootte)

## SVG-placeholder-generator

SVG-placeholders vereisen geen server-side beeldverwerking. Ze worden gegenereerd als inline SVG met aanpasbare achtergrondkleur, voorgrondkleur en tekstlabel.

### Endpoint

```
/svg/{width}/{height}?bg={hex}&fg={hex}&text={label}
```

### Voorbeelden

```
# Default wireframe placeholder
/svg/400/300

# Custom brand colors
/svg/400/300?bg=1c1917&fg=0ea5e9

# With custom text
/svg/400/300?bg=0ea5e9&fg=ffffff&text=Hero+Section
```

### Waarom SVG?

- Bestandsgrootte onder 500 bytes
- Oneindig schaalbaar zonder kwaliteitsverlies
- Nul serververwerkings overhead
- Perfect voor wireframes en low-fidelity prototypes

## Social media presets

PlacePix bevat vooraf gedefinieerde afmetingen voor populaire sociale platforms en schermformaten. Gebruik deze om perfect gedefinieerde placeholder-afbeeldingen te genereren voor Instagram, YouTube, TikTok, LinkedIn, X (Twitter) en standaard displays.

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

### Schermformaten

```
/preset/mobile/nature              # 375x812
/preset/tablet/nature              # 768x1024
/preset/desktop/nature             # 1920x1080
/preset/4k/nature                  # 3840x2160
```

### Long-Tail Gebruikssituatie: Instagram Story API

Als u een social media-beheertool bouwt en **Instagram story-grootte placeholder-afbeeldingen** nodig heeft, gebruik dan `/preset/instagram-story/{category}`. Combineer met `?fit=smart` voor portretfoto's en `?format=webp&quality=70` voor geoptimaliseerde levering.

## Kleurzoek-API

Elke afbeelding in PlacePix wordt gescand op de top 3 dominante kleuren. U kunt de hele bibliotheek doorzoeken op hex-kleur om afbeeldingen te vinden die bij uw merkpalet passen.

### Endpoints

```
# Een afbeelding ophalen die overeenkomt met een specifieke hex-kleur
/color/0ea5e9/400/300

# Elk endpoint filteren op dominante kleur
/400/300/nature?color=d97706

# Alle afbeeldingen weergeven die bij een kleur passen
/api/color/3b82f6
```

### Hoe kleurenscannen werkt

Bij opstarten extraheert PlacePix de meest frequente kleuren uit elke afbeelding met k-means clustering in LAB-kleurruimte. Dit produceert perceptueel nauwkeurige overeenkomsten in plaats van ruwe RGB-gemiddelden. De paletpagina (`/palette`) visualiseert deze kleuren en laat u bladeren per kleurtint-categorie.

## Oriëntatiefilter

Filter willekeurige afbeeldingen op hun native beeldverhouding vóór de selectie. Dit is handig wanneer je afbeeldingen nodig hebt die natuurlijk in een lay-out passen — landschap voor headers, portret voor kaarten of vierkant voor miniaturen.

### Eindpunten

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

### Configuratie

De `squarish`-tolerantie is configureerbaar via de omgevingsvariabele `ORIENTATION_SQUARISH_TOLERANCE` (standaard: `0.15`). Een waarde van `0.15` betekent dat afbeeldingen met een beeldverhouding tussen `0.85` en `1.15` als vierkant worden beschouwd. Stel in op `0.0` voor exact 1:1.

### Hoe het werkt

PlacePix leest afbeeldingafmetingen uit bestandsheaders tijdens de initiële scan (lokale bestanden) en tijdens de achtergrondmetadata-scan (S3-afbeeldingen). De afmetingen worden in het geheugen opgeslagen en gebruikt om de kandidatenpool te filteren vóór willekeurige of seed-gebaseerde selectie. Als er om een oriëntatie wordt gevraagd maar er zijn geen overeenkomende afbeeldingen, wordt een `404` geretourneerd.
## Filters en effecten

Pas real-time filters en effecten toe op elke afbeelding via query-parameters. Alle verwerking gebeurt server-side en wordt gecachet voor volgende verzoeken.

### Kleuraanpassingen

```
?grayscale=1               # Zwart-wit
?sepia=1                   # Warme sepia-toon
?tint=0ea5e9               # Hex-kleur overlay
?brightness=1.3            # 0,0 tot 2,0
?contrast=1.2              # 0,0 tot 2,0
?saturation=2.0            # 0,0 tot 2,0
?invert=true               # Kleuren inverteren
?posterize=4               # Kleurniveaus (1-8)
?duotone=ff0000,0000ff     # Twee-kleurenkaart
```

### Afbeeldingseffecten

```
?blur=2                    # Gaussiaanse vervaging (1-10)
?sharpen=1.5               # Verscherpingshoeveelheid
?emboss=true               # 3D-reliëf
?edges=sobel               # Randdetectie
?edges=canny               # Canny-randen
?halftone=4                # Stippatroon
?oil_painting=true         # Olieverfstijl
?pencil_sketch=true        # Potloodschets
?cartoon=true              # Cartoon-effect
?vignette=0.5              # Randen donkerder maken (0-1)
```

### Overlay-parameters

```
?text=Hello+World          # Tekst-overlay
?border=4,ffffff           # Randbreedte & kleur
?watermark=1               # Geconfigureerd watermerk toepassen
?padding=20                # Interne opvulling
```

## Avatar Generator

Genereer deterministische avatars vanuit elke naam of email. PlacePix ondersteunt twee avatar-types: **Letter avatar** (gekleurde initialen) en **Multiavatar** (multiculturele vector avatars).

### Endpoint

```
/avatar/{size}/{name}
/avatar/{size}/{name}.{ext}
```

### Parameters

- `type` — avatar type: `letter` (default) or `multiavatar`
- `size` — pixel size (e.g. `64`, `128`, `256`)
- `name` — any string; used as seed for the avatar

#### Letter avatar (`type=letter`)

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

### Voorbeelden

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

### Waarom letter avatars gebruiken?

- Nul externe afhankelijkheden — geen Gravatar of avatar-dienst van derden
- Deterministisch — dezelfde naam produceert altijd dezelfde kleur
- SVG-ondersteuning — oneindig schaalbaar, perfect voor HiDPI-schermen
- Zes ingebouwde kleurenpaletten voor elke brand-esthetiek

### Waarom Multiavatar gebruiken?

- 12 miljard unieke multiculturele avatars
- Deterministisch — dezelfde naam produceert altijd dezelfde avatar
- Pure SVG-uitvoer — kleine bestandsgrootte, oneindig schaalbaar
- Geen externe API-aanroepen nodig

## REST API-snelzoekgids

Alle endpoints ondersteunen CORS en retourneren afbeeldingen met langdurige cache-headers. Base64 JSON-uitvoer is beschikbaar voor kleine thumbnails.

### Afbeelding-endpoints

- `GET /{width}/{height}/{category}` — Willekeurige afbeelding uit categorie
- `GET /{width}/{height}` — Willekeurige afbeelding uit alle categorieën
- `GET /id/{id}/{width}/{height}` — Specifieke afbeelding op ID
- `GET /ratio/{ratio}/{width}/{category}` — Beeldverhouding-afbeelding
- `GET /preset/{preset}/{category}` — Social media-preset
- `GET /color/{hex}/{width}/{height}` — Kleur-overeenkomende afbeelding
- `GET /gradient/{w}/{h}/{from}/{to}` — Gradient-afbeelding
- `GET /svg/{width}/{height}` — SVG-placeholder
- `GET /avatar/{size}/{name}` — Letter-avatar (PNG/SVG)

### Metadata-endpoints

- `GET /api/images` — Categorieën en totalen weergeven
- `GET /api/info/id/{id}` — Afbeelding-metadata (afmetingen, kleuren, formaat)
- `GET /api/color/{hex}` — Afbeeldingen die bij een kleur passen

### Health-endpoints

- `GET /health` — Liveness probe (Docker/K8s)
- `GET /ready` — Readiness probe (503 tot afbeeldingen geladen)

## Expertise en referenties

- Actieve bijdragers aan het open-source ecosysteem sinds 2008
- Alle code is open source onder de MIT-licentie en auditbaar op <a href="https://github.com/riadvice/placepix" target="_blank" class="text-accent hover:underline">GitHub</a>

## Veelgestelde vragen

### Hoe implementeer ik PlacePix met Docker?

Voer `docker run -d -p 3000:3000 -v ./images:/app/images riadvice/placepix:latest` uit. Mount uw afbeeldingenmap en de service start onmiddellijk met slim scannen ingeschakeld.

### Wat is slim bijsnijden met gezichtsherkenning?

PlacePix gebruikt OpenCV Haar-cascades om gezichten in afbeeldingen te detecteren. Wanneer u `?fit=smart` aan elke URL toevoegt, wordt het bijsnijdgebied verschoven om te centreren op gedetecteerde gezichten in plaats van het geometrische centrum te gebruiken. Als er geen gezicht wordt gevonden, valt het terug op standaard centraal bijsnijden.

### Kan ik gradient-placeholder-afbeeldingen genereren zonder foto's te uploaden?

Ja. Het `/gradient/{width}/{height}/{from}/{to}` endpoint genereert gradient-afbeeldingen volledig uit URL-parameters. Er zijn geen geüploade afbeeldingen nodig. U kunt ook SVG-placeholders maken met `/svg/{width}/{height}`.

### Hoe genereer ik Instagram story-grootte placeholder-afbeeldingen via API?

Gebruik het preset-endpoint: `/preset/instagram-story/{category}`. Dit retourneert een 1080x1920-afbeelding. Combineer met `?format=webp&quality=70` voor geoptimaliseerde levering en `?fit=smart` voor portret-veilige bijsnijding.

### Ondersteunt PlacePix S3-compatibele objectopslag?

Ja. PlacePix werkt met OVHcloud Object Storage, AWS S3, MinIO en elke S3-compatibele provider. Configureer endpoint, bucket, toegangssleutel en geheime sleutel via omgevingsvariabelen.

### Welke uitvoerformaten worden ondersteund?

WebP, AVIF, JPEG, PNG, SVG en base64 JSON. Gebruik `.webp`, `.avif` of `.png` als bestandsextensie, of voeg `?format=webp` toe als query-parameter. AVIF produceert de kleinste bestanden; PNG is verliesvrij.

### Is PlacePix gratis voor commercieel gebruik?

Ja. PlacePix wordt uitgebracht onder de MIT-licentie en is gratis voor zowel persoonlijk als commercieel gebruik. Omdat het zelfgehost is, zijn er geen gebruikslimieten, geen API-sleutels en geen facturering per verzoek.