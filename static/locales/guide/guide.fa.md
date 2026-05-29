---
title: راهنمای توسعه‌دهنده PlacePix — API تصویر Placeholder خودمیزبان و مرجع ویژگی‌ها
description: راهنمای کامل توسعه‌دهنده PlacePix و مرجع API. یاد بگیرید چگونه تصاویر placeholder با برش هوشمند تشخیص چهره را با Docker پیاده‌سازی کنید، gradient و SVG placeholder تولید کنید، و از presetهای رسانه‌های اجتماعی برای اینستاگرام، یوتیوب و موارد دیگر استفاده کنید.
keywords: API تصویر placeholder خودمیزبان, placeholder برش چهره‌محور, مولد placeholder gradient, سرویس تصویر placeholder Docker, API placeholder Instagram story, مولد placeholder SVG, API تصویر توسعه‌دهنده
author: RIADVICE
robots: index, follow
og_title: راهنمای توسعه‌دهنده PlacePix — API تصویر Placeholder خودمیزبان و مرجع ویژگی‌ها
og_description: راهنمای کامل توسعه‌دهنده پوشش دهنده استقرار Docker، برش هوشمند، placeholder gradient، تولید SVG و presetهای رسانه‌های اجتماعی.
twitter_title: راهنمای توسعه‌دهنده PlacePix — API تصویر Placeholder خودمیزبان و مرجع ویژگی‌ها
twitter_description: راهنمای کامل توسعه‌دهنده پوشش دهنده استقرار Docker، برش هوشمند، placeholder gradient، تولید SVG و presetهای رسانه‌های اجتماعی.
jsonld_name: راهنمای توسعه‌دهنده PlacePix — API تصویر Placeholder خودمیزبان و مرجع ویژگی‌ها
jsonld_description: راهنمای کامل توسعه‌دهنده و مرجع API برای PlacePix، یک سرویس تصویر placeholder خودمیزبان. پوشش استقرار Docker، برش هوشمند تشخیص چهره، placeholder gradient، تولید SVG و presetهای رسانه‌های اجتماعی.
jsonld_proficiency: Expert
jsonld_dependencies: Docker, Python 3.12, FastAPI
header_title: راهنمای توسعه‌دهنده PlacePix
header_subtitle: مرجع API کامل و مستندات ویژگی‌ها برای سرویس تصویر placeholder خودمیزبان. پوشش استقرار Docker، برش هوشمند، placeholder gradient، تولید SVG، آواتارهای حرفی و presetهای رسانه‌های اجتماعی.
author_label: توسط
updated_label: "آخرین بروزرسانی: می ۲۰۲۶"
github_label: متن باز در GitHub
toc_title: فهرست مطالب
---

## PlacePix چیست؟

PlacePix یک **سرویس تصویر placeholder خودمیزبان** است که برای توسعه‌دهندگان و تیم‌های طراحی ساخته شده است. برخلاف سرویس‌های placeholder شخص ثالث که نیاز به فراخوانی‌های شبکه خارجی دارند و ممکن است ناپدید شوند، PlacePix کاملاً بر روی زیرساخت خود شما اجرا می‌شود. تصاویر را در پوشه‌ها رها کنید و بلافاصله نقاط پایانی URL دریافت کنید که تصاویر تغییر اندازه یافته، فیلتر شده و قالب‌بندی شده را ارائه می‌دهند.

این سرویس با استفاده از Python و FastAPI نوشته شده است با پردازش تصویر توسط Pillow و OpenCV. از استقرار Docker و ذخیره‌سازی شیء سازگار با S3 پشتیبانی می‌کند.

### ویژگی‌ها

- **پیکربندی صفر** — تصاویر را در پوشه‌ها رها کنید و بروید
- **برش هوشمند تشخیص چهره** — OpenCV چهره‌ها را تشخیص می‌دهد و در مرکز قرار می‌دهد
- **Placeholder gradient و SVG** — نیازی به تصویر نیست
- **Presetهای رسانه‌های اجتماعی** — اندازه‌های اینستاگرام، یوتیوب، تیک‌تاک داخلی
- **جستجوی رنگ** — تصاویری را پیدا کنید که با پالت برند شما مطابقت دارند
- **آواتارهای حرفی** — تصاویر پروفایل قطعی از نام‌ها

## راهنمای استقرار Docker

سریع‌ترین راه برای اجرای PlacePix با Docker است. یک دستور واحد کل سرویس را با اسکن هوشمند، استخراج رنگ و سازنده URL تعبیه شده مستقر می‌کند.

### استقرار تک‌خطی

```bash
docker run -d -p 3000:3000 \
  -v ./images:/app/images \
  riadvice/placepix:latest
```

### Docker Compose (توصیه شده)

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

### داده‌های پایدار و محیط

هر دو `/app/images` (کتابخانه تصاویر شما) و `/app/data` (کش اسکن و متاداده) را mount کنید تا وضعیت در راه‌اندازی‌های مجدد کانتینر حفظ شود. رفتار را از طریق متغیرهای محیطی یا فایل `.env` پیکربندی کنید.

### ذخیره‌سازی سازگار با S3 OVHcloud

PlacePix از هر بک‌اند سازگار با S3 پشتیبانی می‌کند. برای OVHcloud Object Storage، تنظیم کنید:

```
S3_ENABLED=true
S3_ENDPOINT=https://s3.rbx.io.cloud.ovh.net
S3_ACCESS_KEY=your-key
S3_SECRET_KEY=your-secret
S3_BUCKET=your-bucket
S3_REGION=rbx
```

## برش هوشمند تشخیص چهره

برش مرکز استاندارد می‌تواند در عکاسی پرتره از چهره‌ها عبور کند. PlacePix این را با **برش هوشمند تشخیص چهره** که توسط آبشارهای Haar OpenCV تقویت شده است، حل می‌کند.

### نحوه کار

وقتی یک درخواست شامل `?fit=smart` باشد، PlacePix تصویر را برای چهره‌های انسان با استفاده از OpenCV اسکن می‌کند. اگر چهره‌ها تشخیص داده شوند، پنجره برش جابجا می‌شود تا مرکز چهره تا حد امکان به نقاط تقاطع نسبت طلایی نزدیک باشد. اگر چهره‌ای پیدا نشد، به برش مرکز استاندارد بازمی‌گردد.

### نمونه‌های API

```
# برش تشخیص چهره (چهره‌ها را تشخیص می‌دهد و در مرکز قرار می‌دهد)
/400/300/people?fit=smart

# برش مرکز استاندارد
/400/300/people?fit=crop

# پر کردن cover (ممکن است کشیده شود)
/400/300/people?fit=cover

# Contain (letterboxing)
/400/300/people?fit=contain
```

### چه زمانی از برش هوشمند استفاده کنید

- عکاسی پرتره و headshot
- صفحات تیم که در آن چهره‌ها مهم هستند
- تصاویر کوچک رسانه‌های اجتماعی
- هر سناریویی که برش مرکز هندسی ترکیب‌بندی را خراب می‌کند

## API Placeholder Gradient

تصاویر gradient خطی و شعاعی را بدون آپلود هیچ assetای تولید کنید. عالی برای پس‌زمینه‌های hero، حالت‌های بارگذاری و mockupهای طراحی.

### سینتکس نقطه پایانی

```
/gradient/{width}/{height}/{from_hex}/{to_hex}
```

### نمونه‌ها

```
# Gradient خطی ساده (بالا به پایین)
/gradient/800/400/3b82f6/10b981

# Gradient زاویه‌دار ۴۵ درجه
/gradient/800/400/e11d48/f59e0b?angle=45

# Gradient شعاعی از مرکز
/gradient/800/400/1e293b/64748b?gradient_type=radial

# با فرمت خروجی
/gradient/800/400/0ea5e9/ffffff?format=webp&quality=80
```

### مرجع پارامترها

- `{from_hex}` / `{to_hex}` — رنگ‌های hex بدون پیشوند #
- `?angle=45` — زاویه خطی به درجه (۰-۳۶۰)
- `?gradient_type=radial` — تولید gradient شعاعی
- `?format=webp` — خروجی WebP، AVIF، JPEG، PNG

## تولیدکننده Placeholder SVG

placeholderهای برداری Scalable را با ابعاد دقیق و رنگ‌های hex سفارشی ایجاد کنید. SVGها زیر ۵۰۰ بایت باقی می‌مانند و در هر DPI بی‌نهایت sharp هستند.

### نحو URL

```
/svg/{width}/{height}
/svg/{width}/{height}/{bg_hex}/{fg_hex}
```

### نمونه‌ها

```
# Placeholder پیش‌فرض
/svg/400/300

# با رنگ‌های سفارشی
/svg/400/300/1e293b/ffffff

# به عنوان فایل SVG با پسوند
/svg/400/300.svg
```

### پارامترهای رشته پرس‌وجو

- `?bg=1e293b` — رنگ پس‌زمینه
- `?fg=ffffff` — رنگ متن/foreground
- `?text=Hello` — متن روی placeholder
- `?font=monospace` — فونت CSS
- `?radius=8` — شعاع گوشه گرد

## Presetهای رسانه‌های اجتماعی

URLهای از پیش تعریف شده برای اندازه‌های رایج شبکه‌های اجتماعی. کافی است `/preset/{name}/{category}` را درخواست کنید.

### اینستاگرام

```
/preset/instagram-post/nature      # ۱۰۸۰x۱۰۸۰
/preset/instagram-story/nature     # ۱۰۸۰x۱۹۲۰
/preset/instagram-reel/nature       # ۱۰۸۰x۱۹۲۰
```

### یوتیوب

```
/preset/youtube-thumbnail/nature    # ۱۲۸۰x۷۲۰
/preset/youtube-banner/nature       # ۲۵۶۰x۱۴۴۰
```

### تیک‌تاک

```
/preset/tiktok-video/nature         # ۱۰۸۰x۱۹۲۰
```

### لینکدین

```
/preset/linkedin-post/nature         # ۱۲۰۰x۶۲۷
```

### ایکس (توییتر)

```
/preset/twitter-header/nature        # ۱۵۰۰x۵۰۰
```

### اندازه‌های صفحه نمایش

```
/preset/mobile/nature               # ۳۷۵x۸۱۲
/preset/tablet/nature               # ۷۶۸x۱۰۲۴
/preset/desktop/nature              # ۱۹۲۰x۱۰۸۰
/preset/4k/nature                   # ۳۸۴۰x۲۱۶۰
```

### مورد استفاده Long-Tail: Instagram Story API

اگر در حال ساخت یک ابزار مدیریت رسانه‌های اجتماعی هستید و به **تصاویر placeholder سایز اینستاگرام استوری** نیاز دارید، از `/preset/instagram-story/{category}` استفاده کنید. با `?fit=smart` برای عکس‌های پرتره و `?format=webp&quality=70` برای تحویل بهینه ترکیب کنید.


## فیلتر جهت

قبل از انتخاب، تصاویر تصادفی را بر اساس نسبت ابعاد اصلی فیلتر کنید. این زمانی مفید است که به تصاویری نیاز دارید که به طور طبیعی در یک طرح قرار می‌گیرند — افقی برای سرصفحه‌ها، عمودی برای کارت‌ها یا مربعی برای تصاویر بندانگشتی.

### نقاط پایانی

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

### پیکربندی

تحمل `squarish` از طریق متغیر محیطی `ORIENTATION_SQUARISH_TOLERANCE` قابل پیکربندی است (پیش‌فرض: `0.15`). مقدار `0.15` به این معناست که تصاویر با نسبت ابعاد بین `0.85` و `1.15` مربعی در نظر گرفته می‌شوند. برای دقیقاً 1:1، مقدار `0.0` تنظیم کنید.

### نحوه کار

PlacePix ابعاد تصاویر را از سرصفحه‌های فایل در طول اسکن اولیه (فایل‌های محلی) و در طول اسکن فراداده در پس‌زمینه (تصاویر S3) می‌خواند. ابعاد در حافظه ذخیره می‌شوند و برای فیلتر کردن مجموعه نامزدها قبل از انتخاب تصادفی یا تعیین‌شده استفاده می‌شوند. اگر جهتی درخواست شود اما هیچ تصویری مطابقت نداشته باشد، `404` بازگردانده می‌شود.

## API جستجوی رنگ

هر تصویر در PlacePix برای ۳ رنگ غالب برتر اسکن می‌شود. شما می‌توانید کل کتابخانه را بر اساس رنگ hex جستجو کنید تا تصاویری را پیدا کنید که با پالت برند شما مطابقت دارند.

### نقاط پایانی

```
# دریافت تصویری که با رنگ hex خاصی مطابقت دارد
/color/0ea5e9/400/300

# فیلتر هر نقطه پایانی بر اساس رنگ غالب
/400/300/nature?color=d97706

# لیست همه تصاویر مطابق با یک رنگ
/api/color/3b82f6
```

### نحوه کار اسکن رنگ

در راه‌اندازی، PlacePix رنگ‌های پرتکرار را از هر تصویر با استفاده از خوشه‌بندی k-means در فضای رنگ LAB استخراج می‌کند. این تطابق‌های دقیق از نظر ادراکی را تولید می‌کند نه میانگین‌های RGB خام. صفحه پالت (`/palette`) این رنگ‌ها را تجسم می‌کند و به شما اجازه می‌دهد بر اساس دسته رنگ مرور کنید.

## فیلترها و افکت‌ها

فیلترها و افکت‌های real-time را از طریق پارامترهای پرس‌وجو به هر تصویری اعمال کنید. تمام پردازش در سمت سرور انجام می‌شود و برای درخواست‌های بعدی کش می‌شود.

### تنظیمات رنگ

```
?grayscale=1               # سیاه و سفید
?sepia=1                   # تون sepia گرم
?tint=0ea5e9               # پوشش رنگ hex
?brightness=1.3            # ۰.۰ تا ۲.۰
?contrast=1.2              # ۰.۰ تا ۲.۰
?saturation=2.0            # ۰.۰ تا ۲.۰
?invert=true               # معکوس کردن رنگ‌ها
?posterize=4               # سطوح رنگ (۱-۸)
?duotone=ff0000,0000ff     # نقشه دو رنگی
```

### افکت‌های تصویر

```
?blur=2                    # Gaussian blur (۱-۱۰)
?sharpen=1.5               # میزان sharpening
?emboss=true               # برجستگی ۳ بعدی
?edges=sobel               # تشخیص لبه
?edges=canny               # لبه‌های Canny
?halftone=4                # الگوی نقطه‌ای
?oil_painting=true         # سبک نقاشی روغنی
?pencil_sketch=true        # طرح مدادی
?cartoon=true              # افکت کارتونی
?vignette=0.5              # تاریک کردن لبه‌ها (۰-۱)
```

### پارامترهای Overlay

```
?text=Hello+World          # پوشش متن
?border=4,ffffff           # عرض و رنگ border
?watermark=1               # اعمال watermark پیکربندی شده
?padding=20                # padding داخلی
```

## تولیدکننده آواتار

آواتارهای قطعی را از هر نام یا ایمیلی تولید کنید. PlacePix از دو نوع آواتار پشتیبانی می‌کند: **آواتار حرفی** (حروف اول رنگی) و **Multiavatar** (آواتارهای برداری چندفرهنگی).

### نقطه پایانی

```
/avatar/{size}/{name}
/avatar/{size}/{name}.{ext}
```

### پارامترها

- `type` — avatar type: `letter` (default) or `multiavatar`
- `size` — pixel size (e.g. `64`, `128`, `256`)
- `name` — any string; used as seed for the avatar

#### آواتار حرفی (`type=letter`)

- `circle` — crop to a circle shape
- `border={width}` — اضافه کردن حاشیه
- `border_color={hex}` — رنگ حاشیه
- `bg={hex}` — override background color
- `fg={hex}` — override text/foreground color
- `single=true` — use only the first letter
- `uppercase=false` — preserve lowercase letters
- `palette={name}` — choose from `flatui`, `material`, `pastel`, `neon`, `cool`, `warm`

#### Multiavatar (`type=multiavatar`)

- `env` — include environment background (`true` by default, `false` to omit)
- `part` — specific part code (optional, e.g. `11`)
- `theme` — specific theme code (optional, e.g. `C`)

### نمونه‌ها

```
# Simple 128px letter avatar
/avatar/128/John+Doe

# Circle letter avatar with custom border
/avatar/128/John+Doe?circle=true&border=2&border_color=ffffff

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

### چرا از آواتارهای حرفی استفاده کنیم؟

- بدون وابستگی خارجی — بدون Gravatar یا سرویس آواتار شخص ثالث
- قطعی — همان نام همیشه همان رنگ را تولید می‌کند
- پشتیبانی از SVG — قابل مقیاس‌بندی نامحدود، مناسب برای نمایشگرهای HiDPI
- شش پالت رنگ داخلی برای هر زیبایی‌شناسی برند

### چرا از Multiavatar استفاده کنیم؟

- 12 میلیارد آواتار چندفرهنگی منحصربه‌فرد
- قطعی — همان نام همیشه همان آواتار را تولید می‌کند
- خروجی SVG خالص — حجم فایل کوچک، قابل مقیاس‌بندی نامحدود
- بدون نیاز به فراخوانی API خارجی

## مرجع سریع REST API

همه نقاط پایانی از CORS پشتیبانی می‌کنند و تصاویر را با هدرهای کش بلندمدت برمی‌گردانند. خروجی JSON Base64 برای تصاویر کوچک در دسترس است.

### نقاط پایانی تصویر

- `GET /{width}/{height}/{category}` — تصویر تصادفی از دسته
- `GET /{width}/{height}` — تصویر تصادفی از همه دسته‌ها
- `GET /id/{id}/{width}/{height}` — تصویر خاص بر اساس ID
- `GET /ratio/{ratio}/{width}/{category}` — تصویر نسبت ابعاد
- `GET /preset/{preset}/{category}` — preset رسانه اجتماعی
- `GET /color/{hex}/{width}/{height}` — تصویر مطابق با رنگ
- `GET /gradient/{w}/{h}/{from}/{to}` — تصویر gradient
- `GET /svg/{width}/{height}` — placeholder SVG
- `GET /avatar/{size}/{name}` — آواتار حرفی (PNG/SVG)

### نقاط پایانی متاداده

- `GET /api/images` — لیست دسته‌ها و مجموع‌ها
- `GET /api/info/id/{id}` — متاداده تصویر (ابعاد، رنگ‌ها، فرمت)
- `GET /api/color/{hex}` — تصاویر مطابق با یک رنگ

### نقاط پایانی سلامت

- `GET /health` — بررسی زنده بودن (Docker/K8s)
- `GET /ready` — بررسی آماده بودن (۵۰۳ تا زمانی که تصاویر بارگذاری شوند)

## تخصص و اعتبار

- مشارکت‌کنندگان فعال در اکوسیستم متن باز از سال ۲۰۰۸
- تمام کد متن باز تحت مجوز MIT و قابل حسابرسی در <a href="https://github.com/riadvice/placepix" target="_blank" class="text-accent hover:underline">GitHub</a>

## سوالات متداول

### چگونه PlacePix را با Docker مستقر کنم؟

`docker run -d -p 3000:3000 -v ./images:/app/images riadvice/placepix:latest` را اجرا کنید. پوشه تصاویر خود را mount کنید و سرویس بلافاصله با اسکن هوشمند فعال شروع به کار می‌کند.

### برش هوشمند تشخیص چهره چیست؟

PlacePix از آبشارهای Haar OpenCV برای تشخیص چهره در تصاویر استفاده می‌کند. وقتی `?fit=smart` را به هر URL اضافه می‌کنید، ناحیه برش به مرکز چهره‌های تشخیص داده شده جابجا می‌شود نه استفاده از مرکز هندسی. اگر چهره‌ای پیدا نشد، به برش مرکز استاندارد بازمی‌گردد.

### آیا می‌توانم تصاویر placeholder gradient بدون آپلود عکس تولید کنم؟

بله. نقطه پایانی `/gradient/{width}/{height}/{from}/{to}` تصاویر gradient را کاملاً از پارامترهای URL تولید می‌کند. هیچ تصویر آپلود شده‌ای لازم نیست. شما همچنین می‌توانید با `/svg/{width}/{height}` placeholder SVG ایجاد کنید.

### چگونه تصاویر placeholder سایز اینستاگرام استوری را از طریق API تولید کنم؟

از نقطه پایانی preset استفاده کنید: `/preset/instagram-story/{category}`. این یک تصویر ۱۰۸۰x۱۹۲۰ برمی‌گرداند. با `?format=webp&quality=70` برای تحویل بهینه و `?fit=smart` برای برش ایمن پرتره ترکیب کنید.

### آیا PlacePix از ذخیره‌سازی شیء سازگار با S3 پشتیبانی می‌کند؟

بله. PlacePix با OVHcloud Object Storage، AWS S3، MinIO و هر ارائه‌دهنده سازگار با S3 کار می‌کند. نقطه پایانی، bucket، کلید دسترسی و کلید مخفی را از طریق متغیرهای محیطی پیکربندی کنید.

### چه فرمت‌های خروجی پشتیبانی می‌شوند؟

WebP، AVIF، JPEG، PNG، SVG و JSON base64. از `.webp`، `.avif` یا `.png` به عنوان پسوند فایل استفاده کنید، یا `?format=webp` را به عنوان پارامتر پرس‌وجو اضافه کنید. AVIF کوچک‌ترین فایل‌ها را تولید می‌کند؛ PNG بدون اتلاف است.

### آیا PlacePix برای استفاده تجاری رایگان است؟

بله. PlacePix تحت مجوز MIT منتشر شده و برای استفاده شخصی و تجاری رایگان است. از آنجا که self-hosted است، هیچ محدودیت استفاده، هیچ کلید API و هیچ صورتحساب per-request وجود ندارد.