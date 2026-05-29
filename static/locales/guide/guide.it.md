---
title: Guida per Sviluppatori PlacePix — API di Immagini Placeholder Self-Hosted e Riferimento alle Funzionalità
description: Guida completa per sviluppatori PlacePix e riferimento API. Impara a distribuire immagini placeholder con Docker, generare gradienti e SVG, e utilizzare preset per social media per Instagram, YouTube e altro.
keywords: API immagini placeholder self-hosted, placeholder crop face-aware, generatore placeholder gradiente, servizio immagini placeholder Docker, API placeholder Instagram story, generatore placeholder SVG, API immagini sviluppatore
author: RIADVICE
robots: index, follow
og_title: Guida per Sviluppatori PlacePix — API di Immagini Placeholder Self-Hosted e Riferimento alle Funzionalità
og_description: Guida completa per sviluppatori che copre distribuzione con Docker, ritaglio intelligente, placeholder a gradiente, generazione SVG e preset per social media.
twitter_title: Guida per Sviluppatori PlacePix — API di Immagini Placeholder Self-Hosted e Riferimento alle Funzionalità
twitter_description: Guida completa per sviluppatori che copre distribuzione con Docker, ritaglio intelligente, placeholder a gradiente, generazione SVG e preset per social media.
jsonld_name: Guida per Sviluppatori PlacePix — API di Immagini Placeholder Self-Hosted e Riferimento alle Funzionalità
jsonld_description: Guida completa per sviluppatori e riferimento API per PlacePix, un servizio di immagini placeholder self-hosted. Copre distribuzione con Docker, ritaglio intelligente con riconoscimento facciale, placeholder a gradiente, generazione SVG e preset per social media.
jsonld_proficiency: Expert
jsonld_dependencies: Docker, Python 3.12, FastAPI
header_title: Guida per Sviluppatori PlacePix
header_subtitle: Riferimento API completo e documentazione delle funzionalità per il servizio di immagini placeholder self-hosted. Copre distribuzione con Docker, ritaglio intelligente, placeholder a gradiente, generazione SVG, avatar con lettere e preset per social media.
author_label: Di
updated_label: "Ultimo aggiornamento: maggio 2026"
github_label: Open Source su GitHub
toc_title: Indice
---

## Cos'è PlacePix?

PlacePix è un **servizio di immagini placeholder self-hosted** creato per sviluppatori e team di design. A differenza dei servizi di placeholder di terze parti che richiedono chiamate di rete esterne e potrebbero scomparire, PlacePix funziona interamente sulla tua infrastruttura. Inserisci immagini nelle cartelle e ottieni immediatamente endpoint URL che servono immagini ridimensionate, filtrate e formattate.

Il servizio è scritto in Python usando FastAPI con elaborazione delle immagini basata su Pillow e OpenCV. Supporta distribuzione con Docker e archiviazione oggetti compatibile con S3.

### Funzionalità

- **Configurazione zero** — inserisci immagini nelle cartelle e inizia
- **Ritaglio con riconoscimento facciale** — OpenCV rileva e centra i volti
- **Placeholder a gradiente e SVG** — nessuna immagine richiesta
- **Preset per social media** — dimensioni Instagram, YouTube, TikTok integrate
- **Ricerca per colore** — trova immagini che corrispondono alla tua palette del brand
- **Avatar con lettere** — immagini profilo deterministiche dai nomi

## Guida alla distribuzione Docker

Il modo più veloce per eseguire PlacePix è con Docker. Un singolo comando distribuisce l'intero servizio con scansione intelligente, estrazione colori e il generatore di URL incorporato.

### Deployment di una riga

```bash
docker run -d -p 3000:3000 \
  -v ./images:/app/images \
  riadvice/placepix:latest
```

### Docker Compose (Consigliato)

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

### Dati persistenti e ambiente

Monta sia `/app/images` (la tua libreria di immagini) che `/app/data` (cache di scansione e metadati) per preservare lo stato tra i riavvii del container. Configura il comportamento tramite variabili d'ambiente o un file `.env`.

### Archiviazione compatibile S3 OVHcloud

PlacePix supporta qualsiasi backend compatibile S3. Per OVHcloud Object Storage, imposta:

```
S3_ENABLED=true
S3_ENDPOINT=https://s3.rbx.io.cloud.ovh.net
S3_ACCESS_KEY=your-key
S3_SECRET_KEY=your-secret
S3_BUCKET=your-bucket
S3_REGION=rbx
```

## Ritaglio intelligente con riconoscimento facciale

Il ritaglio centrale standard può tagliare i volti nella fotografia di ritratto. PlacePix risolve questo con **ritaglio intelligente con riconoscimento facciale** basato sulle cascate Haar di OpenCV.

### Come funziona

Quando una richiesta include `?fit=smart`, PlacePix scansiona l'immagine per volti umani usando OpenCV. Se vengono rilevati volti, la finestra di ritaglio viene spostata in modo che il centroide del volto sia il più possibile vicino ai punti di intersezione della sezione aurea. Se non vengono trovati volti, torna al ritaglio centrale standard.

### Esempi API

```
# Ritaglio con riconoscimento facciale (rileva e centra i volti)
/400/300/people?fit=smart

# Ritaglio centrale standard
/400/300/people?fit=crop

# Riempimento copertura (può stirare)
/400/300/people?fit=cover

# Contenimento (letterboxing)
/400/300/people?fit=contain
```

### Quando usare il ritaglio intelligente

- Fotografia di ritratto e primi piani
- Pagine del team dove i volti sono importanti
- Miniature per social media
- Qualsiasi scenario dove il ritaglio geometrico centrale rovina la composizione

## API placeholder a gradiente

Genera immagini a gradiente lineare e radiale al volo senza caricare alcuna risorsa. Perfetto per sfondi hero, stati di caricamento e mockup di design.

### Sintassi dell'endpoint

```
/gradient/{width}/{height}/{from_hex}/{to_hex}
```

### Esempi

```
# Gradiente lineare semplice (dall'alto verso il basso)
/gradient/800/400/3b82f6/10b981

# Gradiente angolato a 45 gradi
/gradient/800/400/e11d48/f59e0b?angle=45

# Gradiente radiale dal centro
/gradient/800/400/1e293b/64748b?gradient_type=radial

# Con formato di output
/gradient/800/400/0ea5e9/ffffff?format=webp&quality=80
```

### Riferimento parametri

- `{from_hex}` / `{to_hex}` — colori hex senza il prefisso #
- `?angle=45` — angolo lineare in gradi (0-360)
- `?gradient_type=radial` — passa a gradiente radiale
- `?format=webp` — output WebP (dimensione file minore)

## Generatore di placeholder SVG

I placeholder SVG non richiedono elaborazione delle immagini lato server. Vengono generati come SVG inline con colore di sfondo personalizzabile, colore di primo piano ed etichetta di testo.

### Endpoint

```
/svg/{width}/{height}?bg={hex}&fg={hex}&text={label}
```

### Esempi

```
# Placeholder wireframe predefinito
/svg/400/300

# Colori del brand personalizzati
/svg/400/300?bg=1c1917&fg=0ea5e9

# Con testo personalizzato
/svg/400/300?bg=0ea5e9&fg=ffffff&text=Hero+Section
```

### Perché SVG?

- Dimensione file inferiore a 500 byte
- Infinitamente scalabile senza perdita di qualità
- Zero overhead di elaborazione server
- Perfetto per wireframe e prototipi a bassa fedeltà

## Preset per social media

PlacePix include dimensioni predefinite per piattaforme social popolari e dimensioni dello schermo. Usale per generare immagini placeholder perfettamente dimensionate per Instagram, YouTube, TikTok, LinkedIn, X (Twitter) e display standard.

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

### Dimensioni Schermo

```
/preset/mobile/nature              # 375x812
/preset/tablet/nature              # 768x1024
/preset/desktop/nature             # 1920x1080
/preset/4k/nature                  # 3840x2160
```

### Caso d'uso Long-Tail: API Instagram Story

Se stai creando uno strumento di gestione dei social media e hai bisogno di **immagini placeholder delle dimensioni delle storie Instagram**, usa `/preset/instagram-story/{category}`. Combina con `?fit=smart` per foto di ritratto e `?format=webp&quality=70` per una consegna ottimizzata.


## Filtraggio per orientamento

Filtra le immagini casuali in base al loro rapporto d'aspetto nativo prima della selezione. Questo è utile quando hai bisogno di immagini che si integrano naturalmente in un layout — paesaggio per le intestazioni, ritratto per le schede o quadrato per le miniature.

### Endpoint

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

### Configurazione

La tolleranza `squarish` è configurabile tramite la variabile d'ambiente `ORIENTATION_SQUARISH_TOLERANCE` (default: `0.15`). Un valore di `0.15` significa che le immagini con un rapporto d'aspetto tra `0.85` e `1.15` sono considerate quadrate. Imposta su `0.0` per un rapporto esatto di 1:1.

### Funzionamento

PlacePix legge le dimensioni delle immagini dalle intestazioni dei file durante la scansione iniziale (file locali) e durante la scansione dei metadati in background (immagini S3). Le dimensioni sono memorizzate in memoria e utilizzate per filtrare il pool di candidati prima della selezione casuale o deterministica. Se viene richiesta un'orientazione ma nessuna immagine corrisponde, viene restituito un `404`.
## Filtri ed effetti

Applica filtri ed effetti in tempo reale a qualsiasi immagine tramite parametri di query. Tutta l'elaborazione viene eseguita lato server e messa in cache per le richieste successive.

### Regolazioni colore

```
?grayscale=1               # Bianco e nero
?sepia=1                   # Tono seppia caldo
?tint=0ea5e9               # Sovrapposizione colore hex
?brightness=1.3            # 0,0 a 2,0
?contrast=1.2              # 0,0 a 2,0
?saturation=2.0            # 0,0 a 2,0
?invert=true               # Inverti colori
?posterize=4               # Livelli colore (1-8)
?duotone=ff0000,0000ff     # Mappa due colori
```

### Effetti immagine

```
?blur=2                    # Sfocatura gaussiana (1-10)
?sharpen=1.5               # Quantità nitidezza
?emboss=true               # Rilievo 3D
?edges=sobel               # Rilevamento bordi
?edges=canny               # Bordi Canny
?halftone=4                # Pattern punti
?oil_painting=true         # Stile pittura ad olio
?pencil_sketch=true        # Schizzo a matita
?cartoon=true              # Effetto cartone animato
?vignette=0.5              # Scurisci bordi (0-1)
```

### Parametri sovrapposizione

```
?text=Hello+World          # Sovrapposizione testo
?border=4,ffffff           # Larghezza e colore bordo
?watermark=1               # Applica filigrana configurata
?padding=20                # Padding interno
```

## Generatore di avatar con lettere

Genera avatar deterministici basati su lettere da qualsiasi nome o email. Perfetto per placeholder profilo utente, sistemi di commenti e directory del team. Ogni nome produce sempre lo stesso colore, quindi gli avatar sono coerenti tra le sessioni.

### Endpoint

```
/avatar/{size}/{name}
/avatar/{size}/{name}.{ext}
```

### Parametri

- `size` — dimensione in pixel (es. `64`, `128`, `256`)
- `name` — qualsiasi stringa; le prime lettere sono estratte per l'avatar
- `circle` — ritaglia a forma di cerchio
- `border={width},{color}` — aggiungi un bordo
- `bg={hex}` — sovrascrivi colore di sfondo
- `fg={hex}` — sovrascrivi colore testo/primo piano
- `single=true` — usa solo la prima lettera
- `uppercase=false` — conserva lettere minuscole
- `palette={name}` — scegli tra `flatui`, `material`, `pastel` o `neon`

### Esempi

```
# Avatar semplice 128px
/avatar/128/John+Doe

# Avatar circolare con bordo personalizzato
/avatar/128/John+Doe?circle=true&border=2,ffffff

# Iniziale singola, palette pastello
/avatar/64/Alice?single=true&palette=pastel

# Output SVG (scalabile, meno di 500 byte)
/avatar/128/John+Doe.svg
```

### Perché usare avatar con lettere?

- Zero dipendenze esterne — nessun Gravatar o servizio avatar di terze parti
- Deterministico — lo stesso nome produce sempre lo stesso colore
- Supporto SVG — infinitamente scalabile, perfetto per display HiDPI
- Quattro palette colori integrate per qualsiasi estetica del brand

## Riferimento rapido API REST

Tutti gli endpoint supportano CORS e restituiscono immagini con header di cache a lungo termine. L'output JSON Base64 è disponibile per miniature piccole.

### Image Endpoints

- `GET /{width}/{height}/{category}` — Immagine casuale dalla categoria
- `GET /{width}/{height}` — Immagine casuale da tutte le categorie
- `GET /id/{id}/{width}/{height}` — Immagine specifica per ID
- `GET /ratio/{ratio}/{width}/{category}` — Immagine con proporzioni
- `GET /preset/{preset}/{category}` — Preset social media
- `GET /color/{hex}/{width}/{height}` — Immagine con colore corrispondente
- `GET /gradient/{w}/{h}/{from}/{to}` — Immagine gradiente
- `GET /svg/{width}/{height}` — Placeholder SVG
- `GET /avatar/{size}/{name}` — Avatar con lettere (PNG/SVG)

### Endpoint metadati

- `GET /api/images` — Elenca categorie e totali
- `GET /api/info/id/{id}` — Metadati immagine (dimensioni, colori, formato)
- `GET /api/color/{hex}` — Immagini che corrispondono a un colore

### Endpoint salute

- `GET /health` — Sonda di vitalità (Docker/K8s)
- `GET /ready` — Sonda di prontezza (503 finché le immagini non sono caricate)

## Competenza e credenziali

- Collaboratori attivi all'ecosistema open source dal 2008
- Tutto il codice è open source sotto licenza MIT e verificabile su <a href="https://github.com/riadvice/placepix" target="_blank" class="text-accent hover:underline">GitHub</a>

## Domande frequenti

### Come distribuisco PlacePix con Docker?

Esegui `docker run -d -p 3000:3000 -v ./images:/app/images riadvice/placepix:latest`. Monta la tua cartella immagini e il servizio si avvia immediatamente con la scansione intelligente abilitata.

### Cos'è il ritaglio intelligente con riconoscimento facciale?

PlacePix usa le cascate Haar di OpenCV per rilevare volti nelle immagini. Quando aggiungi `?fit=smart` a qualsiasi URL, la regione di ritaglio viene spostata per centrare sui volti rilevati piuttosto che usare il centro geometrico. Se nessun volto viene trovato, torna al ritaglio centrale standard.

### Posso generare immagini placeholder a gradiente senza caricare foto?

Sì. L'endpoint `/gradient/{width}/{height}/{from}/{to}` genera immagini a gradiente interamente dai parametri URL. Non sono richieste immagini caricate. Puoi anche creare placeholder SVG con `/svg/{width}/{height}`.

### Come genero immagini placeholder delle dimensioni delle storie Instagram via API?

Usa l'endpoint preset: `/preset/instagram-story/{category}`. Questo restituisce un'immagine 1080x1920. Combina con `?format=webp&quality=70` per una consegna ottimizzata e `?fit=smart` per un ritaglio sicuro per i ritratti.

### PlacePix supporta l'archiviazione di oggetti compatibile S3?

Sì. PlacePix funziona con OVHcloud Object Storage, AWS S3, MinIO e qualsiasi provider compatibile S3. Configura endpoint, bucket, chiave di accesso e chiave segreta tramite variabili d'ambiente.

### Quali formati di output sono supportati?

WebP, AVIF, JPEG, PNG, SVG e JSON base64. Usa `.webp`, `.avif` o `.png` come estensione del file, o aggiungi `?format=webp` come parametro di query. AVIF produce i file più piccoli; PNG è senza perdita.

### PlacePix è gratuito per uso commerciale?

Sì. PlacePix è rilasciato sotto licenza MIT ed è gratuito sia per uso personale che commerciale. Essendo self-hosted, non ci sono limiti di utilizzo, chiavi API né fatturazione per richiesta.
