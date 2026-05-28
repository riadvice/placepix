---
title: PlacePix Geliştirici Rehberi — Kendi Barındırılan Placeholder Görüntü API'si ve Özellik Referansı
description: Tam PlacePix geliştirici rehberi ve API referansı. Docker ile yer tutucu görüntüleri nasıl dağıtacağınızı, gradyan ve SVG nasıl oluşturacağınızı ve Instagram, YouTube ve daha fazlası için sosyal medya ön ayarlarını nasıl kullanacağınızı öğrenin.
keywords: kendi barındırılan placeholder görüntü API'si, yüz tanımalı kırpma placeholder'ı, gradyan placeholder oluşturucu, Docker placeholder görüntü hizmeti, Instagram story placeholder API'si, SVG placeholder oluşturucu, geliştirici görüntü API'si
author: RIADVICE
robots: index, follow
og_title: PlacePix Geliştirici Rehberi — Kendi Barındırılan Placeholder Görüntü API'si ve Özellik Referansı
og_description: Docker dağıtımı, akıllı kırpma, gradyan yer tutucuları, SVG oluşturma ve sosyal medya ön ayarlarını kapsayan tam geliştirici rehberi.
twitter_title: PlacePix Geliştirici Rehberi — Kendi Barındırılan Placeholder Görüntü API'si ve Özellik Referansı
twitter_description: Docker dağıtımı, akıllı kırpma, gradyan yer tutucuları, SVG oluşturma ve sosyal medya ön ayarlarını kapsayan tam geliştirici rehberi.
jsonld_name: PlacePix Geliştirici Rehberi — Kendi Barındırılan Placeholder Görüntü API'si ve Özellik Referansı
jsonld_description: PlacePix için tam geliştirici rehberi ve API referansı, kendi barındırılan bir yer tutucu görüntü hizmeti. Docker dağıtımı, yüz tanımalı akıllı kırpma, gradyan yer tutucuları, SVG oluşturma ve sosyal medya ön ayarlarını kapsar.
jsonld_proficiency: Expert
jsonld_dependencies: Docker, Python 3.12, FastAPI
header_title: PlacePix Geliştirici Rehberi
header_subtitle: Kendi barındırılan yer tutucu görüntü hizmeti için tam API referansı ve özellik belgeleri. Docker dağıtımı, akıllı kırpma, gradyan yer tutucuları, SVG oluşturma, harf avatarları ve sosyal medya ön ayarlarını kapsar.
author_label: Yazar
updated_label: "Son güncelleme: Mayıs 2026"
github_label: GitHub'da Açık Kaynak
toc_title: İçindekiler
---

## PlacePix Nedir?

PlacePix, geliştiriciler ve tasarım ekipleri için oluşturulmuş **kendi barındırılan bir yer tutucu görüntü hizmetidir**. Harici ağ çağrıları gerektiren ve kaybolabilen üçüncü taraf yer tutucu hizmetlerinin aksine, PlacePix tamamen kendi altyapınızda çalışır. Görüntüleri klasörlere bırakın ve anında yeniden boyutlandırılmış, filtrelenmiş ve formatlanmış görüntüler sunan URL uç noktaları alın.

Hizmet, görüntü işleme Pillow ve OpenCV tarafından desteklenen FastAPI kullanılarak Python'da yazılmıştır. Docker dağıtımını ve S3 uyumlu nesne depolamayı destekler.

### Özellikler

- **Sıfır yapılandırma** — görüntüleri klasörlere bırakın ve başlayın
- **Yüz tanımalı kırpma** — OpenCV yüzleri algılar ve merkezler
- **Gradyan ve SVG yer tutucuları** — görüntü gerekmez
- **Sosyal medya ön ayarları** — Instagram, YouTube, TikTok boyutları dahili
- **Renk arama** — marka paletinize uyan görüntüleri bulun
- **Harf avatarları** — isimlerden deterministik profil görüntüleri

## Docker Dağıtım Kılavuzu

PlacePix'i çalıştırmanın en hızlı yolu Docker'dır. Tek bir komut, akıllı tarama, renk çıkarma ve gömülü URL oluşturucu ile tüm hizmeti dağıtır.

### Tek Satır Dağıtım

```bash
docker run -d -p 3000:3000 \
  -v ./images:/app/images \
  riadvice/placepix:latest
```

### Docker Compose (Önerilen)

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

### Kalıcı Veri ve Ortam

Konteyner yeniden başlatmalarında durumu korumak için hem `/app/images` (görüntü kitaplığınız) hem de `/app/data` (tarama önbelleği ve meta veriler) bağlayın. Davranışı ortam değişkenleri veya bir `.env` dosyası aracılığıyla yapılandırın.

### OVHcloud S3 Uyumlu Depolama

PlacePix herhangi bir S3 uyumlu backend'i destekler. OVHcloud Object Storage için şunları ayarlayın:

```
S3_ENABLED=true
S3_ENDPOINT=https://s3.rbx.io.cloud.ovh.net
S3_ACCESS_KEY=your-key
S3_SECRET_KEY=your-secret
S3_BUCKET=your-bucket
S3_REGION=rbx
```

## Yüz Algılayan Akıllı Kırpma

Standart orta kırpma, portre fotoğrafçılığında yüzleri kesebilir. PlacePix, OpenCV Haar kaskadlarıyla desteklenen **yüz tanımalı akıllı kırpma** ile bunu çözer.

### Nasıl Çalışır

Bir istek `?fit=smart` içerdiğinde, PlacePix OpenCV kullanarak görüntüdeki insan yüzlerini tarar. Yüzler algılanırsa, kırpma penceresi yüz ağırlık merkezinin altın oran kesişim noktalarına olabildiğince yakın olması için kaydırılır. Hiç yüz bulunamazsa, standart orta kırpmaya geri döner.

### API Örnekleri

```
# Yüz tanımalı kırpma (yüzleri algılar ve merkezler)
/400/300/people?fit=smart

# Standart orta kırpma
/400/300/people?fit=crop

# Kapak doldurma (esneyebilir)
/400/300/people?fit=cover

# İçerme (letterboxing)
/400/300/people?fit=contain
```

### Akıllı Kırpma Ne Zaman Kullanılır

- Portre fotoğrafçılığı ve kafa çekimleri
- Yüzlerin önemli olduğu takım sayfaları
- Sosyal medya küçük resimleri
- Geometrik merkez kırpmanın kompozisyonu bozduğu her senaryo

## Gradyan Yer Tutucu API

Herhangi bir kaynak yüklemeden anında doğrusal ve radyal gradyan görüntüleri oluşturun. Kahraman arka planları, yükleme durumları ve tasarım maketleri için mükemmel.

### Endpoint Sözdizimi

```
/gradient/{width}/{height}/{from_hex}/{to_hex}
```

### Örnekler

```
# Basit doğrusal gradyan (yukarıdan aşağıya)
/gradient/800/400/3b82f6/10b981

# 45 derecelik açılı gradyan
/gradient/800/400/e11d48/f59e0b?angle=45

# Merkezden radyal gradyan
/gradient/800/400/1e293b/64748b?gradient_type=radial

# Çıktı formatı ile
/gradient/800/400/0ea5e9/ffffff?format=webp&quality=80
```

### Parametre Referansı

- `{from_hex}` / `{to_hex}` — # öneki olmadan hex renkler
- `?angle=45` — derece cinsinden doğrusal açı (0-360)
- `?gradient_type=radial` — radyal gradyana geçer
- `?format=webp` — WebP çıktısı (daha küçük dosya boyutu)

## SVG Yer Tutucu Oluşturucu

SVG placeholder'ları sunucu tarafı görüntü işlemesi gerektirmez. Özelleştirilebilir arka plan rengi, ön plan rengi ve metin etiketi ile inline SVG olarak oluşturulurlar.

### Endpoint

```
/svg/{width}/{height}?bg={hex}&fg={hex}&text={label}
```

### Örnekler

```
# Default wireframe placeholder
/svg/400/300

# Custom brand colors
/svg/400/300?bg=1c1917&fg=0ea5e9

# With custom text
/svg/400/300?bg=0ea5e9&fg=ffffff&text=Hero+Section
```

### Neden SVG?

- Dosya boyutu 500 byte'ın altında
- Kalite kaybı olmadan sonsuz ölçeklenebilir
- Sıfır sunucu işleme maliyeti
- Wireframe'ler ve düşük kaliteli prototipler için mükemmel

## Sosyal Medya Ön Ayarları

PlacePix, popüler sosyal medya platformları ve ekran boyutları için önceden tanımlanmış boyutlar içerir. Instagram, YouTube, TikTok, LinkedIn, X (Twitter) ve standart ekranlar için mükemmel boyutlu placeholder görüntüleri oluşturmak için bunları kullanın.

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

### Ekran Boyutları

```
/preset/mobile/nature              # 375x812
/preset/tablet/nature              # 768x1024
/preset/desktop/nature             # 1920x1080
/preset/4k/nature                  # 3840x2160
```

### Uzun Kuyruk Kullanım Durumu: Instagram Story API

Bir sosyal medya yönetim aracı oluşturuyorsanız ve **Instagram story boyutu yer tutucu görüntülerine** ihtiyacınız varsa, `/preset/instagram-story/{category}` kullanın. Portre fotoğrafları için `?fit=smart` ile ve optimize edilmiş teslimat için `?format=webp&quality=70` ile birleştirin.

## Renk Arama API

PlacePix'teki her görüntü, ilk 3 baskın rengi için taranır. Marka paletinizle eşleşen görüntüleri bulmak için tüm kitaplığı hex rengine göre arayabilirsiniz.

### Endpoints

```
# Belirli bir hex rengiyle eşleşen görüntü al
/color/0ea5e9/400/300

# Herhangi bir uç noktayı baskın renge göre filtrele
/400/300/nature?color=d97706

# Bir renkle eşleşen tüm görüntüleri listele
/api/color/3b82f6
```

### Renk Tarama Nasıl Çalışır

Başlangıçta PlacePix, LAB renk uzayında k-means kümelemesi kullanarak her görüntüden en sık görülen renkleri çıkarır. Bu, ham RGB ortalamaları yerine algısal olarak doğru eşleşmeler üretir. Palet sayfası (`/palette`) bu renkleri görselleştirir ve ton kategorisine göre göz atmanıza olanak tanır.

## Filtreler ve Efektler

Sorgu parametreleri aracılığıyla herhangi bir görüntüye gerçek zamanlı filtreler ve efektler uygulayın. Tüm işleme sunucu tarafında yapılır ve sonraki istekler için önbelleğe alınır.

### Renk Ayarlamaları

```
?grayscale=1               # Siyah ve beyaz
?sepia=1                   # Sıcak sepya tonu
?tint=0ea5e9               # Hex renk kaplaması
?brightness=1.3            # 0,0 ile 2,0 arası
?contrast=1.2              # 0,0 ile 2,0 arası
?saturation=2.0            # 0,0 ile 2,0 arası
?invert=true               # Renkleri tersine çevir
?posterize=4               # Renk seviyeleri (1-8)
?duotone=ff0000,0000ff     # İki renkli harita
```

### Görüntü Efektleri

```
?blur=2                    # Gauss bulanıklığı (1-10)
?sharpen=1.5               # Keskinleştirme miktarı
?emboss=true               # 3D kabartma
?edges=sobel               # Kenar algılama
?edges=canny               # Canny kenarları
?halftone=4                # Nokta deseni
?oil_painting=true         # Yağlı boya stili
?pencil_sketch=true        # Kalem eskizi
?cartoon=true              # Çizgi film efekti
?vignette=0.5              # Kenarları karart (0-1)
```

### Yerleşim Parametreleri

```
?text=Hello+World          # Metin yerleşimi
?border=4,ffffff           # Kenarlık genişliği ve rengi
?watermark=1               # Yapılandırılmış filigranı uygula
?padding=20                # İç dolgu
```

## Harf Avatarı Oluşturucu

Herhangi bir isim veya e-postadan deterministik harf tabanlı avatarlar oluşturun. Kullanıcı profili yer tutucuları, yorum sistemleri ve takım dizinleri için mükemmel. Her isim her zaman aynı rengi üretir, bu nedenle avatarlar oturumlar arasında tutarlıdır.

### Endpoint

```
/avatar/{size}/{name}
/avatar/{size}/{name}.{ext}
```

### Parametreler

- `size` — piksel boyutu (örn. `64`, `128`, `256`)
- `name` — herhangi bir dize; avatar için ilk harfler çıkarılır
- `circle` — daire şekline kırpma
- `border={width},{color}` — kenarlık ekleme
- `bg={hex}` — arka plan rengini geçersiz kılma
- `fg={hex}` — metin/ön plan rengini geçersiz kılma
- `single=true` — yalnızca ilk harfi kullanma
- `uppercase=false` — küçük harfleri koruma
- `palette={name}` — `flatui`, `material`, `pastel` veya `neon` arasından seçim

### Örnekler

```
# Basit 128px avatar
/avatar/128/John+Doe

# Özel kenarlıklı daire avatar
/avatar/128/John+Doe?circle=true&border=2,ffffff

# Tek baş harf, pastel palet
/avatar/64/Alice?single=true&palette=pastel

# SVG çıktısı (ölçeklenebilir, 500 baytın altında)
/avatar/128/John+Doe.svg
```

### Neden Harf Avatarları Kullanılmalı?

- Sıfır dış bağımlılık — Gravatar veya üçüncü taraf avatar hizmeti yok
- Deterministik — aynı isim her zaman aynı rengi üretir
- SVG desteği — sonsuz ölçeklenebilir, HiDPI ekranlar için mükemmel
- Herhangi bir marka estetiği için dört yerleşik renk paleti

## REST API Hızlı Referans

Tüm uç noktalar CORS'u destekler ve uzun süreli önbellek başlıklarıyla görüntüleri döndürür. Base64 JSON çıktısı küçük küçük resimler için kullanılabilir.

### Görüntü Uç Noktaları

- `GET /{width}/{height}/{category}` — Kategoriden rastgele görüntü
- `GET /{width}/{height}` — Tüm kategorilerden rastgele görüntü
- `GET /id/{id}/{width}/{height}` — ID'ye göre belirli görüntü
- `GET /ratio/{ratio}/{width}/{category}` — En boy oranı görüntüsü
- `GET /preset/{preset}/{category}` — Sosyal medya ön ayarı
- `GET /color/{hex}/{width}/{height}` — Renk eşleşen görüntü
- `GET /gradient/{w}/{h}/{from}/{to}` — Gradyan görüntüsü
- `GET /svg/{width}/{height}` — SVG yer tutucu
- `GET /avatar/{size}/{name}` — Harf avatarı (PNG/SVG)

### Meta Veri Uç Noktaları

- `GET /api/images` — Kategorileri ve toplamları listele
- `GET /api/info/id/{id}` — Görüntü meta verisi (boyutlar, renkler, format)
- `GET /api/color/{hex}` — Bir renkle eşleşen görüntüler

### Sağlık Uç Noktaları

- `GET /health` — Canlılık sondası (Docker/K8s)
- `GET /ready` — Hazır olma sondası (503 görüntüler yüklenene kadar)

## Uzmanlık ve Referanslar

- 2008'den beri açık kaynak ekosistemine aktif katkıda bulunanlar
- Tüm kod MIT Lisansı altında açık kaynak ve <a href="https://github.com/riadvice/placepix" target="_blank" class="text-accent hover:underline">GitHub</a>'da denetlenebilir

## Sıkça Sorulan Sorular

### Docker ile PlacePix'i nasıl dağıtırım?

`docker run -d -p 3000:3000 -v ./images:/app/images riadvice/placepix:latest` komutunu çalıştırın. Görüntü klasörünüzü bağlayın ve hizmet akıllı tarama etkinleştirilmiş olarak hemen başlar.

### Yüz algılayan akıllı kırpma nedir?

PlacePix, görüntülerde yüzleri tespit etmek için OpenCV Haar kaskadlarını kullanır. Herhangi bir URL'ye `?fit=smart` eklediğinizde, kırpma bölgesi geometrik merkezi kullanmak yerine tespit edilen yüzleri ortalamak için kaydırılır. Yüz bulunamazsa, standart orta kırpmaya geri döner.

### Fotoğraf yüklemeden gradyan yer tutucu görüntüleri oluşturabilir miyim?

Evet. `/gradient/{width}/{height}/{from}/{to}` uç noktası, gradyan görüntülerini tamamen URL parametrelerinden oluşturur. Yüklenen görüntülere gerek yoktur. Ayrıca `/svg/{width}/{height}` ile SVG yer tutucuları da oluşturabilirsiniz.

### API ile Instagram story boyutu yer tutucu görüntülerini nasıl oluştururum?

Ön ayar uç noktasını kullanın: `/preset/instagram-story/{category}`. Bu, 1080x1920 bir görüntü döndürür. Optimize edilmiş teslimat için `?format=webp&quality=70` ile ve portre-güvenli kırpma için `?fit=smart` ile birleştirin.

### PlacePix S3 uyumlu nesne depolamayı destekliyor mu?

Evet. PlacePix, OVHcloud Object Storage, AWS S3, MinIO ve herhangi bir S3 uyumlu sağlayıcı ile çalışır. Ortam değişkenleri aracılığıyla uç nokta, kova, erişim anahtarı ve gizli anahtarı yapılandırın.

### Hangi çıktı formatları destekleniyor?

WebP, AVIF, JPEG, PNG, SVG ve base64 JSON. Dosya uzantısı olarak `.webp`, `.avif` veya `.png` kullanın veya sorgu parametresi olarak `?format=webp` ekleyin. AVIF en küçük dosyaları üretir; PNG kayıpsızdır.

### PlacePix ticari kullanım için ücretsiz mi?

Evet. PlacePix MIT Lisansı altında yayınlanmıştır ve hem kişisel hem de ticari kullanım için ücretsizdir. Kendi barındırılan olduğu için, kullanım limiti yoktur, API anahtarı yoktur ve istek başına faturalama yoktur.
