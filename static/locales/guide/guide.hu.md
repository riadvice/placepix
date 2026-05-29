---
title: PlacePix Fejlesztői Útmutató — Saját üzemeltetésű Placeholder Kép API és Funkcióreferencia
description: Teljes PlacePix fejlesztői útmutató és API referencia. Ismerje meg, hogyan telepítsen placeholder képeket Dockerrel, hogyan generáljon gradienseket és SVG-ket, és használja a közösségi média előbeállításait Instagram, YouTube és egyéb platformokhoz.
keywords: self-hosted placeholder kép API, arcérzékelő körbevágás placeholder, színátmenetes placeholder generátor, Docker placeholder kép szolgáltatás, Instagram story placeholder API, SVG placeholder generátor, fejlesztő kép API
author: RIADVICE
robots: index, follow
og_title: PlacePix Fejlesztői Útmutató — Saját üzemeltetésű Placeholder Kép API és Funkcióreferencia
og_description: Teljes fejlesztői útmutató, amely lefedi a Docker telepítést, intelligens vágást, gradiens placeholdereket, SVG generálást és közösségi média előbeállításokat.
twitter_title: PlacePix Fejlesztői Útmutató — Saját üzemeltetésű Placeholder Kép API és Funkcióreferencia
twitter_description: Teljes fejlesztői útmutató, amely lefedi a Docker telepítést, intelligens vágást, gradiens placeholdereket, SVG generálást és közösségi média előbeállításokat.
jsonld_name: PlacePix Fejlesztői Útmutató — Saját üzemeltetésű Placeholder Kép API és Funkcióreferencia
jsonld_description: Teljes fejlesztői útmutató és API referencia a PlacePix-hez, egy saját üzemeltetésű placeholder képszolgáltatáshoz. Lefedi a Docker telepítést, arcérzékelő intelligens vágást, gradiens placeholdereket, SVG generálást és közösségi média előbeállításokat.
jsonld_proficiency: Expert
jsonld_dependencies: Docker, Python 3.12, FastAPI
header_title: PlacePix Fejlesztői Útmutató
header_subtitle: Teljes API referencia és funkciódokumentáció a saját üzemeltetésű placeholder képszolgáltatáshoz. Tartalmazza a Docker telepítést, intelligens vágást, gradiens placeholderek, SVG generálást, betű avatarokat és közösségi média előbeállításokat.
author_label: Szerző
updated_label: "Utolsó frissítés: 2026. május"
github_label: Nyílt forráskód a GitHubon
toc_title: Tartalomjegyzék
---

## Mi az a PlacePix?

A PlacePix egy **saját üzemeltetésű placeholder képszolgáltatás**, amelyet fejlesztőknek és dizájncsapatoknak építettek. A harmadik fél általi placeholder szolgáltatásokkal ellentétben, amelyek külső hálózati hívásokat igényelnek és eltűnhetnek, a PlacePix teljes egészében a saját infrastruktúráján fut. Dobd be a képeket mappákba, és azonnal megkapod a URL endpointokat, amelyek átméretezett, szűrt és formázott képeket szolgáltatnak.

A szolgáltatás Pythonban íródott FastAPI-val, képfeldolgozással, amelyet a Pillow és az OpenCV hajt. Támogatja a Docker telepítést és az S3-kompatibilis objektumtárolást.

### Jellemzők

- **Nulla konfiguráció** — dobd be a képeket mappákba és indulj
- **Arcérzékelő vágás** — Az OpenCV észleli és középre helyezi az arcokat
- **Gradiens és SVG placeholderek** — nincs szükség képekre
- **Közösségi média előbeállítások** — Instagram, YouTube, TikTok méretek beépítve
- **Színkeresés** — találj a márka színpalettájához illeszkedő képeket
- **Betű avatarok** — determinisztikus profilképek nevekből

## Docker telepítési útmutató

A PlacePix futtatásának leggyorsabb módja a Docker. Egyetlen parancs telepíti az egész szolgáltatást intelligens szkenneléssel, színkivonattal és a beépített URL builderrel.

### Egy soros telepítés

```bash
docker run -d -p 3000:3000 \
  -v ./images:/app/images \
  riadvice/placepix:latest
```

### Docker Compose (Ajánlott)

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

### Állandó adatok és környezet

Mountolja mind a `/app/images` (képkönyvtárát), mind az `/app/data` (szkennelési cache és metaadatok) mappát az állapot megőrzése érdekében a konténer újraindítások során. Konfigurálja a viselkedést környezeti változók vagy egy `.env` fájl segítségével.

### OVHcloud S3-kompatibilis tárolás

A PlacePix bármilyen S3-kompatibilis backendet támogat. Az OVHcloud Object Storage-hoz állítsa be:

```
S3_ENABLED=true
S3_ENDPOINT=https://s3.rbx.io.cloud.ovh.net
S3_ACCESS_KEY=your-key
S3_SECRET_KEY=your-secret
S3_BUCKET=your-bucket
S3_REGION=rbx
```

## Arcérzékeny intelligens vágás

A standard középső vágás átvághatja az arcokat a portréfotózáson. A PlacePix ezt OpenCV Haar kaskádokkal működő **arcérzékelő intelligens vágással** oldja meg.

### Hogyan működik

Amikor egy kérés tartalmazza a `?fit=smart` paramétert, a PlacePix az OpenCV segítségével szkenneli a képet emberi arcok után. Ha arcokat észlel, a vágási ablak eltolódik, hogy az arc centroid a lehető legközelebb legyen az aranymetszés metszéspontjaihoz. Ha nem talál arcokat, visszaesik a standard középső vágásra.

### API példák

```
# Arcérzékelő vágás (észleli és középre helyezi az arcokat)
/400/300/people?fit=smart

# Standard középső vágás
/400/300/people?fit=crop

# Borító kitöltés (nyújthat)
/400/300/people?fit=cover

# Tartalmazás (letterboxing)
/400/300/people?fit=contain
```

### Mikor használja az intelligens vágást

- Portréfotózás és headshotok
- Csapatoldalak, ahol az arcok számítanak
- Közösségi média miniatűrök
- Bármely forgatókönyv, ahol a geometriai középső vágás tönkreteszi a kompozíciót

## Gradiens placeholder API

Generáljon lineáris és radiális gradiens képeket on-the-fly bármilyen eszköz feltöltése nélkül. Tökéletes hero háttérképekhez, betöltési állapotokhoz és design mockupokhoz.

### Végpont szintaxis

```
/gradient/{width}/{height}/{from_hex}/{to_hex}
```

### Példák

```
# Egyszerű lineáris gradiens (fentről lefelé)
/gradient/800/400/3b82f6/10b981

# 45 fokos szögű gradiens
/gradient/800/400/e11d48/f59e0b?angle=45

# Radiális gradiens a középpontból
/gradient/800/400/1e293b/64748b?gradient_type=radial

# Kimeneti formátummal
/gradient/800/400/0ea5e9/ffffff?format=webp&quality=80
```

### Paraméterreferencia

- `{from_hex}` / `{to_hex}` — hex színek a # prefix nélkül
- `?angle=45` — lineáris szög fokban (0-360)
- `?gradient_type=radial` — radiális gradiensre vált
- `?format=webp` — WebP kimenet (kisebb fájlméret)

## SVG placeholder generátor

Az SVG placeholderek nem igényelnek server-side képfeldolgozást. Inline SVG-ként generálódnak testreszabható háttérszínnel, előtérszínnel és szövegcímkével.

### Végpont

```
/svg/{width}/{height}?bg={hex}&fg={hex}&text={label}
```

### Példák

```
# Default wireframe placeholder
/svg/400/300

# Custom brand colors
/svg/400/300?bg=1c1917&fg=0ea5e9

# With custom text
/svg/400/300?bg=0ea5e9&fg=ffffff&text=Hero+Section
```

### Miért SVG?

- Fájlméret 500 byte alatt
- Végtelenül skálázható minőségveszteség nélkül
- Nulla server feldolgozási overhead
- Tökéletes wireframe-ekhez és alacsony hűségű prototípusokhoz

## Közösségi média előbeállítások

A PlacePix előre meghatározott méreteket tartalmaz népszerű közösségi platformokhoz és képernyőméretekhez. Használja ezeket tökéletesen méretezett placeholder képek generálásához Instagramhoz, YouTube-hoz, TikTokhoz, LinkedInhez, X (Twitter)hez és szabványos megjelenítőkhöz.

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

### Képernyőméretek

```
/preset/mobile/nature              # 375x812
/preset/tablet/nature              # 768x1024
/preset/desktop/nature             # 1920x1080
/preset/4k/nature                  # 3840x2160
```

### Long-Tail Használati Eset: Instagram Story API

Ha közösségi média kezelő eszközt épít, és **Instagram story méretű placeholder képekre** van szüksége, használja a `/preset/instagram-story/{category}` végpontot. Kombinálja a `?fit=smart` paraméterrel portréfotókhoz és a `?format=webp&quality=70` paraméterrel az optimalizált kézbesítéshez.

## Színkereső API

A PlacePix minden képét átvizsgálja a 3 legdominánsabb szín szempontjából. Hex szín alapján keresheti át az egész könyvtárat, hogy olyan képeket találjon, amelyek illeszkednek a márka színpalettájához.

### Végponts

```
# Get an image matching a specific hex color
/color/0ea5e9/400/300

# Filter any endpoint by dominant color
/400/300/nature?color=d97706

# List all images matching a color
/api/color/3b82f6
```

### How Color Scanning Works

Indításkor a PlacePix k-means klaszterezést használva kinyeri a leggyakoribb színeket minden képből a LAB színtérben. Ez érzékileg pontos egyezéseket eredményez a nyers RGB átlagok helyett. A paletta oldal (`/palette`) vizualizálja ezeket a színeket, és lehetővé teszi a színárnyalat-kategóriák szerinti böngészést.

## Tájolás szűrés

Szűrje a véletlenszerű képeket az eredeti képarányuk alapján a választás előtt. Ez akkor hasznos, amikor olyan képekre van szüksége, amelyek természetesen illeszkednek egy elrendezésbe — tájkép a fejlécekhez, portré a kártyákhoz, vagy négyzet a miniatűrökhöz.

### Végpontok

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

### Konfiguráció

A `squarish` tűrés a `ORIENTATION_SQUARISH_TOLERANCE` környezeti változón keresztül konfigurálható (alapértelmezett: `0.15`). A `0.15` érték azt jelenti, hogy a `0.85` és `1.15` közötti képarányú képek négyzetesnek minősülnek. Állítsa `0.0`-ra a pontos 1:1-hez.

### Működés

A PlacePix a képek méreteit a fájlfejlécekből olvassa ki az inicializáló szkennelés során (helyi fájlok), valamint a háttér-metadataszkennelés során (S3-képek). A méreteket a memóriában tárolja, és a véletlenszerű vagy seed-alapú választás előtt szűri a jelölt-készletet. Ha az orientációt kérik, de nincs egyező kép, `404` hiba tér vissza.

## Szűrők és effektek

Alkalmazzon valós idejű szűrőket és effekteket bármely képre lekérdezési paramétereken keresztül. Minden feldolgozás szerveroldalon történik és cache-elésre kerül a későbbi kérésekhez.

### Színbeállítások

```
?grayscale=1               # Fekete-fehér
?sepia=1                   # Meleg szépia tónus
?tint=0ea5e9               # Hex szín overlay
?brightness=1.3            # 0,0-tól 2,0-ig
?contrast=1.2              # 0,0-tól 2,0-ig
?saturation=2.0            # 0,0-tól 2,0-ig
?invert=true               # Színek invertálása
?posterize=4               # Színszintek (1-8)
?duotone=ff0000,0000ff     # Kétszínes térkép
```

### Képeffektek

```
?blur=2                    # Gauss-elmosódás (1-10)
?sharpen=1.5               # Élesítés mértéke
?emboss=true               # 3D domborítás
?edges=sobel               # Éldetektálás
?edges=canny               # Canny élek
?halftone=4                # Pontminta
?oil_painting=true         # Olajfestmény stílus
?pencil_sketch=true        # Ceruza rajz
?cartoon=true              # Rajzfilm effekt
?vignette=0.5              # Sötétített szélek (0-1)
```

### Overlay paraméterek

```
?text=Hello+World          # Szöveg overlay
?border=4,ffffff           # Keret szélessége és színe
?watermark=1               # Beállított vízjel alkalmazása
?padding=20                # Belső padding
```

## Avatar Generátor

Generálj determinisztikus avatarokat bármilyen névből vagy emailből. A PlacePix két avatar típust támogat: **Betű avatar** (színes kezdőbetűk) és **Multiavatar** (multikulturális vektor avatarok).

### Végpont

```
/avatar/{size}/{name}
/avatar/{size}/{name}.{ext}
```

### Paraméterek

- `type` — avatar type: `letter` (default) or `multiavatar`
- `size` — pixel size (e.g. `64`, `128`, `256`)
- `name` — any string; used as seed for the avatar

#### Betű avatar (`type=letter`)

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

### Példák

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

### Miért használj betű avatarokat?

- Nulla külső függőség — nincs Gravatar vagy harmadik féltől származó avatar szolgáltatás
- Determinisztikus — ugyanaz a név mindig ugyanazt a színt adja
- SVG támogatás — végtelenül skálázható, tökéletes HiDPI kijelzőkhöz
- Hat beépített színpaletta bármilyen márka esztétikához

### Miért használj Multiavatart?

- 12 milliárd egyedi multikulturális avatar
- Determinisztikus — ugyanaz a név mindig ugyanazt az avatart adja
- Tiszta SVG kimenet — kis fájlméret, végtelenül skálázható
- Nem szükségesek külső API hívások

## REST API gyorsreferencia

Minden endpoint támogatja a CORS-t és hosszú távú cache fejlécekkel tér vissza a képekkel. Base64 JSON kimenet elérhető kis thumbnailokhoz.

### Képvégpontok

- `GET /{width}/{height}/{category}` — Véletlenszerű kép kategóriából
- `GET /{width}/{height}` — Véletlenszerű kép az összes kategóriából
- `GET /id/{id}/{width}/{height}` — Konkrét kép azonosító alapján
- `GET /ratio/{ratio}/{width}/{category}` — Képarány kép
- `GET /preset/{preset}/{category}` — Közösségi média előbeállítás
- `GET /color/{hex}/{width}/{height}` — Színmegfeleltetett kép
- `GET /gradient/{w}/{h}/{from}/{to}` — Gradiens kép
- `GET /svg/{width}/{height}` — SVG helyőrző
- `GET /avatar/{size}/{name}` — Betű avatar (PNG/SVG)

### Metadata végpontok

- `GET /api/images` — Kategóriák és összesítők listázása
- `GET /api/info/id/{id}` — Kép metaadatok (méretek, színek, formátum)
- `GET /api/color/{hex}` — Színt megfeleltető képek

### Health végpontok

- `GET /health` — Liveness probe (Docker/K8s)
- `GET /ready` — Readiness probe (503 amíg a képek nem töltődnek be)

## Szakértelem és referenciák

- Aktív közreműködők az open-source ökoszisztémában 2008 óta
- Minden kód open source MIT License alatt és auditálható a <a href="https://github.com/riadvice/placepix" target="_blank" class="text-accent hover:underline">GitHub</a>-on

## Gyakran ismételt kérdések

### Hogyan telepítem a PlacePix-et Dockerrel?

Futtassa a `docker run -d -p 3000:3000 -v ./images:/app/images riadvice/placepix:latest` parancsot. Mountolja a képmappáját és a szolgáltatás azonnal indul intelligens szkenneléssel.

### Mi az az arcérzékeny intelligens vágás?

A PlacePix OpenCV Haar kaskádokat használ az arcok észlelésére a képeken. Amikor `?fit=smart` paramétert ad bármely URL-hez, a vágási régió az észlelt arcok középpontjára tolódik, a geometriai középpont használata helyett. Ha nincs arc, visszaáll a standard középső vágásra.

### Generálhatok gradiens placeholder képeket fotók feltöltése nélkül?

Igen. A `/gradient/{width}/{height}/{from}/{to}` végpont teljesen URL paraméterekből generál gradiens képeket. Nincs szükség feltöltött képekre. SVG helyőrzőket is készíthet a `/svg/{width}/{height}` végponttal.

### Hogyan generálok Instagram story méretű placeholder képeket API-n keresztül?

Használja a preset végpontot: `/preset/instagram-story/{category}`. Ez egy 1080x1920 képet ad vissza. Kombinálja `?format=webp&quality=70` paraméterrel az optimalizált kézbesítéshez és `?fit=smart` paraméterrel a portrét biztonságos vágáshoz.

### Támogatja a PlacePix az S3-kompatibilis objektumtárolást?

Igen. A PlacePix működik OVHcloud Object Storage, AWS S3, MinIO és bármely S3-kompatibilis szolgáltatóval. Konfigurálja az endpoint, bucket, access key és secret key beállításokat környezeti változókon keresztül.

### Milyen kimeneti formátumok támogatottak?

WebP, AVIF, JPEG, PNG, SVG és base64 JSON. Használja a `.webp`, `.avif` vagy `.png` kiterjesztést, vagy adjon hozzá `?format=webp` query paramétert. Az AVIF a legkisebb fájlokat adja; a PNG lossless.

### Ingyenes a PlacePix kereskedelmi felhasználásra?

Igen. A PlacePix MIT License alatt kiadott és ingyenes mind személyes, mind kereskedelmi felhasználásra. Mivel self-hosted, nincsenek használati korlátozások, API kulcsok és kérésenkénti számlázás.