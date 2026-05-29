---
title: Panduan Pembangun PlacePix — API Imej Placeholder yang Dihos Sendiri dan Rujukan Ciri-ciri
description: Panduan pembangun PlacePix yang lengkap dan rujukan API. Belajar cara menyebarkan imej placeholder dengan Docker, menjana gradien dan SVG, dan menggunakan preset media sosial untuk Instagram, YouTube, dan banyak lagi.
keywords: API imej placeholder self-hosted, crop pintar dengan pengesanan muka, penjana placeholder gradien, perkhidmatan imej placeholder Docker, API placeholder cerita Instagram, penjana placeholder SVG, API imej pembangun
author: RIADVICE
robots: index, follow
og_title: PlacePix Developer Guide — Self-Hosted Placeholder Image API & Feature Reference
og_description: Panduan pembangun lengkap yang merangkumi penyebaran Docker, crop pintar, placeholder gradien, penjanaan SVG, dan preset media sosial.
twitter_title: PlacePix Developer Guide — Self-Hosted Placeholder Image API & Feature Reference
twitter_description: Panduan pembangun lengkap yang merangkumi penyebaran Docker, crop pintar, placeholder gradien, penjanaan SVG, dan preset media sosial.
jsonld_name: PlacePix Developer Guide — Self-Hosted Placeholder Image API & Feature Reference
jsonld_description: Panduan pembangun lengkap dan rujukan API untuk PlacePix, perkhidmatan imej placeholder self-hosted. Merangkumi penyebaran Docker, crop pintar dengan pengesanan muka, placeholder gradien, penjanaan SVG, dan preset media sosial.
jsonld_proficiency: Expert
jsonld_dependencies: Docker, Python 3.12, FastAPI
header_title: Panduan Pembangun PlacePix
header_subtitle: Rujukan API lengkap dan dokumentasi ciri untuk perkhidmatan imej placeholder yang dihos sendiri. Merangkumi penyebaran Docker, pemotongan pintar, placeholder gradien, penjanaan SVG, avatar huruf, dan preset media sosial.
author_label: Oleh
updated_label: "Last updated: May 2026"
github_label: Sumber Terbuka di GitHub
toc_title: Kandungan
---

## Apakah PlacePix?

PlacePix adalah **perkhidmatan imej placeholder yang dihos sendiri** yang dibina untuk pembangun dan pasukan reka bentuk. Berbeza dengan perkhidmatan placeholder pihak ketiga yang memerlukan panggilan rangkaian luar dan mungkin hilang, PlacePix berjalan sepenuhnya pada infrastruktur anda sendiri. Letakkan imej ke folder, dan segera dapatkan endpoint URL yang menghidangkan imej yang diubah saiz, ditapis, dan diformat.

Perkhidmatan ini ditulis dalam Python menggunakan FastAPI dengan pemprosesan imej yang dikuasai oleh Pillow dan OpenCV. Ia menyokong penyebaran Docker, dan penyimpanan objek yang serasi dengan S3.

### Ciri-ciri

- **Konfigurasi sifar** — letakkan imej dalam folder dan pergi
- **Pemotongan sedar wajah** — OpenCV mengesan dan memusatkan wajah
- **Placeholder gradien & SVG** — tiada imej diperlukan
- **Preset media sosial** — saiz Instagram, YouTube, TikTok built-in
- **Carian warna** — cari imej yang sepadan dengan palet jenama anda
- **Avatar huruf** — imej profil deterministik dari nama

## Panduan Penyebaran Docker

Cara terpantas untuk menjalankan PlacePix adalah dengan Docker. Satu perintah menyebarkan keseluruhan perkhidmatan dengan pengimbasan pintar, pengekstrakan warna, dan pembina URL yang tertanam.

### Penyebaran Satu Baris

```bash
docker run -d -p 3000:3000 \
  -v ./images:/app/images \
  riadvice/placepix:latest
```

### Docker Compose (Disyorkan)

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

### Data Kekal & Persekitaran

Mount kedua-dua `/app/images` (pustaka imej anda) dan `/app/data` (cache imbasan dan metadata) untuk mengekalkan keadaan merentas semula hidup kontena. Konfigurasikan tingkah laku melalui pemboleh ubah persekitaran atau fail `.env`.

### Storan Serasi S3 OVHcloud

PlacePix menyokong mana-mana backend yang serasi dengan S3. Untuk OVHcloud Object Storage, tetapkan:

```
S3_ENABLED=true
S3_ENDPOINT=https://s3.rbx.io.cloud.ovh.net
S3_ACCESS_KEY=your-key
S3_SECRET_KEY=your-secret
S3_BUCKET=your-bucket
S3_REGION=rbx
```

## Pemotongan Pintar yang Mengenali Muka

Pemotongan tengah piawai boleh mengiris wajah dalam fotografi potret. PlacePix menyelesaikan masalah ini dengan **pemotongan pintar yang mengenali muka** yang dikuasai oleh kaskad Haar OpenCV.

### Bagaimana Ia Berfungsi

Apabila permintaan termasuk `?fit=smart`, PlacePix mengimbas imej untuk wajah manusia menggunakan OpenCV. Jika wajah dikesan, tetingkap pemotongan digeser supaya centroid wajah terletak sedekat mungkin dengan titik persilangan nisbah emas. Jika tiada wajah ditemui, ia kembali kepada pemotongan tengah piawai.

### Contoh API

```
# Potongan sedar muka (mengesan dan memusatkan wajah)
/400/300/people?fit=smart

# Potongan tengah piawai
/400/300/people?fit=crop

# Isian cover (mungkin meregang)
/400/300/people?fit=cover

# Mengandungi (letterboxing)
/400/300/people?fit=contain
```

### Bila Guna Smart Crop

- Fotografi potret dan headshot
- Halaman pasukan di mana wajah penting
- Thumbnail media sosial
- Mana-mana senario di mana pemotongan tengah geometri merosakkan komposisi

## API Placeholder Gradien

Hasilkan imej gradient linear dan radial on-the-fly tanpa memuat naik sebarang aset. Sesuai untuk latar belakang hero, keadaan pemuatan, dan mockup reka bentuk.

### Sintaks Endpoint

```
/gradient/{width}/{height}/{from_hex}/{to_hex}
```

### Contoh

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

### Rujukan Parameter

- `{from_hex}` / `{to_hex}` — warna hex tanpa awalan #
- `?angle=45` — sudut linear dalam darjah (0-360)
- `?gradient_type=radial` — switches to radial gradient
- `?format=webp` — WebP output (smaller file size)

## Penjana Placeholder SVG

SVG placeholder tidak memerlukan pemprosesan imej server-side. Dihasilkan sebagai inline SVG dengan warna latar belakang, warna latar depan, dan label teks yang boleh disesuaikan.

### Endpoint

```
/svg/{width}/{height}?bg={hex}&fg={hex}&text={label}
```

### Contoh

```
# Default wireframe placeholder
/svg/400/300

# Custom brand colors
/svg/400/300?bg=1c1917&fg=0ea5e9

# With custom text
/svg/400/300?bg=0ea5e9&fg=ffffff&text=Hero+Section
```

### Mengapa SVG?

- Saiz fail di bawah 500 bait
- Infinitely scalable tanpa kehilangan kualiti
- Zero server processing overhead
- Sempurna untuk wireframe dan prototip low-fidelity

## Preset Media Sosial

PlacePix merangkumi dimensi yang telah ditentukan untuk platform sosial popular dan saiz skrin. Gunakannya untuk menghasilkan imej placeholder dengan saiz sempurna untuk Instagram, YouTube, TikTok, LinkedIn, X (Twitter), dan paparan standard.

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

### Saiz Skrin

```
/preset/mobile/nature              # 375x812
/preset/tablet/nature              # 768x1024
/preset/desktop/nature             # 1920x1080
/preset/4k/nature                  # 3840x2160
```

### Kes Penggunaan Long-Tail: Instagram Story API

Jika anda membina alat pengurusan media sosial dan memerlukan **imej placeholder saiz Instagram story**, gunakan `/preset/instagram-story/{category}`. Gabungkan dengan `?fit=smart` untuk foto potret dan `?format=webp&quality=70` untuk penghantaran yang dioptimumkan.


## Penapisan Orientasi

Tapis imej rawak mengikut nisbah aspek asli mereka sebelum pemilihan. Ini berguna apabila anda memerlukan imej yang semula jadi sesuai dengan susun atur — landskap untuk pengepala, potret untuk kad, atau segi empat sama untuk imej kecil.

### Titik Akhir

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

### Konfigurasi

Toleransi `squarish` boleh dikonfigurasi melalui pembolehubah persekitaran `ORIENTATION_SQUARISH_TOLERANCE` (lalai: `0.15`). Nilai `0.15` bermaksud imej dengan nisbah aspek antara `0.85` dan `1.15` dianggap segi empat sama. Tetapkan kepada `0.0` untuk 1:1 tepat.

### Cara Ia Berfungsi

PlacePix membaca dimensi imej daripada pengepala fail semasa imbasan awal (fail tempatan) dan semasa imbasan metadata latar belakang (imej S3). Dimensi disimpan dalam memori dan digunakan untuk menapis kumpulan calon sebelum pemilihan rawak atau benih. Jika orientasi diminta tetapi tiada imej yang sepadan, `404` dikembalikan.

## API Carian Warna

Setiap imej dalam PlacePix diimbas untuk 3 warna dominan teratas. Anda boleh mencari keseluruhan pustaka mengikut warna hex untuk mencari imej yang sepadan dengan palet jenama anda.

### Endpoints

```
# Dapatkan imej yang sepadan dengan warna hex tertentu
/color/0ea5e9/400/300

# Tapis mana-mana endpoint mengikut warna dominan
/400/300/nature?color=d97706

# Senarai semua imej yang sepadan dengan warna
/api/color/3b82f6
```

### Bagaimana Pengimbasan Warna Berfungsi

Semasa permulaan, PlacePix mengekstrak warna yang paling kerap dari setiap imej menggunakan pengelompokan k-means dalam ruang warna LAB. Ini menghasilkan padanan yang tepat secara perceptual berbanding purata RGB mentah. Halaman palet (`/palette`) mengvisualisasikan warna-warna ini dan membolehkan anda melayar mengikut kategori warna.

## Penapis & Kesan

Gunakan penapis dan kesan real-time ke mana-mana imej melalui parameter pertanyaan. Semua pemprosesan dilakukan di pihak server dan di-cache untuk permintaan seterusnya.

### Penyesuaian Warna

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

### Kesan Imej

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

### Parameter Overlay

```
?text=Hello+World          # Text overlay
?border=4,ffffff           # Border width & color
?watermark=1               # Apply configured watermark
?padding=20                # Internal padding
```

## Penjana Avatar Huruf

Jana avatar berdasarkan huruf yang deterministik dari mana-mana nama atau e-mel. Sempurna untuk placeholder profil pengguna, sistem komen, dan direktori pasukan. Setiap nama sentiasa menghasilkan warna yang sama, jadi avatar adalah konsisten merentasi sesi.

### Endpoint

```
/avatar/{size}/{name}
/avatar/{size}/{name}.{ext}
```

### Parameter

- `size` — pixel size (e.g. `64`, `128`, `256`)
- `name` — any string; first letters are extracted for the avatar
- `circle` — crop to a circle shape
- `border={width},{color}` — add a border
- `bg={hex}` — override background color
- `fg={hex}` — override text/foreground color
- `single=true` — use only the first letter
- `uppercase=false` — preserve lowercase letters
- `palette={name}` — choose from `flatui`, `material`, `pastel`, or `neon`

### Contoh

```
# Avatar 128px ringkas
/avatar/128/John+Doe

# Avatar bulatan dengan border tersuai
/avatar/128/John+Doe?circle=true&border=2,ffffff

# Singkatan tunggal, palet pastel
/avatar/64/Alice?single=true&palette=pastel

# Output SVG (boleh skala, di bawah 500 bait)
/avatar/128/John+Doe.svg
```

### Mengapa Guna Avatar Huruf?

- Zero external dependencies — no Gravatar or third-party avatar service
- Deterministic — the same name always produces the same color
- Sokongan SVG — infinitely scalable, sesuai untuk paparan HiDPI
- Empat palet warna built-in untuk mana-mana estetik jenama

## Rujukan Pantas REST API

Semua endpoint menyokong CORS dan mengembalikan imej dengan header cache jangka panjang. Output Base64 JSON tersedia untuk thumbnail kecil.

### Endpoint Imej

- `GET /{width}/{height}/{category}` — Random image from category
- `GET /{width}/{height}` — Random image from all categories
- `GET /id/{id}/{width}/{height}` — Specific image by ID
- `GET /ratio/{ratio}/{width}/{category}` — Aspect ratio image
- `GET /preset/{preset}/{category}` — Social media preset
- `GET /color/{hex}/{width}/{height}` — Color-matched image
- `GET /gradient/{w}/{h}/{from}/{to}` — Gradient image
- `GET /svg/{width}/{height}` — SVG placeholder
- `GET /avatar/{size}/{name}` — Letter avatar (PNG/SVG)

### Endpoint Metadata

- `GET /api/images` — List categories and totals
- `GET /api/info/id/{id}` — Image metadata (dimensions, colors, format)
- `GET /api/color/{hex}` — Images matching a color

### Endpoint Health

- `GET /health` — Liveness probe (Docker/K8s)
- `GET /ready` — Readiness probe (503 until images loaded)

## Kepakaran dan Kelayakan

- Active contributors to the open-source ecosystem since 2008
- All code is open source under the MIT License and auditable on <a href="https://github.com/riadvice/placepix" target="_blank" class="text-accent hover:underline">GitHub</a>

## Soalan Lazim

### Bagaimanakah saya menyebarkan PlacePix dengan Docker?

Run `docker run -d -p 3000:3000 -v ./images:/app/images riadvice/placepix:latest`. Mount your image folder and the service starts immediately with smart scanning enabled.

### Apakah pemotongan pintar yang mengenali muka?

PlacePix uses OpenCV Haar cascades to detect faces in images. When you add `?fit=smart` to any URL, the crop region is shifted to center on detected faces rather than using geometric center. If no face is found, it falls back to standard center cropping.

### Can I generate gradient placeholder images without uploading photos?

Yes. The `/gradient/{width}/{height}/{from}/{to}` endpoint generates gradient images entirely from URL parameters. No uploaded images are required. You can also create SVG placeholders with `/svg/{width}/{height}`.

### How do I generate Instagram story size placeholder images via API?

Use the preset endpoint: `/preset/instagram-story/{category}`. This returns a 1080x1920 image. Combine with `?format=webp&quality=70` for optimized delivery and `?fit=smart` for portrait-safe cropping.

### Adakah PlacePix menyokong storan objek S3-serasi?

Yes. PlacePix works with OVHcloud Object Storage, AWS S3, MinIO, and any S3-compatible provider. Configure endpoint, bucket, access key, and secret key via environment variables.

### Format output apa yang disokong?

WebP, AVIF, JPEG, PNG, SVG, and base64 JSON. Use `.webp`, `.avif`, or `.png` as the file extension, or add `?format=webp` as a query parameter. AVIF produces the smallest files; PNG is lossless.

### Adakah PlacePix percuma untuk kegunaan komersial?

Yes. PlacePix is released under the MIT License and is free for both personal and commercial use. Because it is self-hosted, there are no usage limits, no API keys, and no per-request billing.
