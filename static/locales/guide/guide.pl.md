---
title: Przewodnik dewelopera PlacePix — Samodzielnie hostowane API obrazów placeholder i referencja funkcji
description: Kompletny przewodnik dewelopera PlacePix i referencja API. Naucz się wdrażać obrazy placeholder za pomocą Dockera, generować gradienty i SVG, oraz używać presetów mediów społecznościowych dla Instagram, YouTube i innych.
keywords: API obrazów placeholder self-hosted, placeholder z przycinaniem wykrywającym twarze, generator gradientowych placeholderów, usługa obrazów placeholder Docker, API placeholderów Instagram Story, generator placeholderów SVG, API obrazów dewelopera
author: RIADVICE
robots: index, follow
og_title: Przewodnik dewelopera PlacePix — Samodzielnie hostowane API obrazów placeholder i referencja funkcji
og_description: Kompletny przewodnik dewelopera obejmujący wdrażanie Docker, inteligentne przycinanie, gradientowe placeholdery, generowanie SVG i presety mediów społecznościowych.
twitter_title: Przewodnik dewelopera PlacePix — Samodzielnie hostowane API obrazów placeholder i referencja funkcji
twitter_description: Kompletny przewodnik dewelopera obejmujący wdrażanie Docker, inteligentne przycinanie, gradientowe placeholdery, generowanie SVG i presety mediów społecznościowych.
jsonld_name: Przewodnik dewelopera PlacePix — Samodzielnie hostowane API obrazów placeholder i referencja funkcji
jsonld_description: Kompletny przewodnik dewelopera i referencja API dla PlacePix, samodzielnie hostowanej usługi obrazów placeholder. Obejmuje wdrażanie Docker, inteligentne przycinanie z rozpoznawaniem twarzy, gradientowe placeholdery, generowanie SVG i presety mediów społecznościowych.
jsonld_proficiency: Expert
jsonld_dependencies: Docker, Python 3.12, FastAPI
header_title: Przewodnik dewelopera PlacePix
header_subtitle: Kompletna referencja API i dokumentacja funkcji dla samodzielnie hostowanej usługi obrazów placeholder. Obejmuje wdrażanie Docker, inteligentne przycinanie, gradientowe placeholdery, generowanie SVG, awatary literowe i presety mediów społecznościowych.
author_label: Autor
updated_label: "Ostatnia aktualizacja: maj 2026"
github_label: Open Source na GitHubie
toc_title: Spis Treści
---

## Co to jest PlacePix?

PlacePix to **samodzielnie hostowana usługa obrazów placeholder** stworzona dla deweloperów i zespołów projektowych. W przeciwieństwie do usług placeholder stron trzecich, które wymagają zewnętrznych wywołań sieciowych i mogą zniknąć, PlacePix działa całkowicie na własnej infrastrukturze. Upuszczaj obrazy do folderów i natychmiast otrzymuj endpointy URL serwujące przeskalowane, przefiltrowane i sformatowane obrazy.

Usługa jest napisana w Pythonie przy użyciu FastAPI z przetwarzaniem obrazów zasilanym przez Pillow i OpenCV. Obsługuje wdrażanie Docker i kompatybilną z S3 pamięć masową obiektów.

### Funkcje

- **Konfiguracja zero** — upuszczaj obrazy do folderów i działaj
- **Inteligentne przycinanie twarzy** — OpenCV wykrywa i centruje twarze
- **Gradientowe i SVG placeholdery** — nie wymagają obrazów
- **Presety mediów społecznościowych** — wbudowane rozmiary Instagram, YouTube, TikTok
- **Wyszukiwanie kolorów** — znajdź obrazy pasujące do palety marki
- **Awatary literowe** — deterministyczne obrazy profilowe z imion

## Przewodnik wdrażania Docker

Najszybszym sposobem na uruchomienie PlacePix jest Docker. Jedno polecenie wdraża całą usługę z inteligentnym skanowaniem, ekstrakcją kolorów i wbudowanym konstruktorem URL.

### Wdrażanie jednym wierszem

```bash
docker run -d -p 3000:3000 \
  -v ./images:/app/images \
  riadvice/placepix:latest
```

### Docker Compose (Zalecane)

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

### Trwałe dane i środowisko

Zamontuj zarówno `/app/images` (bibliotekę obrazów), jak i `/app/data` (pamięć podręczną skanowania i metadane), aby zachować stan między ponownymi uruchomieniami kontenera. Skonfiguruj zachowanie za pomocą zmiennych środowiskowych lub pliku `.env`.

### OVHcloud Pamięć masowa zgodna z S3

PlacePix obsługuje dowolny backend zgodny z S3. Dla OVHcloud Object Storage, ustaw:

```
S3_ENABLED=true
S3_ENDPOINT=https://s3.rbx.io.cloud.ovh.net
S3_ACCESS_KEY=your-key
S3_SECRET_KEY=your-secret
S3_BUCKET=your-bucket
S3_REGION=rbx
```

## Inteligentne przycinanie z rozpoznawaniem twarzy

Standardowe centralne przycinanie może przeciąć twarze na fotografii portretowej. PlacePix rozwiązuje to za pomocą **inteligentnego przycinania z rozpoznawaniem twarzy** napędzanego kaskadami Haar OpenCV.

### Jak to działa

Gdy żądanie zawiera `?fit=smart`, PlacePix skanuje obraz w poszukiwaniu ludzkich twarzy przy użyciu OpenCV. Jeśli twarze zostaną wykryte, okno przycinania jest przesuwane, aby środek ciężkości twarzy znajdował się jak najbliżej punktów przecięcia złotego podziału. Jeśli nie znaleziono twarzy, następuje powrót do standardowego centralnego przycinania.

### Przykłady API

```
# Przycinanie z rozpoznawaniem twarzy (wykrywa i centruje twarze)
/400/300/people?fit=smart

# Standardowe centralne przycinanie
/400/300/people?fit=crop

# Wypełnienie okładki (może rozciągnąć)
/400/300/people?fit=cover

# Zawieranie (letterboxing)
/400/300/people?fit=contain
```

### Kiedy używać inteligentnego przycinania

- Fotografia portretowa i headshoty
- Strony zespołów, gdzie twarze mają znaczenie
- Miniaturki mediów społecznościowych
- Każdy scenariusz, w którym geometryczne centralne przycinanie psuje kompozycję

## API placeholder gradientowych

Generuj liniowe i radialne obrazy gradientowe na żywo bez przesyłania zasobów. Idealne dla teł hero, stanów ładowania i makiet projektowych.

### Składnia endpointu

```
/gradient/{width}/{height}/{from_hex}/{to_hex}
```

### Przykłady

```
# Prosty gradient liniowy (z góry na dół)
/gradient/800/400/3b82f6/10b981

# Gradient pod kątem 45 stopni
/gradient/800/400/e11d48/f59e0b?angle=45

# Gradient radialny ze środka
/gradient/800/400/1e293b/64748b?gradient_type=radial

# Z formatem wyjściowym
/gradient/800/400/0ea5e9/ffffff?format=webp&quality=80
```

### Referencja parametrów

- `{from_hex}` / `{to_hex}` — kolory hex bez prefiksu #
- `?angle=45` — kąt liniowy w stopniach (0-360)
- `?gradient_type=radial` — przełącza na gradient radialny
- `?format=webp` — wyjście WebP (mniejszy rozmiar pliku)

## Generator placeholder SVG

SVG placeholdery nie wymagają przetwarzania obrazów po stronie serwera. Są generowane jako inline SVG z konfigurowalnym kolorem tła, kolorem pierwszego planu i etykietą tekstową.

### Endpoint

```
/svg/{width}/{height}?bg={hex}&fg={hex}&text={label}
```

### Przykłady

```
# Default wireframe placeholder
/svg/400/300

# Custom brand colors
/svg/400/300?bg=1c1917&fg=0ea5e9

# With custom text
/svg/400/300?bg=0ea5e9&fg=ffffff&text=Hero+Section
```

### Dlaczego SVG?

- Rozmiar pliku poniżej 500 bajtów
- Nieskończenie skalowalny bez utraty jakości
- Zerowe obciążenie przetwarzania serwera
- Idealny dla wireframe'ów i prototypów low-fidelity

## Presety mediów społecznościowych

PlacePix zawiera predefiniowane wymiary dla popularnych platform społecznościowych i rozmiarów ekranów. Użyj ich do generowania perfekcyjnie dopasowanych obrazów placeholder dla Instagrama, YouTube'a, TikToka, LinkedIn, X (Twitter) i standardowych wyświetlaczy.

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

### Rozmiary ekranów

```
/preset/mobile/nature              # 375x812
/preset/tablet/nature              # 768x1024
/preset/desktop/nature             # 1920x1080
/preset/4k/nature                  # 3840x2160
```

### Przypadek użycia Long-Tail: Instagram Story API

Jeśli budujesz narzędzie do zarządzania mediami społecznościowymi i potrzebujesz **obrazów placeholder o rozmiarze Instagram Story**, użyj `/preset/instagram-story/{category}`. Połącz z `?fit=smart` dla zdjęć portretowych i `?format=webp&quality=70` dla zoptymalizowanej dostawy.

## API wyszukiwania po kolorze

Każdy obraz w PlacePix jest skanowany pod kątem 3 dominujących kolorów. Możesz przeszukiwać całą bibliotekę według koloru hex, aby znaleźć obrazy pasujące do palety marki.

### Endpoints

```
# Pobierz obraz pasujący do określonego koloru hex
/color/0ea5e9/400/300

# Filtruj dowolny endpoint według koloru dominującego
/400/300/nature?color=d97706

# Wyświetl wszystkie obrazy pasujące do koloru
/api/color/3b82f6
```

### Jak działa skanowanie kolorów

Podczas uruchamiania PlacePix wyodrębnia najczęstsze kolory z każdego obrazu za pomocą klastrowania k-means w przestrzeni kolorów LAB. Daje to percepcyjnie dokładne dopasowania, a nie surowe średnie RGB. Strona palety (`/palette`) wizualizuje te kolory i pozwala przeglądać według kategorii odcieni.

## Filtrowanie według orientacji

Filtruj losowe obrazy według ich natywnego proporcji przed wyborem. Jest to przydatne, gdy potrzebujesz obrazów, które naturalnie pasują do układu — krajobraz dla nagłówków, portret dla kart lub kwadrat dla miniaturek.

### Punkty końcowe

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

### Konfiguracja

Tolerancja `squarish` jest konfigurowalna przez zmienną środowiskową `ORIENTATION_SQUARISH_TOLERANCE` (domyślnie: `0.15`). Wartość `0.15` oznacza, że obrazy z proporcjami między `0.85` a `1.15` są uznawane za kwadratowe. Ustaw `0.0` dla dokładnego 1:1.

### Jak to działa

PlacePix odczytuje wymiary obrazów z nagłówków plików podczas początkowego skanowania (pliki lokalne) oraz podczas skanowania metadanych w tle (obrazy S3). Wymiary są przechowywane w pamięci i używane do filtrowania puli kandydatów przed losowym lub deterministycznym wyborem. Jeśli żądana jest orientacja, ale żaden obraz nie pasuje, zwracany jest `404`.
## Filtry i efekty

Stosuj filtry i efekty w czasie rzeczywistym do dowolnego obrazu za pomocą parametrów zapytania. Całe przetwarzanie odbywa się po stronie serwera i jest buforowane dla kolejnych żądań.

### Korekty kolorów

```
?grayscale=1               # Czarno-białe
?sepia=1                   # Ciepły odcień sepii
?tint=0ea5e9               # Nałożenie koloru hex
?brightness=1.3            # 0,0 do 2,0
?contrast=1.2              # 0,0 do 2,0
?saturation=2.0            # 0,0 do 2,0
?invert=true               # Odwróć kolory
?posterize=4               # Poziomy kolorów (1-8)
?duotone=ff0000,0000ff     # Dwukolorowa mapa
```

### Efekty obrazu

```
?blur=2                    # Rozmycie gaussowskie (1-10)
?sharpen=1.5               # Ilość wyostrzania
?emboss=true               # Płaskorzeźba 3D
?edges=sobel               # Wykrywanie krawędzi
?edges=canny               # Krawędzie Canny
?halftone=4                # Wzorzec kropek
?oil_painting=true         # Styl malowania olejnego
?pencil_sketch=true        # Szkic ołówkowy
?cartoon=true              # Efekt kreskówkowy
?vignette=0.5              # Przyciemnianie krawędzi (0-1)
```

### Parametry nakładki

```
?text=Hello+World          # Nakładka tekstu
?border=4,ffffff           # Szerokość i kolor ramki
?watermark=1               # Zastosuj skonfigurowany znak wodny
?padding=20                # Wewnętrzne wypełnienie
```

## Generator Avatarów

Generuj deterministyczne awatary z dowolnego imienia lub emaila. PlacePix obsługuje dwa typy awatarów: **Avatar literowy** (kolorowe inicjały) i **Multiavatar** (multikulturowe awatary wektorowe).

### Endpoint

```
/avatar/{size}/{name}
/avatar/{size}/{name}.{ext}
```

### Parametry

- `type` — avatar type: `letter` (default) or `multiavatar`
- `size` — pixel size (e.g. `64`, `128`, `256`)
- `name` — any string; used as seed for the avatar

#### Avatar literowy (`type=letter`)

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

### Przykłady

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

### Dlaczego warto używać avatarów literowych?

- Zero zewnętrznych zależności — żadnego Gravatar ani usługi avatarów stron trzecich
- Deterministyczny — to samo imię zawsze daje ten sam kolor
- Wsparcie SVG — nieskończenie skalowalne, idealne dla wyświetlaczy HiDPI
- Sześć wbudowanych palet kolorów dla każdej estetyki marki

### Dlaczego warto używać Multiavatara?

- 12 miliardów unikalnych multikulturowych awatarów
- Deterministyczny — to samo imię zawsze daje ten sam awatar
- Czyste wyjście SVG — mały rozmiar pliku, nieskończenie skalowalne
- Nie są wymagane zewnętrzne wywołania API

## Szybka referencja REST API

Wszystkie endpointy obsługują CORS i zwracają obrazy z nagłówkami długoterminowej pamięci podręcznej. Wyjście Base64 JSON jest dostępne dla małych miniatur.

### Endpointy obrazów

- `GET /{width}/{height}/{category}` — Losowy obraz z kategorii
- `GET /{width}/{height}` — Losowy obraz ze wszystkich kategorii
- `GET /id/{id}/{width}/{height}` — Konkretny obraz po ID
- `GET /ratio/{ratio}/{width}/{category}` — Obraz o określonym proporcji
- `GET /preset/{preset}/{category}` — Preset mediów społecznościowych
- `GET /color/{hex}/{width}/{height}` — Obraz dopasowany kolorystycznie
- `GET /gradient/{w}/{h}/{from}/{to}` — Obraz gradientowy
- `GET /svg/{width}/{height}` — Placeholder SVG
- `GET /avatar/{size}/{name}` — Awatar literowy (PNG/SVG)

### Endpointy metadanych

- `GET /api/images` — Lista kategorii i sum
- `GET /api/info/id/{id}` — Metadane obrazu (wymiary, kolory, format)
- `GET /api/color/{hex}` — Obrazy pasujące do koloru

### Endpointy zdrowia

- `GET /health` — Sonda liveness (Docker/K8s)
- `GET /ready` — Sonda readiness (503 do momentu załadowania obrazów)

## Wiedza specjalistyczna i referencje

- Aktywni współtwórcy ekosystemu open source od 2008 roku
- Cały kod jest open source na licencji MIT i możliwy do audytu na <a href="https://github.com/riadvice/placepix" target="_blank" class="text-accent hover:underline">GitHub</a>

## Często zadawane pytania

### Jak wdrożyć PlacePix za pomocą Dockera?

Uruchom `docker run -d -p 3000:3000 -v ./images:/app/images riadvice/placepix:latest`. Zamontuj folder z obrazami, a usługa uruchomi się natychmiast z włączonym inteligentnym skanowaniem.

### Czym jest inteligentne przycinanie z rozpoznawaniem twarzy?

PlacePix używa kaskad Haar OpenCV do wykrywania twarzy na obrazach. Gdy dodasz `?fit=smart` do dowolnego URL-a, region przycinania jest przesuwany, aby wycentrować wykryte twarze, zamiast używać centrum geometrycznego. Jeśli nie znaleziono twarzy, następuje powrót do standardowego centralnego przycinania.

### Czy mogę generować gradientowe obrazy placeholder bez przesyłania zdjęć?

Tak. Endpoint `/gradient/{width}/{height}/{from}/{to}` generuje obrazy gradientowe całkowicie z parametrów URL. Nie są wymagane przesłane obrazy. Możesz też tworzyć placeholdery SVG za pomocą `/svg/{width}/{height}`.

### Jak wygenerować obrazy placeholder o rozmiarze Instagram Story przez API?

Użyj endpointu preset: `/preset/instagram-story/{category}`. Zwraca obraz 1080x1920. Połącz z `?format=webp&quality=70` dla zoptymalizowanej dostawy i `?fit=smart` dla bezpiecznego przycinania portretowego.

### Czy PlacePix obsługuje pamięć masową zgodną z S3?

Tak. PlacePix działa z OVHcloud Object Storage, AWS S3, MinIO i każdym dostawcą zgodnym z S3. Skonfiguruj endpoint, bucket, klucz dostępu i klucz tajny za pomocą zmiennych środowiskowych.

### Jakie formaty wyjściowe są obsługiwane?

WebP, AVIF, JPEG, PNG, SVG i base64 JSON. Użyj `.webp`, `.avif` lub `.png` jako rozszerzenie pliku, lub dodaj `?format=webp` jako parametr zapytania. AVIF produkuje najmniejsze pliki; PNG jest bezstratny.

### Czy PlacePix jest darmowy do użytku komercyjnego?

Tak. PlacePix jest wydany na licencji MIT i jest darmowy zarówno do użytku osobistego, jak i komercyjnego. Ponieważ jest samodzielnie hostowany, nie ma limitów użytkowania, kluczy API ani płatności za żądanie.