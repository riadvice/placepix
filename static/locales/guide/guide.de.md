---
title: PlacePix Entwicklerhandbuch — Selbstgehostete Placeholder Image API und Funktionsreferenz
description: Vollständiges PlacePix Entwicklerhandbuch und API-Referenz. Erfahren Sie, wie Sie Placeholder-Bilder mit Docker bereitstellen, Gradienten und SVG generieren und Social-Media-Voreinstellungen für Instagram, YouTube und mehr verwenden.
keywords: selbstgehostete placeholder image API, face-aware crop placeholder, gradient placeholder generator, Docker placeholder image service, Instagram story placeholder API, SVG placeholder generator, developer image API
author: RIADVICE
robots: index, follow
og_title: PlacePix Entwicklerhandbuch — Selbstgehostete Placeholder-Image-API & Funktionsreferenz
og_description: Vollständiges Entwicklerhandbuch mit Docker-Bereitstellung, Smart Crop, Gradient-Placeholder, SVG-Generierung und Social-Media-Voreinstellungen.
twitter_title: PlacePix Entwicklerhandbuch — Selbstgehostete Placeholder-Image-API & Funktionsreferenz
twitter_description: Vollständiges Entwicklerhandbuch mit Docker-Bereitstellung, Smart Crop, Gradient-Placeholder, SVG-Generierung und Social-Media-Voreinstellungen.
jsonld_name: PlacePix Entwicklerhandbuch — Selbstgehostete Placeholder-Image-API & Funktionsreferenz
jsonld_description: Vollständiges Entwicklerhandbuch und API-Referenz für PlacePix, einen selbstgehosteten Placeholder-Bilderdienst. Deckt Docker-Bereitstellung, Face-Aware-Smart-Crop, Gradient-Placeholder, SVG-Generierung und Social-Media-Voreinstellungen ab.
jsonld_proficiency: Expert
jsonld_dependencies: Docker, Python 3.12, FastAPI
header_title: PlacePix Entwicklerhandbuch
header_subtitle: Vollständige API-Referenz und Funktionsdokumentation für den selbstgehosteten Placeholder-Bilderdienst. Deckt Docker-Bereitstellung, intelligentes Zuschneiden, Gradient-Placeholder, SVG-Generierung, Buchstaben-Avatare und Social-Media-Voreinstellungen ab.
author_label: Von
updated_label: "Zuletzt aktualisiert: Mai 2026"
github_label: Open Source auf GitHub
toc_title: Inhaltsverzeichnis
---

## Was ist PlacePix?

PlacePix ist ein **selbstgehosteter Placeholder-Bilderdienst**, der für Entwickler und Designteams entwickelt wurde. Im Gegensatz zu Drittanbieter-Placeholder-Diensten, die externe Netzwerkaufrufe erfordern und verschwinden können, läuft PlacePix vollständig auf Ihrer eigenen Infrastruktur. Legen Sie Bilder in Ordnern ab und erhalten Sie sofort URL-Endpunkte, die verkleinerte, gefilterte und formatierte Bilder ausliefern.

Der Dienst ist in Python mit FastAPI geschrieben und verwendet Pillow und OpenCV für die Bildverarbeitung. Er unterstützt Docker-Bereitstellung und S3-kompatiblen Objektspeicher.

### Funktionen

- **Zero Configuration** — Bilder in Ordnern ablegen und loslegen
- **Gesichterkennendes Zuschneiden** — OpenCV erkennt und zentriert Gesichter
- **Gradient- & SVG-Placeholder** — keine Bilder erforderlich
- **Social-Media-Voreinstellungen** — Instagram, YouTube, TikTok-Größen integriert
- **Farbensuche** — Bilder finden, die zu Ihrer Markenfarbpalette passen
- **Buchstaben-Avatare** — deterministische Profilbilder aus Namen

## Docker-Bereitstellungshandbuch

Der schnellste Weg, PlacePix auszuführen, ist mit Docker. Ein einzelner Befehl stellt den gesamten Dienst mit intelligentem Scannen, Farbextraktion und dem eingebetteten URL-Builder bereit.

### Einzeilen-Bereitstellung

```bash
docker run -d -p 3000:3000 \
  -v ./images:/app/images \
  riadvice/placepix:latest
```

### Docker Compose (Empfohlen)

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

### Persistente Daten und Umgebung

Binden Sie sowohl `/app/images` (Ihre Bildbibliothek) als auch `/app/data` (Scan-Cache und Metadaten) ein, um den Zustand über Container-Neustarts hinweg zu erhalten. Konfigurieren Sie das Verhalten über Umgebungsvariablen oder eine `.env`-Datei.

### OVHcloud S3-kompatibler Speicher

PlacePix unterstützt jedes S3-kompatible Backend. Für OVHcloud Object Storage setzen Sie:

```
S3_ENABLED=true
S3_ENDPOINT=https://s3.rbx.io.cloud.ovh.net
S3_ACCESS_KEY=ihr-key
S3_SECRET_KEY=ihr-secret
S3_BUCKET=ihr-bucket
S3_REGION=rbx
```

## Gesichterkennendes intelligentes Zuschneiden

Standardmäßiges Zentrum-Zuschneiden kann bei Porträtfotografien durch Gesichter schneiden. PlacePix löst dies mit **gesichterkennendem intelligentem Zuschneiden**, unterstützt durch OpenCV Haar-Kaskaden.

### Wie es funktioniert

Wenn eine Anfrage `?fit=smart` enthält, scannt PlacePix das Bild mit OpenCV auf menschliche Gesichter. Werden Gesichter erkannt, wird das Zuschneide-Fenster verschoben, sodass der Gesichtsschwerpunkt so nah wie möglich an den goldenen Schnitt-Schnittpunkten liegt. Werden keine Gesichter gefunden, greift es auf Standard-Zentrum-Zuschneiden zurück.

### API-Beispiele

```
# Gesichterkennendes Zuschneiden (erkennt und zentriert Gesichter)
/400/300/people?fit=smart

# Standard-Zentrum-Zuschneiden
/400/300/people?fit=crop

# Cover-Füllung (kann strecken)
/400/300/people?fit=cover

# Contain (Letterboxing)
/400/300/people?fit=contain
```

### Wann Smart Crop verwenden

- Porträtfotografie und Headshots
- Teamseiten, wo Gesichter wichtig sind
- Social-Media-Thumbnails
- Jedes Szenario, wo geometrisches Zentrum-Zuschneiden die Komposition ruiniert

## Gradient-Placeholder-API

Generieren Sie lineare und radiale Gradientenbilder on-the-fly, ohne Assets hochzuladen. Perfekt für Hero-Hintergründe, Ladezustände und Design-Mockups.

### Endpunkt-Syntax

```
/gradient/{width}/{height}/{from_hex}/{to_hex}
```

### Beispiele

```
# Einfacher linearer Gradient (oben nach unten)
/gradient/800/400/3b82f6/10b981

# 45-Grad-Winkel-Gradient
/gradient/800/400/e11d48/f59e0b?angle=45

# Radialer Gradient von der Mitte
/gradient/800/400/1e293b/64748b?gradient_type=radial

# Mit Ausgabeformat
/gradient/800/400/0ea5e9/ffffff?format=webp&quality=80
```

### Parameter-Referenz

- `{from_hex}` / `{to_hex}` — Hex-Farben ohne #-Präfix
- `?angle=45` — linearer Winkel in Grad (0-360)
- `?gradient_type=radial` — wechselt zu radialem Gradient
- `?format=webp` — WebP-Ausgabe (kleinere Dateigröße)

## SVG-Placeholder-Generator

SVG-Placeholder erfordern keine serverseitige Bildverarbeitung. Sie werden als Inline-SVG mit anpassbarer Hintergrundfarbe, Vordergrundfarbe und Textbeschriftung generiert.

### Endpunkt

```
/svg/{width}/{height}?bg={hex}&fg={hex}&text={label}
```

### Beispiele

```
# Standard Wireframe-Placeholder
/svg/400/300

# Benutzerdefinierte Markenfarben
/svg/400/300?bg=1c1917&fg=0ea5e9

# Mit benutzerdefiniertem Text
/svg/400/300?bg=0ea5e9&fg=ffffff&text=Hero+Section
```

### Warum SVG?

- Dateigröße unter 500 Bytes
- Unendlich skalierbar ohne Qualitätsverlust
- Keine Server-Verarbeitungs-Overhead
- Perfekt für Wireframes und Low-Fidelity-Prototypen

## Social-Media-Voreinstellungen

PlacePix enthält vordefinierte Abmessungen für beliebte Social-Media-Plattformen und Bildschirmgrößen. Verwenden Sie diese, um perfekt dimensionierte Placeholder-Bilder für Instagram, YouTube, TikTok, LinkedIn, X (Twitter) und Standard-Displays zu generieren.

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

### Bildschirmgrößen

```
/preset/mobile/nature              # 375x812
/preset/tablet/nature              # 768x1024
/preset/desktop/nature             # 1920x1080
/preset/4k/nature                  # 3840x2160
```

### Long-Tail-Anwendungsfall: Instagram Story API

Wenn Sie ein Social-Media-Management-Tool erstellen und **Instagram-Story-Größen-Placeholder-Bilder** benötigen, verwenden Sie `/preset/instagram-story/{category}`. Kombinieren Sie mit `?fit=smart` für Porträtfotos und `?format=webp&quality=70` für optimierte Auslieferung.

## Farbensuche-API

Jedes Bild in PlacePix wird auf seine 3 dominantesten Farben gescannt. Sie können die gesamte Bibliothek nach Hex-Farben durchsuchen, um Bilder zu finden, die zu Ihrer Markenfarbpalette passen.

### Endpunkte

```
# Bild mit bestimmter Hex-Farbe abrufen
/color/0ea5e9/400/300

# Beliebigen Endpunkt nach dominanter Farbe filtern
/400/300/nature?color=d97706

# Alle Bilder mit einer Farbe auflisten
/api/color/3b82f6
```

### Wie die Farbscanning funktioniert

Beim Start extrahiert PlacePix die häufigsten Farben aus jedem Bild mit k-Means-Clustering im LAB-Farbraum. Dies erzeugt wahrnehmungsgenaue Übereinstimmungen anstelle von reinen RGB-Durchschnitten. Die Palette-Seite (`/palette`) visualisiert diese Farben und lässt Sie nach Farbtonkategorien browsen.

## Ausrichtungsfilter

Filtern Sie zufällige Bilder nach ihrem nativen Seitenverhältnis vor der Auswahl. Das ist nützlich, wenn Sie Bilder benötigen, die natürlich in ein Layout passen — Landschaft für Header, Hochformat für Karten oder Quadrat für Vorschaubilder.

### Endpunkte

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

Die `squarish`-Toleranz ist über die Umgebungsvariable `ORIENTATION_SQUARISH_TOLERANCE` konfigurierbar (Standard: `0.15`). Ein Wert von `0.15` bedeutet, dass Bilder mit einem Seitenverhältnis zwischen `0.85` und `1.15` als quadratisch betrachtet werden. Setzen Sie `0.0` für exakt 1:1.

### Funktionsweise

PlacePix liest Bildabmessungen aus Datei-Headern während des initialen Scans (lokale Dateien) und während des Hintergrund-Metadaten-Scans (S3-Bilder). Die Abmessungen werden im Speicher gehalten und verwendet, um die Kandidatenliste vor der zufälligen oder deterministischen Auswahl zu filtern. Wenn keine passenden Bilder gefunden werden, wird ein `404` zurückgegeben.
## Filter und Effekte

Wenden Sie Echtzeit-Filter und Effekte auf beliebige Bilder über Abfrageparameter an. Die gesamte Verarbeitung erfolgt serverseitig und wird für nachfolgende Anfragen zwischengespeichert.

### Farbanpassungen

```
?grayscale=1               # Schwarz & Weiß
?sepia=1                   # Warmer Sepia-Ton
?tint=0ea5e9               # Hex-Farben-Overlay
?brightness=1.3            # 0,0 bis 2,0
?contrast=1.2              # 0,0 bis 2,0
?saturation=2.0            # 0,0 bis 2,0
?invert=true               # Farben invertieren
?posterize=4               # Farbstufen (1-8)
?duotone=ff0000,0000ff     # Zwei-Farben-Karte
```

### Bildeffekte

```
?blur=2                    # Gaußscher Weichzeichner (1-10)
?sharpen=1.5               # Schärfemenge
?emboss=true               # 3D-Relief
?edges=sobel               # Kantenerkennung
?edges=canny               # Canny-Kanten
?halftone=4                # Punktmuster
?oil_painting=true         # Ölgemälde-Stil
?pencil_sketch=true        # Bleistiftzeichnung
?cartoon=true              # Cartoon-Effekt
?vignette=0.5              # Kanten abdunkeln (0-1)
```

### Overlay-Parameter

```
?text=Hello+World          # Text-Overlay
?border=4,ffffff           # Rahmenbreite & -farbe
?watermark=1               # Konfiguriertes Wasserzeichen anwenden
?padding=20                # Interner Abstand
```

## Buchstaben-Avatar-Generator

Generieren Sie deterministische buchstabenbasierte Avatare aus beliebigen Namen oder E-Mails. Perfekt für Benutzerprofil-Placeholder, Kommentarsysteme und Teamverzeichnisse. Jeder Name erzeugt immer dieselbe Farbe, sodass Avatare über Sitzungen hinweg konsistent sind.

### Endpunkt

```
/avatar/{size}/{name}
/avatar/{size}/{name}.{ext}
```

### Parameter

- `size` — Pixelgröße (z.B. `64`, `128`, `256`)
- `name` — beliebige Zeichenkette; erste Buchstaben werden für den Avatar extrahiert
- `circle` — zu Kreisform zuschneiden
- `border={width},{color}` — Rahmen hinzufügen
- `bg={hex}` — Hintergrundfarbe überschreiben
- `fg={hex}` — Text-/Vordergrundfarbe überschreiben
- `single=true` — nur den ersten Buchstaben verwenden
- `uppercase=false` — Kleinbuchstaben beibehalten
- `palette={name}` — wählen aus `flatui`, `material`, `pastel` oder `neon`

### Beispiele

```
# Einfacher 128px-Avatar
/avatar/128/John+Doe

# Kreis-Avatar mit benutzerdefiniertem Rahmen
/avatar/128/John+Doe?circle=true&border=2,ffffff

# Einzelinitial, Pastell-Palette
/avatar/64/Alice?single=true&palette=pastel

# SVG-Ausgabe (skalierbar, unter 500 Bytes)
/avatar/128/John+Doe.svg
```

### Warum Buchstaben-Avatare verwenden?

- Null externe Abhängigkeiten — kein Gravatar oder Drittanbieter-Avatar-Dienst
- Deterministisch — derselbe Name erzeugt immer dieselbe Farbe
- SVG-Unterstützung — unendlich skalierbar, perfekt für HiDPI-Displays
- Vier integrierte Farbpaletten für jede Markenästhetik

## REST API-Kurzreferenz

Alle Endpunkte unterstützen CORS und geben Bilder mit Langzeit-Cache-Headern zurück. Base64-JSON-Ausgabe ist für kleine Thumbnails verfügbar.

### Bild-Endpunkte

- `GET /{width}/{height}/{category}` — Zufälliges Bild aus Kategorie
- `GET /{width}/{height}` — Zufälliges Bild aus allen Kategorien
- `GET /id/{id}/{width}/{height}` — Bestimmtes Bild nach ID
- `GET /ratio/{ratio}/{width}/{category}` — Bild mit Seitenverhältnis
- `GET /preset/{preset}/{category}` — Social-Media-Voreinstellung
- `GET /color/{hex}/{width}/{height}` — Farbabgestimmtes Bild
- `GET /gradient/{w}/{h}/{from}/{to}` — Gradientenbild
- `GET /svg/{width}/{height}` — SVG-Placeholder
- `GET /avatar/{size}/{name}` — Buchstaben-Avatar (PNG/SVG)

### Metadaten-Endpunkte

- `GET /api/images` — Kategorien und Summen auflisten
- `GET /api/info/id/{id}` — Bildmetadaten (Abmessungen, Farben, Format)
- `GET /api/color/{hex}` — Bilder mit einer Farbe

### Health-Endpunkte

- `GET /health` — Liveness-Probe (Docker/K8s)
- `GET /ready` — Readiness-Probe (503 bis Bilder geladen)

## Fachwissen und Referenzen

- Aktive Mitwirkende am Open-Source-Ökosystem seit 2008
- Der gesamte Code ist Open Source unter der MIT-Lizenz und auf <a href="https://github.com/riadvice/placepix" target="_blank" class="text-accent hover:underline">GitHub</a> überprüfbar

## Häufig gestellte Fragen

### Wie stelle ich PlacePix mit Docker bereit?

Führen Sie `docker run -d -p 3000:3000 -v ./images:/app/images riadvice/placepix:latest` aus. Binden Sie Ihren Bildordner ein und der Dienst startet sofort mit aktiviertem intelligentem Scannen.

### Was ist gesichterkennendes intelligentes Zuschneiden?

PlacePix verwendet OpenCV Haar-Kaskaden, um Gesichter in Bildern zu erkennen. Wenn Sie `?fit=smart` zu einer beliebigen URL hinzufügen, wird der Zuschneidebereich verschoben, um auf erkannte Gesichter zu zentrieren, anstatt das geometrische Zentrum zu verwenden. Wird kein Gesicht gefunden, greift es auf Standard-Zentrum-Zuschneiden zurück.

### Kann ich Gradient-Placeholder-Bilder ohne Hochladen von Fotos generieren?

Ja. Der Endpunkt `/gradient/{width}/{height}/{from}/{to}` generiert Gradientenbilder vollständig aus URL-Parametern. Es sind keine hochgeladenen Bilder erforderlich. Sie können auch SVG-Placeholder mit `/svg/{width}/{height}` erstellen.

### Wie generiere ich Instagram-Story-Größen-Placeholder-Bilder über die API?

Verwenden Sie den Preset-Endpunkt: `/preset/instagram-story/{category}`. Dies gibt ein 1080x1920-Bild zurück. Kombinieren Sie mit `?format=webp&quality=70` für optimierte Auslieferung und `?fit=smart` für porträtsicheres Zuschneiden.

### Unterstützt PlacePix S3-kompatiblen Objektspeicher?

Ja. PlacePix funktioniert mit OVHcloud Object Storage, AWS S3, MinIO und jedem S3-kompatiblen Anbieter. Konfigurieren Sie Endpunkt, Bucket, Access Key und Secret Key über Umgebungsvariablen.

### Welche Ausgabeformate werden unterstützt?

WebP, AVIF, JPEG, PNG, SVG und Base64-JSON. Verwenden Sie `.webp`, `.avif` oder `.png` als Dateierweiterung oder fügen Sie `?format=webp` als Abfrageparameter hinzu. AVIF erzeugt die kleinsten Dateien; PNG ist verlustfrei.

### Ist PlacePix für kommerzielle Nutzung kostenlos?

Ja. PlacePix wird unter der MIT-Lizenz veröffentlicht und ist sowohl für persönliche als auch für kommerzielle Nutzung kostenlos. Da es selbstgehostet ist, gibt es keine Nutzungslimits, keine API-Schlüssel und keine Abrechnung pro Anfrage.
