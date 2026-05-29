---
title: Посібник розробника PlacePix — API самостійно розміщених зображень placeholder та довідник функцій
description: Повний посібник розробника PlacePix та довідник по API. Дізнайтеся, як розгортати зображення placeholder за допомогою Docker, генерувати градієнти та SVG, та використовувати пресети для соціальних мереж Instagram, YouTube та інших.
keywords: API для зображень placeholder self-hosted, розумна обрізка з розпізнаванням облич, генератор градієнтних плейсхолдерів, Docker сервіс зображень placeholder, API для Instagram story placeholder, генератор SVG placeholder, API для зображень розробника
author: RIADVICE
robots: index, follow
og_title: PlacePix Developer Guide — Self-Hosted Placeholder Image API & Feature Reference
og_description: Повний посібник розробника, що охоплює розгортання Docker, розумну обрізку, градієнтні плейсхолдери, генерацію SVG та пресети для соціальних мереж.
twitter_title: PlacePix Developer Guide — Self-Hosted Placeholder Image API & Feature Reference
twitter_description: Повний посібник розробника, що охоплює розгортання Docker, розумну обрізку, градієнтні плейсхолдери, генерацію SVG та пресети для соціальних мереж.
jsonld_name: PlacePix Developer Guide — Self-Hosted Placeholder Image API & Feature Reference
jsonld_description: Повний посібник розробника та довідник API для PlacePix, self-hosted сервісу зображень placeholder. Охоплює розгортання Docker, розумну обрізку з розпізнаванням облич, градієнтні плейсхолдери, генерацію SVG та пресети для соціальних мереж.
jsonld_proficiency: Expert
jsonld_dependencies: Docker, Python 3.12, FastAPI
header_title: Посібник розробника PlacePix
header_subtitle: Повний довідник по API та документація функцій для самостійно розміщеного сервісу зображень placeholder. Охоплює розгортання Docker, розумну обрізку, градієнтні плейсхолдери, генерацію SVG, літерні аватари та пресети для соціальних мереж.
author_label: Автор
updated_label: "Last updated: May 2026"
github_label: Відкритий код на GitHub
toc_title: Зміст
---

## Що таке PlacePix?

PlacePix — це **self-hosted сервіс placeholder-зображень**, створений для розробників та дизайнерських команд. На відміну від сторонніх placeholder-сервісів, які потребують зовнішніх мережевих викликів і можуть зникнути, PlacePix працює повністю на вашій власній інфраструктурі. Помістіть зображення в папки, і миттєво отримайте URL-ендпоїнти, які обслуговують зображення зі зміненим розміром, відфільтровані та відформатовані.

Сервіс написаний на Python з використанням FastAPI з обробкою зображень на основі Pillow та OpenCV. Він підтримує розгортання Docker та S3-сумісне об'єктне сховище.

### Можливості

- **Нульова конфігурація** — помістіть зображення в папки та йдіть
- **Обрізка з розпізнаванням облич** — OpenCV виявляє та центрує обличчя
- **Gradient та SVG placeholder** — зображення не потрібні
- **Пресети соціальних мереж** — розміри Instagram, YouTube, TikTok вбудовані
- **Пошук за кольором** — знайдіть зображення, що відповідають палітрі вашого бренду
- **Літерні аватари** — детерміновані зображення профілю з імен

## Посібник з розгортання Docker

Найшвидший спосіб запустити PlacePix — за допомогою Docker. Одна команда розгортає весь сервіс з розумним скануванням, вилученням кольорів та вбудованим URL-білдером.

### Розгортання одним рядком

```bash
docker run -d -p 3000:3000 \
  -v ./images:/app/images \
  riadvice/placepix:latest
```

### Docker Compose (Рекомендовано)

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

### Постійні дані та середовище

Mount both `/app/images` (your image library) and `/app/data` (scan cache and metadata) to preserve state across container restarts. Configure behavior via environment variables or a `.env` file.

### Сховище OVHcloud, сумісне з S3

PlacePix supports any S3-compatible backend. For OVHcloud Object Storage, set:

```
S3_ENABLED=true
S3_ENDPOINT=https://s3.rbx.io.cloud.ovh.net
S3_ACCESS_KEY=your-key
S3_SECRET_KEY=your-secret
S3_BUCKET=your-bucket
S3_REGION=rbx
```

## Розумна обрізка з розпізнаванням облич

Стандартне центральне обрізання може розрізати обличчя в портретній фотографії. PlacePix вирішує це за допомогою **розумного обрізання з розпізнаванням облич** на базі каскадів Хаара OpenCV.

### Як це працює

Коли запит включає `?fit=smart`, PlacePix сканує зображення на наявність людських облич за допомогою OpenCV. Якщо обличчя виявлено, вікно обрізання зміщується так, щоб центроїд обличчя знаходився якомога ближче до точок перетину золотого перетину. Якщо обличчя не знайдено, відбувається повернення до стандартного центрального обрізання.

### Приклади API

```
# Face-aware crop (detects and centers faces)
/400/300/people?fit=smart

# Standard center crop
/400/300/people?fit=crop

# Cover fill (may stretch)
/400/300/people?fit=cover

# Contain (letterboxing)
/400/300/people?fit=contain
```

### Коли використовувати розумну обрізку

- Портретна фотографія та знімки голови
- Сторінки команд, де обличчя мають значення
- Мініатюри соціальних мереж
- Будь-який сценарій, де геометричне центральне обрізання псує композицію

## API градієнтних плейсхолдерів

Generate linear and radial gradient images on the fly without uploading any assets. Perfect for hero backgrounds, loading states, and design mockups.

### Синтаксис ендпоінту

```
/gradient/{width}/{height}/{from_hex}/{to_hex}
```

### Приклади

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

### Довідник параметрів

- `{from_hex}` / `{to_hex}` — hex colors without the # prefix
- `?angle=45` — linear angle in degrees (0-360)
- `?gradient_type=radial` — switches to radial gradient
- `?format=webp` — WebP output (smaller file size)

## Генератор SVG-плейсхолдерів

SVG плейсхолдери не вимагають обробки зображень на стороні сервера. Вони генеруються як inline SVG з налаштовуваним кольором фону, кольором переднього плану та текстовою міткою.

### Ендпоінт

```
/svg/{width}/{height}?bg={hex}&fg={hex}&text={label}
```

### Приклади

```
# Default wireframe placeholder
/svg/400/300

# Custom brand colors
/svg/400/300?bg=1c1917&fg=0ea5e9

# With custom text
/svg/400/300?bg=0ea5e9&fg=ffffff&text=Hero+Section
```

### Чому SVG?

- Розмір файлу менше 500 байт
- Безмежно масштабований без втрати якості
- Нульові накладні витрати на обробку сервером
- Ідеально для wireframes та low-fidelity прототипів

## Пресети для соціальних мереж

PlacePix включає попередньо визначені розміри для популярних соціальних платформ та розмірів екранів. Використовуйте їх для створення зображень плейсхолдерів ідеального розміру для Instagram, YouTube, TikTok, LinkedIn, X (Twitter) та стандартних дисплеїв.

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

### Screen Sizes

```
/preset/mobile/nature              # 375x812
/preset/tablet/nature              # 768x1024
/preset/desktop/nature             # 1920x1080
/preset/4k/nature                  # 3840x2160
```

### Додатковий випадок використання: API Instagram Story

Якщо ви створюєте інструмент управління соціальними мережами і потребуєте **зображень placeholder розміру Instagram story**, використовуйте `/preset/instagram-story/{category}`. Поєднайте з `?fit=smart` для портретних фото та `?format=webp&quality=70` для оптимізованої доставки.

## API пошуку за кольором

Кожне зображення в PlacePix сканується на наявність 3 основних кольорів. Ви можете шукати всю бібліотеку за hex кольором, щоб знайти зображення, які відповідають палітрі вашого бренду.

### Ендпоінти

```
# Отримати зображення з конкретним hex кольором
/color/0ea5e9/400/300

# Фільтрувати будь-який ендпоінт за домінантним кольором
/400/300/nature?color=d97706

# Перелік всіх зображень з відповідним кольором
/api/color/3b82f6
```

### Як працює сканування кольорів

При запуску PlacePix витягує найчастіші кольори з кожного зображення за допомогою кластеризації k-means у LAB колірному просторі. Це дає перцептивно точні збіги, а не сирі RGB середні значення. Сторінка палітри (`/palette`) візуалізує ці кольори та дозволяє переглядати за категоріями відтінків.

## Фільтрація за орієнтацією

Фільтруйте випадкові зображення за їхнім вихідним співвідношенням сторін перед вибором. Це корисно, коли вам потрібні зображення, які природно вписуються в макет — альбомна для заголовків, портретна для карток або квадратна для мініатюр.

### Кінцеві точки

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

### Конфігурація

Допуск `squarish` налаштовується через змінну середовища `ORIENTATION_SQUARISH_TOLERANCE` (за замовчуванням: `0.15`). Значення `0.15` означає, що зображення зі співвідношенням сторін між `0.85` і `1.15` вважаються квадратними. Встановіть `0.0` для точного 1:1.

### Як це працює

PlacePix зчитує розміри зображень із заголовків файлів під час початкового сканування (локальні файли) та під час фонового сканування метаданих (зображення S3). Розміри зберігаються в пам'яті та використовуються для фільтрації пула кандидатів перед випадковим або детермінованим вибором. Якщо запитано орієнтацію, але немає відповідних зображень, повертається `404`.

## Фільтри та ефекти

Застосовуйте фільтри та ефекти в реальному часі до будь-якого зображення через параметри запиту. Вся обробка виконується на стороні сервера та кешується для наступних запитів.

### Корекція кольору

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

### Ефекти зображення

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

### Параметри накладання

```
?text=Hello+World          # Text overlay
?border=4,ffffff           # Border width & color
?watermark=1               # Apply configured watermark
?padding=20                # Internal padding
```

## Генератор літерних аватарів

Створюйте детерміновані аватари на основі літер з будь-якого імені або електронної пошти. Ідеально для плейсхолдерів профілів користувачів, систем коментарів і командних директорій. Кожне ім'я завжди дає той самий колір, тому аватари узгоджуються між сеансами.

### Ендпоінт

```
/avatar/{size}/{name}
/avatar/{size}/{name}.{ext}
```

### Параметри

- `size` — розмір у пікселях (напр. `64`, `128`, `256`)
- `name` — будь-який рядок; для аватара витягуються перші літери
- `circle` — обрізати до круглої форми
- `border={width},{color}` — додати рамку
- `bg={hex}` — перевизначити колір фону
- `fg={hex}` — перевизначити колір тексту/переднього плану
- `single=true` — використовувати лише першу літеру
- `uppercase=false` — зберегти малі літери
- `palette={name}` — вибрати з `flatui`, `material`, `pastel` або `neon`

### Приклади

```
# Простий 128px аватар
/avatar/128/John+Doe

# Круглий аватар з користувацьким обрамленням
/avatar/128/John+Doe?circle=true&border=2,ffffff

# Одиночна ініціал, пастельна палітра
/avatar/64/Alice?single=true&palette=pastel

# SVG вивід (масштабований, менше 500 байт)
/avatar/128/John+Doe.svg
```

### Чому використовувати літерні аватари?

- Нульові зовнішні залежності — немає Gravatar або стороннього сервісу аватарів
- Детермінований — одне і те ж ім'я завжди дає той самий колір
- Підтримка SVG — безмежно масштабований, ідеальний для HiDPI дисплеїв
- Чотири вбудовані кольорові палітри для будь-якого бренду

## Швидкий довідник REST API

Всі ендпоїнти підтримують CORS і повертають зображення з довгостроковими заголовками кешу. Вивід Base64 JSON доступний для малих мініатюр.

### Image Endpoints

- `GET /{width}/{height}/{category}` — Випадкове зображення з категорії
- `GET /{width}/{height}` — Випадкове зображення з усіх категорій
- `GET /id/{id}/{width}/{height}` — Конкретне зображення за ID
- `GET /ratio/{ratio}/{width}/{category}` — Зображення зі співвідношенням сторін
- `GET /preset/{preset}/{category}` — Пресет для соціальних мереж
- `GET /color/{hex}/{width}/{height}` — Зображення з відповідним кольором
- `GET /gradient/{w}/{h}/{from}/{to}` — Градієнтне зображення
- `GET /svg/{width}/{height}` — SVG плейсхолдер
- `GET /avatar/{size}/{name}` — Літерний аватар (PNG/SVG)

### Metadata Endpoints

- `GET /api/images` — Список категорій та підсумків
- `GET /api/info/id/{id}` — Метадані зображення (розміри, кольори, формат)
- `GET /api/color/{hex}` — Зображення з відповідним кольором

### Health Endpoints

- `GET /health` — Liveness проба (Docker/K8s)
- `GET /ready` — Readiness проба (503 поки зображення не завантажені)

## Експертиза та рекомендації

- Активні учасники екосистеми open-source з 2008 року
- Увесь код є відкритим під ліцензією MIT і доступний для аудиту на <a href="https://github.com/riadvice/placepix" target="_blank" class="text-accent hover:underline">GitHub</a>

## Часті запитання

### Як розгорнути PlacePix за допомогою Docker?

Запустіть `docker run -d -p 3000:3000 -v ./images:/app/images riadvice/placepix:latest`. Змонтуйте папку зображень і сервіс запуститься негайно з увімкненим розумним скануванням.

### Що таке розумна обрізка з розпізнаванням облич?

PlacePix використовує каскади Хаара OpenCV для виявлення облич на зображеннях. Коли ви додаєте `?fit=smart` до будь-якого URL, область обрізки зміщується до центру на виявлених обличах, а не використовує геометричний центр. Якщо облич не знайдено, він повертається до стандартного центрального обрізання.

### Чи можу я генерувати градієнтні placeholder-зображення без завантаження фотографій?

Так. Ендпоїнт `/gradient/{width}/{height}/{from}/{to}` генерує градієнтні зображення повністю з URL-параметрів. Завантажені зображення не потрібні. Ви також можете створити SVG placeholder з `/svg/{width}/{height}`.

### Як я можу генерувати placeholder-зображення розміру Instagram story через API?

Використовуйте preset ендпоїнт: `/preset/instagram-story/{category}`. Це повертає зображення 1080x1920. Поєднайте з `?format=webp&quality=70` для оптимізованої доставки та `?fit=smart` для безпечного портретного обрізання.

### Чи підтримує PlacePix сховище об'єктів, сумісне з S3?

Так. PlacePix працює з OVHcloud Object Storage, AWS S3, MinIO та будь-яким S3-сумісним провайдером. Налаштуйте ендпоїнт, бакет, ключ доступу та секретний ключ через змінні середовища.

### Які формати виведення підтримуються?

WebP, AVIF, JPEG, PNG, SVG та base64 JSON. Використовуйте `.webp`, `.avif` або `.png` як розширення файлу, або додайте `?format=webp` як параметр запиту. AVIF створює найменші файли; PNG є безвтратним.

### PlacePix безкоштовний для комерційного використання?

Так. PlacePix випущено під ліцензією MIT і безкоштовно як для особистого, так і для комерційного використання. Оскільки це self-hosted, немає обмежень на використання, немає API-ключів і немає тарифікації за запит.
