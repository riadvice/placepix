---
title: Průvodce pro vývojáře PlacePix — Samohostované API placeholder obrázků a referenční příručka funkcí
description: Kompletní průvodce pro vývojáře PlacePix a referenční příručka API. Naučte se nasazovat obrázky placeholder pomocí Dockeru, generovat gradienty a SVG, a používat předvolby sociálních sítí pro Instagram, YouTube a další.
keywords: samohostované placeholder API, inteligentní ořez s rozpoznáváním obličejů, generátor gradientních placeholderů, Docker služba placeholder obrázků, Instagram story placeholder API, generátor SVG placeholderů, vývojářské image API
author: RIADVICE
robots: index, follow
og_title: Průvodce pro vývojáře PlacePix — Samohostované API placeholder obrázků a referenční příručka funkcí
og_description: Kompletní průvodce pro vývojáře pokrývající nasazení Dockeru, inteligentní ořez, gradientní placeholdery, generování SVG a předvolby sociálních sítí.
twitter_title: Průvodce pro vývojáře PlacePix — Samohostované API placeholder obrázků a referenční příručka funkcí
twitter_description: Kompletní průvodce pro vývojáře pokrývající nasazení Dockeru, inteligentní ořez, gradientní placeholdery, generování SVG a předvolby sociálních sítí.
jsonld_name: Průvodce pro vývojáře PlacePix — Samohostované API placeholder obrázků a referenční příručka funkcí
jsonld_description: Kompletní průvodce pro vývojáře a referenční příručka API pro PlacePix, samohostovanou službu placeholder obrázků. Pokrývá nasazení Dockeru, inteligentní ořez s rozpoznáváním obličejů, gradientní placeholdery, generování SVG a předvolby sociálních sítí.
jsonld_proficiency: Expert
jsonld_dependencies: Docker, Python 3.12, FastAPI
header_title: Průvodce pro vývojáře PlacePix
header_subtitle: Kompletní API reference a dokumentace funkcí pro samohostovanou službu placeholder obrázků. Pokrývá nasazení Dockeru, inteligentní ořez, gradientní placeholdery, generování SVG, písmenné avatary a předvolby sociálních sítí.
author_label: Od
updated_label: "Poslední aktualizace: květen 2026"
github_label: Open Source na GitHubu
toc_title: Obsah
---

## Co je PlacePix?

PlacePix je **samohostovaná služba placeholder obrázků** vytvořená pro vývojáře a designové týmy. Na rozdíl od služeb placeholder třetích stran, které vyžadují externí síťová volání a mohou zmizet, PlacePix běží výhradně na vaší vlastní infrastruktuře. Přetáhněte obrázky do složek a okamžitě získejte URL endpointy, které poskytují změněné velikosti, filtrované a formátované obrázky.

Služba je napsána v Pythonu pomocí FastAPI s image processingem poháněným Pillow a OpenCV. Podporuje nasazení Docker a S3-kompatibilní úložiště objektů.

### Funkce

- **Nulová konfigurace** — přetáhněte obrázky do složek a běžte
- **Ořez s rozpoznáváním obličejů** — OpenCV detekuje a centruje obličeje
- **Gradientní a SVG placeholdery** — nejsou potřeba žádné obrázky
- **Předvolby sociálních sítí** — vestavěné velikosti Instagram, YouTube, TikTok
- **Vyhledávání podle barev** — najděte obrázky odpovídající paletě vaší značky
- **Písmenné avatary** — deterministické profilové obrázky z jmen

## Průvodce nasazením Dockeru

Nejrychlejší způsob, jak spustit PlacePix, je pomocí Dockeru. Jedním příkazem nasadíte celou službu s inteligentním skenováním, extrakcí barev a vestavěným URL builderem.

### Jednořádkové nasazení

```bash
docker run -d -p 3000:3000 \
  -v ./images:/app/images \
  riadvice/placepix:latest
```

### Docker Compose (Doporučeno)

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

### Perzistentní data a prostředí

Mountujte jak `/app/images` (vaši knihovnu obrázků), tak `/app/data` (cache skenování a metadata), abyste zachovali stav při restartech kontejnerů. Konfigurujte chování pomocí proměnných prostředí nebo souboru `.env`.

### OVHcloud S3-kompatibilní úložiště

PlacePix podporuje jakýkoli S3-kompatibilní backend. Pro OVHcloud Object Storage nastavte:

```
S3_ENABLED=true
S3_ENDPOINT=https://s3.rbx.io.cloud.ovh.net
S3_ACCESS_KEY=your-key
S3_SECRET_KEY=your-secret
S3_BUCKET=your-bucket
S3_REGION=rbx
```

## Inteligentní ořez s rozpoznáváním obličejů

Standardní centrální ořez může v portrétní fotografii proříznout obličeje. PlacePix to řeší pomocí **inteligentního ořezu s rozpoznáváním obličejů** poháněného kaskádami Haar OpenCV.

### Jak to funguje

Když požadavek obsahuje `?fit=smart`, PlacePix skenuje obrázek pomocí OpenCV na přítomnost lidských obličejů. Pokud jsou obličeje detekovány, okno ořezu je posunuto tak, aby se centroid obličeje nacházel co nejblíže k průsečíkům zlatého řezu. Pokud nejsou nalezeny žádné obličeje, vrátí se k standardnímu centrálnímu ořezu.

### Příklady API

```
# Ořez s rozpoznáváním obličejů (detekuje a centruje obličeje)
/400/300/people?fit=smart

# Standardní centrální ořez
/400/300/people?fit=crop

# Vyplnění krycí plochy (může se natáhnout)
/400/300/people?fit=cover

# Obsah (letterboxing)
/400/300/people?fit=contain
```

### Kdy použít Smart Crop

- Portrétní fotografie a headshoty
- Týmové stránky, kde obličeje hrají roli
- Miniatury sociálních sítí
- Jakýkoli scénář, kde geometrický centrální ořez ničí kompozici

## API gradientních placeholderů

Generujte lineární a radiální gradientní obrázky za běhu bez nahrávání jakýchkoli prostředků. Ideální pro hlavní pozadí, stavy načítání a designové mockupy.

### Syntaxe endpointu

```
/gradient/{width}/{height}/{from_hex}/{to_hex}
```

### Příklady

```
# Jednoduchý lineární gradient (shora dolů)
/gradient/800/400/3b82f6/10b981

# 45 stupňový úhlový gradient
/gradient/800/400/e11d48/f59e0b?angle=45

# Radiální gradient ze středu
/gradient/800/400/1e293b/64748b?gradient_type=radial

# S výstupním formátem
/gradient/800/400/0ea5e9/ffffff?format=webp&quality=80
```

### Referenční příručka parametrů

- `{from_hex}` / `{to_hex}` — hex barvy bez prefixu #
- `?angle=45` — lineární úhel ve stupních (0-360)
- `?gradient_type=radial` — přepne na radiální gradient
- `?format=webp` — WebP výstup (menší velikost souboru)

## Generátor SVG placeholderů

SVG placeholdery nevyžadují žádné zpracování obrázků na straně serveru. Jsou generovány jako inline SVG s přizpůsobitelnou barvou pozadí, barvou popředí a textovým štítkem.

### Koncový bod

```
/svg/{width}/{height}?bg={hex}&fg={hex}&text={label}
```

### Příklady

```
# Výchozí wireframe placeholder
/svg/400/300

# Vlastní barvy značky
/svg/400/300?bg=1c1917&fg=0ea5e9

# S vlastním textem
/svg/400/300?bg=0ea5e9&fg=ffffff&text=Hero+Section
```

### Proč SVG?

- Velikost souboru pod 500 bajty
- Nekonečně škálovatelné bez ztráty kvality
- Nulová režie zpracování na serveru
- Perfektní pro wireframy a low-fidelity prototypy

## Předvolby pro sociální sítě

PlacePix zahrnuje předdefinované rozměry pro populární sociální platformy a velikosti obrazovek. Použijte je k generování perfektně dimenzovaných placeholder obrázků pro Instagram, YouTube, TikTok, LinkedIn, X (Twitter) a standardní displeje.

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

### Velikosti obrazovek

```
/preset/mobile/nature              # 375x812
/preset/tablet/nature              # 768x1024
/preset/desktop/nature             # 1920x1080
/preset/4k/nature                  # 3840x2160
```

### Případ použití Long-Tail: Instagram Story API

Pokud vytváříte nástroj pro správu sociálních sítí a potřebujete **placeholder obrázky ve velikosti Instagram story**, použijte `/preset/instagram-story/{category}`. Kombinujte s `?fit=smart` pro portrétní fotografie a `?format=webp&quality=70` pro optimalizované doručování.

## API pro vyhledávání podle barvy

Každý obrázek v PlacePix je skenován na jeho 3 dominantní barvy. Můžete prohledávat celou knihovnu podle hex barvy a najít obrázky, které odpovídají paletě vaší značky.

### Koncový bods

```
# Get an image matching a specific hex color
/color/0ea5e9/400/300

# Filter any endpoint by dominant color
/400/300/nature?color=d97706

# List all images matching a color
/api/color/3b82f6
```

### How Color Scanning Works

Při spuštění PlacePix extrahuje z každého obrázku nejčastější barvy pomocí k-means clustering v LAB color space. To produkuje perceptuálně přesné shody spíše než raw RGB průměry. Stránka palety (`/palette`) vizualizuje tyto barvy a umožňuje vám procházet podle kategorie odstínů.

## Filtrování podle orientace

Před výběrem filtrujte náhodné obrázky podle jejich nativního poměru stran. To je užitečné, když potřebujete obrázky, které se přirozeně vejdou do rozvržení — krajina pro záhlaví, portrét pro karty nebo čtverec pro náhledy.

### Koncové body

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

### Konfigurace

Tolerance `squarish` je konfigurovatelná pomocí proměnné prostředí `ORIENTATION_SQUARISH_TOLERANCE` (výchozí: `0.15`). Hodnota `0.15` znamená, že obrázky s poměrem stran mezi `0.85` a `1.15` jsou považovány za čtvercové. Nastavte `0.0` pro přesný poměr 1:1.

### Jak to funguje

PlacePix čte rozměry obrázků ze záhlaví souborů během počátečního skenování (místní soubory) a během skenování metadat na pozadí (S3 obrázky). Rozměry jsou uloženy v paměti a použity k filtrování kandidátů před náhodným nebo deterministickým výběrem. Pokud je požadována orientace, ale žádné obrázky neodpovídají, vrátí se `404`.
## Filtry a efekty

Aplikujte real-time filtry a efekty na jakýkoli obrázek pomocí query parametrů. Veškeré zpracování probíhá na straně serveru a je cacheováno pro následné požadavky.

### Úpravy barev

```
?grayscale=1               # Černobílé
?sepia=1                   # Teplý sépiový tón
?tint=0ea5e9               # Hex barevný overlay
?brightness=1.3            # 0,0 až 2,0
?contrast=1.2              # 0,0 až 2,0
?saturation=2.0            # 0,0 až 2,0
?invert=true               # Invertovat barvy
?posterize=4               # Úrovně barev (1-8)
?duotone=ff0000,0000ff     # Dvoubarevná mapa
```

### Efekty obrázků

```
?blur=2                    # Gaussovské rozostření (1-10)
?sharpen=1.5               # Množství zaostření
?emboss=true               # 3D reliéf
?edges=sobel               # Detekce hran
?edges=canny               # Canny hrany
?halftone=4                # Bodový vzor
?oil_painting=true         # Styl olejomalby
?pencil_sketch=true        # Tužkový náčrt
?cartoon=true              # Cartoon efekt
?vignette=0.5              # Ztmavení okrajů (0-1)
```

### Parametry overlay

```
?text=Hello+World          # Textový overlay
?border=4,ffffff           # Šířka a barva okraje
?watermark=1               # Aplikovat nakonfigurovaný vodoznak
?padding=20                # Vnitřní padding
```

## Generátor písmenných avatarů

Generujte deterministické písmenné avatary z jakéhokoli jména nebo e-mailu. Ideální pro placeholder uživatelských profilů, komentářové systémy a týmové adresáře. Každé jméno vždy produkuje stejnou barvu, takže avatary jsou konzistentní napříč relacemi.

### Koncový bod

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

### Příklady

```
# Jednoduchý 128px avatar
/avatar/128/John+Doe

# Kruhový avatar s vlastním okrajem
/avatar/128/John+Doe?circle=true&border=2,ffffff

# Jedna iniciála, pastelová paleta
/avatar/64/Alice?single=true&palette=pastel

# SVG výstup (škálovatelný, pod 500 bajtů)
/avatar/128/John+Doe.svg
```

### Proč používat písmenné avatary?

- Nulové externí závislosti — žádný Gravatar nebo avatarová služba třetí strany
- Deterministické — stejné jméno vždy produkuje stejnou barvu
- Podpora SVG — nekonečně škálovatelné, ideální pro HiDPI displeje
- Čtyři vestavěné barevné palety pro jakoukoli estetiku značky

## Stručný přehled REST API

Všechny endpointy podporují CORS a vracejí obrázky s dlouhodobými cache hlavičkami. Base64 JSON výstup je dostupný pro malé náhledy.

### Endpointy obrázků

- `GET /{width}/{height}/{category}` — Náhodný obrázek z kategorie
- `GET /{width}/{height}` — Náhodný obrázek ze všech kategorií
- `GET /id/{id}/{width}/{height}` — Konkrétní obrázek podle ID
- `GET /ratio/{ratio}/{width}/{category}` — Obrázek s poměrem stran
- `GET /preset/{preset}/{category}` — Předvolba sociálních médií
- `GET /color/{hex}/{width}/{height}` — Obrázek s odpovídající barvou
- `GET /gradient/{w}/{h}/{from}/{to}` — Gradientní obrázek
- `GET /svg/{width}/{height}` — SVG placeholder
- `GET /avatar/{size}/{name}` — Písmenný avatar (PNG/SVG)

### Metadata endpointy

- `GET /api/images` — Seznam kategorií a celkových počtů
- `GET /api/info/id/{id}` — Metadata obrázku (rozměry, barvy, formát)
- `GET /api/color/{hex}` — Obrázky odpovídající barvě

### Health endpointy

- `GET /health` — Liveness probe (Docker/K8s)
- `GET /ready` — Readiness probe (503 dokud nejsou obrázky načteny)

## Odbornost a pověření

- Aktivní přispěvatelé do open-source ekosystému od roku 2008
- Veškerý kód je open source pod MIT licencí a auditovatelný na <a href="https://github.com/riadvice/placepix" target="_blank" class="text-accent hover:underline">GitHubu</a>

## Často kladené otázky

### Jak nasadím PlacePix pomocí Dockeru?

Spusťte `docker run -d -p 3000:3000 -v ./images:/app/images riadvice/placepix:latest`. Mountujte vaši složku s obrázky a služba se okamžitě spustí s povoleným inteligentním skenováním.

### Co je inteligentní ořez s rozpoznáváním obličejů?

PlacePix používá Haar kaskády OpenCV k detekci obličejů v obrázcích. Když přidáte `?fit=smart` k jakémukoli URL, oblast ořezu se posune tak, aby se vycentrovala na detekované obličeje, namísto použití geometrického středu. Pokud není nalezen žádný obličej, vrátí se k standardnímu centrálnímu ořezu.

### Mohu generovat gradientní placeholder obrázky bez nahrávání fotografií?

Ano. Endpoint `/gradient/{width}/{height}/{from}/{to}` generuje gradientní obrázky výhradně z URL parametrů. Nejsou vyžadovány žádné nahrané obrázky. Můžete také vytvářet SVG placeholdery pomocí `/svg/{width}/{height}`.

### Jak generuji placeholder obrázky ve velikosti Instagram story přes API?

Použijte preset endpoint: `/preset/instagram-story/{category}`. To vrací obrázek 1080x1920. Kombinujte s `?format=webp&quality=70` pro optimalizované doručování a `?fit=smart` pro bezpečné ořezání portrétů.

### Podporuje PlacePix S3-kompatibilní úložiště?

Ano. PlacePix funguje s OVHcloud Object Storage, AWS S3, MinIO a jakýmkoli S3-kompatibilním poskytovatelem. Nakonfigurujte endpoint, bucket, přístupový klíč a tajný klíč pomocí proměnných prostředí.

### Jaké výstupní formáty jsou podporovány?

WebP, AVIF, JPEG, PNG, SVG a base64 JSON. Použijte `.webp`, `.avif` nebo `.png` jako příponu souboru, nebo přidejte `?format=webp` jako query parametr. AVIF produkuje nejmenší soubory; PNG je bezztrátový.

### Je PlacePix zdarma pro komerční použití?

Ano. PlacePix je vydán pod MIT licencí a je zdarma jak pro osobní, tak pro komerční použití. Protože je self-hosted, neexistují žádné limity používání, žádné API klíče a žádné fakturace za požadavek.
