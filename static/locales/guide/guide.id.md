---
title: Panduan Pengembang PlacePix — API Gambar Placeholder yang Di-host Sendiri dan Referensi Fitur
description: Panduan lengkap pengembang PlacePix dan referensi API. Pelajari cara menjalankan gambar placeholder dengan Docker, menghasilkan gradien dan SVG, dan menggunakan preset media sosial untuk Instagram, YouTube, dan lainnya.
keywords: API gambar placeholder self-hosted, crop pintar dengan deteksi wajah, generator placeholder gradien, layanan gambar placeholder Docker, API placeholder cerita Instagram, generator placeholder SVG, API gambar pengembang
author: RIADVICE
robots: index, follow
og_title: PlacePix Developer Guide — Self-Hosted Placeholder Image API & Feature Reference
og_description: Panduan pengembang lengkap yang mencakup deployment Docker, crop pintar, placeholder gradien, pembuatan SVG, dan preset media sosial.
twitter_title: PlacePix Developer Guide — Self-Hosted Placeholder Image API & Feature Reference
twitter_description: Panduan pengembang lengkap yang mencakup deployment Docker, crop pintar, placeholder gradien, pembuatan SVG, dan preset media sosial.
jsonld_name: PlacePix Developer Guide — Self-Hosted Placeholder Image API & Feature Reference
jsonld_description: Panduan pengembang lengkap dan referensi API untuk PlacePix, layanan gambar placeholder self-hosted. Mencakup deployment Docker, crop pintar dengan deteksi wajah, placeholder gradien, pembuatan SVG, dan preset media sosial.
jsonld_proficiency: Expert
jsonld_dependencies: Docker, Python 3.12, FastAPI
header_title: Panduan Pengembang PlacePix
header_subtitle: Referensi API lengkap dan dokumentasi fitur untuk layanan gambar placeholder yang dihost sendiri. Meliputi deployment Docker, pemotongan pintar, placeholder gradien, pembuatan SVG, avatar huruf, dan preset media sosial.
author_label: Oleh
updated_label: "Last updated: May 2026"
github_label: Sumber Terbuka di GitHub
toc_title: Daftar Isi
---

## Apa itu PlacePix?

PlacePix adalah **layanan gambar placeholder yang dihost sendiri** yang dibuat untuk pengembang dan tim desain. Berbeda dengan layanan placeholder pihak ketiga yang memerlukan panggilan jaringan eksternal dan mungkin menghilang, PlacePix berjalan seluruhnya pada infrastruktur Anda sendiri. Letakkan gambar ke folder, dan langsung dapatkan endpoint URL yang menyajikan gambar yang diubah ukurannya, difilter, dan diformat.

Layanan ini ditulis dalam Python menggunakan FastAPI dengan pemrosesan gambar yang didukung oleh Pillow dan OpenCV. Ini mendukung deployment Docker, dan penyimpanan objek yang kompatibel dengan S3.

### Fitur

- **Konfigurasi nol** — letakkan gambar di folder dan jalankan
- **Pemotongan sadar wajah** — OpenCV mendeteksi dan memusatkan wajah
- **Placeholder gradien & SVG** — tidak memerlukan gambar
- **Preset media sosial** — ukuran Instagram, YouTube, TikTok built-in
- **Pencarian warna** — temukan gambar yang cocok dengan palet merek Anda
- **Avatar huruf** — gambar profil deterministik dari nama

## Panduan Deployment Docker

Cara tercepat untuk menjalankan PlacePix adalah dengan Docker. Satu perintah mendeploy seluruh layanan dengan pemindaian pintar, ekstraksi warna, dan URL builder yang tertanam.

### Deployment Satu Baris

```bash
docker run -d -p 3000:3000 \
  -v ./images:/app/images \
  riadvice/placepix:latest
```

### Docker Compose (Direkomendasikan)

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

### Data Persisten & Lingkungan

Mount baik `/app/images` (perpustakaan gambar Anda) dan `/app/data` (cache pemindaian dan metadata) untuk mempertahankan status di seluruh restart container. Konfigurasikan perilaku melalui variabel lingkungan atau file `.env`.

### Penyimpanan S3-Kompatibel OVHcloud

PlacePix mendukung backend yang kompatibel dengan S3 apa pun. Untuk OVHcloud Object Storage, atur:

```
S3_ENABLED=true
S3_ENDPOINT=https://s3.rbx.io.cloud.ovh.net
S3_ACCESS_KEY=your-key
S3_SECRET_KEY=your-secret
S3_BUCKET=your-bucket
S3_REGION=rbx
```

## Pemotongan Pintar yang Sadar Wajah

Pemotongan tengah standar dapat memotong wajah dalam fotografi potret. PlacePix memecahkan masalah ini dengan **pemotongan pintar yang sadar wajah** yang didukung oleh kaskad Haar OpenCV.

### Cara Kerjanya

Ketika permintaan mencakup `?fit=smart`, PlacePix memindai gambar untuk wajah manusia menggunakan OpenCV. Jika wajah terdeteksi, jendela pemotongan digeser sehingga centroid wajah terletak sedekat mungkin dengan titik perpotongan rasio emas. Jika tidak ada wajah yang ditemukan, ia kembali ke pemotongan tengah standar.

### Contoh API

```
# Pemotongan sadar wajah (mendeteksi dan memusatkan wajah)
/400/300/people?fit=smart

# Pemotongan tengah standar
/400/300/people?fit=crop

# Isian cover (mungkin meregang)
/400/300/people?fit=cover

# Berisi (letterboxing)
/400/300/people?fit=contain
```

### Kapan Menggunakan Smart Crop

- Fotografi potret dan headshot
- Halaman tim di mana wajah penting
- Thumbnail media sosial
- Skenario apa pun di mana pemotongan tengah geometris merusak komposisi

## API Placeholder Gradien

Hasilkan gambar gradient linear dan radial secara langsung tanpa mengunggah aset apa pun. Sempurna untuk latar belakang hero, status pemuatan, dan mockup desain.

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

### Referensi Parameter

- `{from_hex}` / `{to_hex}` — warna hex tanpa awalan #
- `?angle=45` — sudut linear dalam derajat (0-360)
- `?gradient_type=radial` — switches to radial gradient
- `?format=webp` — WebP output (smaller file size)

## Pembuat Placeholder SVG

SVG placeholder tidak memerlukan pemrosesan gambar server-side. Dihasilkan sebagai inline SVG dengan warna latar belakang, warna latar depan, dan label teks yang dapat disesuaikan.

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

- Ukuran file di bawah 500 byte
- Infinitely scalable tanpa kehilangan kualitas
- Zero server processing overhead
- Sempurna untuk wireframe dan prototipe low-fidelity

## Preset Media Sosial

PlacePix menyertakan dimensi yang telah ditentukan sebelumnya untuk platform sosial populer dan ukuran layar. Gunakan ini untuk menghasilkan gambar placeholder dengan ukuran sempurna untuk Instagram, YouTube, TikTok, LinkedIn, X (Twitter), dan tampilan standar.

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

### Ukuran Layar

```
/preset/mobile/nature              # 375x812
/preset/tablet/nature              # 768x1024
/preset/desktop/nature             # 1920x1080
/preset/4k/nature                  # 3840x2160
```

### Kasus Penggunaan Long-Tail: Instagram Story API

Jika Anda membuat alat manajemen media sosial dan memerlukan **gambar placeholder ukuran Instagram story**, gunakan `/preset/instagram-story/{category}`. Kombinasikan dengan `?fit=smart` untuk foto potret dan `?format=webp&quality=70` untuk pengiriman yang dioptimalkan.


## Penyaringan Orientasi

Filter gambar acak berdasarkan rasio aspek asli mereka sebelum pemilihan. Ini berguna ketika Anda memerlukan gambar yang secara alami cocok dengan tata letak — lanskap untuk header, potret untuk kartu, atau persegi untuk thumbnail.

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

### Konfigurasi

Toleransi `squarish` dapat dikonfigurasi melalui variabel lingkungan `ORIENTATION_SQUARISH_TOLERANCE` (default: `0.15`). Nilai `0.15` berarti gambar dengan rasio aspek antara `0.85` dan `1.15` dianggap persegi. Atur ke `0.0` untuk 1:1 yang tepat.

### Cara Kerja

PlacePix membaca dimensi gambar dari header file selama pemindaian awal (file lokal) dan selama pemindaian metadata latar belakang (gambar S3). Dimensi disimpan dalam memori dan digunakan untuk menyaring kumpulan kandidat sebelum pemilihan acak atau seed. Jika orientasi diminta tetapi tidak ada gambar yang cocok, `404` dikembalikan.
## Filter & Efek

Terapkan filter dan efek real-time ke gambar apa pun melalui parameter query. Semua pemrosesan dilakukan di sisi server dan di-cache untuk permintaan selanjutnya.

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

### Efek Gambar

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

## Pembuat Avatar Huruf

Hasilkan avatar berbasis huruf yang deterministik dari nama atau email apa pun. Sempurna untuk placeholder profil pengguna, sistem komentar, dan direktori tim. Setiap nama selalu menghasilkan warna yang sama, sehingga avatar konsisten di seluruh sesi.

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
# Avatar 128px sederhana
/avatar/128/John+Doe

# Avatar lingkaran dengan border kustom
/avatar/128/John+Doe?circle=true&border=2,ffffff

# Inisial tunggal, palet pastel
/avatar/64/Alice?single=true&palette=pastel

# Output SVG (dapat diskalakan, di bawah 500 byte)
/avatar/128/John+Doe.svg
```

### Mengapa Menggunakan Avatar Huruf?

- Zero external dependencies — no Gravatar or third-party avatar service
- Deterministic — the same name always produces the same color
- SVG support — infinitely scalable, perfect for HiDPI displays
- Four built-in color palettes for any brand aesthetic

## Referensi Cepat REST API

Semua endpoint mendukung CORS dan mengembalikan gambar dengan header cache jangka panjang. Output Base64 JSON tersedia untuk thumbnail kecil.

### Endpoint Gambar

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

## Keahlian dan Kredensial

- Kontributor aktif ke ekosistem open-source sejak 2008
- All code is open source under the MIT License and auditable on <a href="https://github.com/riadvice/placepix" target="_blank" class="text-accent hover:underline">GitHub</a>

## Pertanyaan yang Sering Diajukan

### Bagaimana cara menjalankan PlacePix dengan Docker?

Jalankan `docker run -d -p 3000:3000 -v ./images:/app/images riadvice/placepix:latest`. Mount folder gambar Anda dan layanan segera dimulai dengan pemindaian pintar diaktifkan.

### Apa itu pemotongan pintar yang sadar wajah?

PlacePix menggunakan OpenCV Haar cascades untuk mendeteksi wajah dalam gambar. Ketika Anda menambahkan `?fit=smart` ke URL apa pun, wilayah crop digeser untuk memusatkan pada wajah yang terdeteksi daripada menggunakan pusat geometris. Jika tidak ada wajah yang ditemukan, akan kembali ke crop pusat standar.

### Bisakah saya membuat gambar placeholder gradien tanpa mengunggah foto?

Ya. Endpoint `/gradient/{width}/{height}/{from}/{to}` menghasilkan gambar gradien sepenuhnya dari parameter URL. Tidak diperlukan gambar yang diunggah. Anda juga dapat membuat placeholder SVG dengan `/svg/{width}/{height}`.

### Bagaimana cara membuat gambar placeholder ukuran cerita Instagram melalui API?

Gunakan endpoint preset: `/preset/instagram-story/{category}`. Ini mengembalikan gambar 1080x1920. Gabungkan dengan `?format=webp&quality=70` untuk pengiriman yang dioptimalkan dan `?fit=smart` untuk crop aman potret.

### Apakah PlacePix mendukung penyimpanan objek S3-kompatibel?

Yes. PlacePix works with OVHcloud Object Storage, AWS S3, MinIO, and any S3-compatible provider. Configure endpoint, bucket, access key, and secret key via environment variables.

### Format output apa yang didukung?

WebP, AVIF, JPEG, PNG, SVG, dan base64 JSON. Gunakan `.webp`, `.avif`, atau `.png` sebagai ekstensi file, atau tambahkan `?format=webp` sebagai parameter query. AVIF menghasilkan file terkecil; PNG adalah lossless.

### Apakah PlacePix gratis untuk penggunaan komersial?

Ya. PlacePix dirilis di bawah Lisensi MIT dan gratis untuk penggunaan pribadi dan komersial. Karena self-hosted, tidak ada batasan penggunaan, tidak ada API key, dan tidak ada penagihan per-permintaan.
