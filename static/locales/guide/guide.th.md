---
title: คู่มือนักพัฒนา PlacePix — API รูปภาพ Placeholder ที่โฮสต์เองและคู่มืออ้างอิงคุณสมบัติ
description: คู่มือนักพัฒนา PlacePix ฉบับสมบูรณ์และคู่มืออ้างอิง API เรียนรู้วิธีการดำเนินการรูปภาพ placeholder ด้วย Docker สร้าง gradients และ SVG และใช้ค่าที่ตั้งล่วงหน้าของโซเชียลมีเดียสำหรับ Instagram YouTube และอื่นๆ
keywords: API รูปภาพ placeholder self-hosted, การครอปรูปที่รู้จำใบหน้า, เครื่องมือสร้าง placeholder ไล่สี, บริการรูปภาพ placeholder Docker, API placeholder เรื่องราว Instagram, เครื่องมือสร้าง placeholder SVG, API รูปภาพสำหรับนักพัฒนา
author: RIADVICE
robots: index, follow
og_title: PlacePix Developer Guide — Self-Hosted Placeholder Image API & Feature Reference
og_description: คู่มือนักพัฒนาฉบับสมบูรณ์ที่ครอบคลุมการดำเนินการ Docker การตัดภาพอัจฉริยะ placeholder ไล่สี การสร้าง SVG และค่าที่ตั้งล่วงหน้าของโซเชียลมีเดีย
twitter_title: PlacePix Developer Guide — Self-Hosted Placeholder Image API & Feature Reference
twitter_description: คู่มือนักพัฒนาฉบับสมบูรณ์ที่ครอบคลุมการดำเนินการ Docker การตัดภาพอัจฉริยะ placeholder ไล่สี การสร้าง SVG และค่าที่ตั้งล่วงหน้าของโซเชียลมีเดีย
jsonld_name: PlacePix Developer Guide — Self-Hosted Placeholder Image API & Feature Reference
jsonld_description: คู่มือนักพัฒนาฉบับสมบูรณ์และคู่มืออ้างอิง API สำหรับ PlacePix บริการรูปภาพ placeholder แบบ self-hosted ครอบคลุมการดำเนินการ Docker การตัดภาพอัจฉริยะที่รู้จำใบหน้า placeholder ไล่สี การสร้าง SVG และค่าที่ตั้งล่วงหน้าของโซเชียลมีเดีย
jsonld_proficiency: Expert
jsonld_dependencies: Docker, Python 3.12, FastAPI
header_title: คู่มือนักพัฒนา PlacePix
header_subtitle: คู่มืออ้างอิง API ที่สมบูรณ์และเอกสารคุณสมบัติสำหรับบริการรูปภาพ placeholder ที่โฮสต์เอง ครอบคลุมการดำเนินการ Docker การตัดภาพอัจฉริยะ placeholder ไล่สี การสร้าง SVG อวตารตัวอักษร และค่าที่ตั้งล่วงหน้าของโซเชียลมีเดีย
author_label: โดย
updated_label: "Last updated: May 2026"
github_label: โอเพ่นซอร์สบน GitHub
toc_title: สารบัญ
---

## PlacePix คืออะไร?

PlacePix คือ **บริการรูปภาพ placeholder แบบ self-hosted** ที่สร้างขึ้นสำหรับนักพัฒนาและทีมออกแบบ ไม่เหมือนกับบริการ placeholder ของบุคคลที่สามที่ต้องการการเชื่อมต่อเครือข่ายภายนอกและอาจหายไป PlacePix ทำงานทั้งหมดบนโครงสร้างพื้นฐานของคุณเอง วางรูปภาพลงในโฟลเดอร์ และรับ endpoint URL ทันทีที่ให้บริการรูปภาพที่ปรับขนาด กรอง และจัดรูปแบบ

บริการนี้เขียนด้วย Python โดยใช้ FastAPI พร้อมการประมวลผลรูปภาพที่ขับเคลื่อนโดย Pillow และ OpenCV รองรับการปรับใช้ Docker และการจัดเก็บวัตถุที่เข้ากันได้กับ S3

### คุณสมบัติ

- **การกำหนดค่าศูนย์** — วางรูปภาพในโฟลเดอร์และไป
- **การครอบตัดที่ตระหนักถึงใบหน้า** — OpenCV ตรวจจับและจัดศูนย์ใบหน้า
- **Placeholder แบบ Gradient และ SVG** — ไม่ต้องใช้รูปภาพ
- **พรีเซ็ตโซเชียลมีเดีย** — ขนาด Instagram, YouTube, TikTok ในตัว
- **การค้นหาสี** — ค้นหารูปภาพที่ตรงกับพาเลทแบรนด์ของคุณ
- **อวตารตัวอักษร** — รูปภาพโปรไฟล์ที่กำหนดได้จากชื่อ

## คู่มือการดำเนินการ Docker

วิธีที่เร็วที่สุดในการรัน PlacePix คือด้วย Docker คำสั่งเดียวปรับใช้บริการทั้งหมดด้วยการสแกนอัจฉริยะ การแยกสี และ URL builder ที่ฝังอยู่

### การดำเนินการในบรรทัดเดียว

```bash
docker run -d -p 3000:3000 \
  -v ./images:/app/images \
  riadvice/placepix:latest
```

### Docker Compose (แนะนำ)

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

### ข้อมูลถาวรและสภาพแวดล้อม

ติดตั้งทั้ง `/app/images` (ห้องสมุดรูปภาพของคุณ) และ `/app/data` (แคชการสแกนและข้อมูลเมตา) เพื่อรักษาสถานะระหว่างการรีสตาร์ตคอนเทนเนอร์ กำหนดค่าพฤติกรรมผ่านตัวแปรสภาพแวดล้อมหรือไฟล์ `.env`

### พื้นที่จัดเก็บที่เข้ากันได้กับ S3 ของ OVHcloud

PlacePix รองรับแบ็กเอนด์ที่เข้ากันได้กับ S3 ใดๆ สำหรับ OVHcloud Object Storage ให้ตั้งค่า:

```
S3_ENABLED=true
S3_ENDPOINT=https://s3.rbx.io.cloud.ovh.net
S3_ACCESS_KEY=your-key
S3_SECRET_KEY=your-secret
S3_BUCKET=your-bucket
S3_REGION=rbx
```

## การตัดภาพอัจฉริยะที่ตรวจจับใบหน้า

การครอปตรงกลางแบบมาตรฐานสามารถตัดผ่านใบหน้าในการถ่ายภาพบุคคลได้ PlacePix แก้ไขปัญหานี้ด้วย **การครอปอัจฉริยะที่ตรวจจับใบหน้า** โดยใช้ OpenCV Haar cascades

### วิธีการทำงาน

เมื่อคำขอรวมถึง `?fit=smart` PlacePix จะสแกนภาพเพื่อหาใบหน้ามนุษย์โดยใช้ OpenCV หากตรวจพบใบหน้า หน้าต่างการครอปจะถูกเลื่อนเพื่อให้ศูนย์กลางใบหน้าอยู่ใกล้จุดตัดของอัตราส่วนทองคำมากที่สุด หากไม่พบใบหน้า จะกลับไปใช้การครอปตรงกลางแบบมาตรฐาน

### ตัวอย่าง API

```
# การครอปตรวจจับใบหน้า (ตรวจจับและจัดศูนย์ใบหน้า)
/400/300/people?fit=smart

# การครอปตรงกลางมาตรฐาน
/400/300/people?fit=crop

# เติมเต็มแบบครอบ (อาจยืดได้)
/400/300/people?fit=cover

# การบรรจุ (letterboxing)
/400/300/people?fit=contain
```

### เมื่อใดควรใช้ Smart Crop

- การถ่ายภาพบุคคลและภาพหัว
- หน้าทีมงานที่ใบหน้ามีความสำคัญ
- ภาพขนาดย่อของโซเชียลมีเดีย
- สถานการณ์ใดๆ ที่การครอปตรงกลางแบบเรขาคณิตทำลายองค์ประกอบ

## API Placeholder ไล่สี

สร้างรูปภาพ gradient แบบเส้นตรงและแบบรังสีได้ทันทีโดยไม่ต้องอัปโหลด asset ใดๆ เหมาะสำหรับพื้นหลัง hero, สถานะ loading และ mockup ออกแบบ

### ไวยากรณ์ของเอ็นด์พอยต์

```
/gradient/{width}/{height}/{from_hex}/{to_hex}
```

### ตัวอย่าง

```
# ไล่สีเชิงเส้นแบบง่าย (จากบนลงล่าง)
/gradient/800/400/3b82f6/10b981

# ไล่สีมุม 45 องศา
/gradient/800/400/e11d48/f59e0b?angle=45

# ไล่สีรังสีจากศูนย์กลาง
/gradient/800/400/1e293b/64748b?gradient_type=radial

# พร้อมรูปแบบเอาต์พุต
/gradient/800/400/0ea5e9/ffffff?format=webp&quality=80
```

### อ้างอิงพารามิเตอร์

- `{from_hex}` / `{to_hex}` — สี hex โดยไม่มีคำนำหน้า #
- `?angle=45` — มุมเส้นตรงเป็นตารางศูนย์ (0-360)
- `?gradient_type=radial` — เปลี่ยนเป็นไล่สีรังสี
- `?format=webp` — เอาต์พุต WebP (ขนาดไฟล์เล็กกว่า)

## เครื่องมือสร้าง Placeholder SVG

SVG placeholders ไม่จำเป็นต้องประมวลผลภาพฝั่งเซิร์ฟเวอร์ สร้างเป็น inline SVG พร้อมสีพื้นหลัง สีตัวอักษร และป้ายข้อความที่ปรับแต่งได้

### เอ็นด์พอยต์

```
/svg/{width}/{height}?bg={hex}&fg={hex}&text={label}
```

### ตัวอย่าง

```
# Default wireframe placeholder
/svg/400/300

# Custom brand colors
/svg/400/300?bg=1c1917&fg=0ea5e9

# With custom text
/svg/400/300?bg=0ea5e9&fg=ffffff&text=Hero+Section
```

### ทำไม SVG?

- ขนาดไฟล์ต่ำกว่า 500 ไบต์
- ปรับขนาดได้ไม่จำกัดโดยไม่สูญเสียคุณภาพ
- ไม่มีค่าใช้จ่ายในการประมวลผลเซิร์ฟเวอร์
- เหมาะสำหรับ wireframes และต้นแบบความละเอียดต่ำ

## ค่าที่ตั้งล่วงหน้าสำหรับโซเชียลมีเดีย

PlacePix รวมขนาดที่กำหนดไว้ล่วงหน้าสำหรับแพลตฟอร์มโซเชียลยอดนิยมและขนาดหน้าจอ ใช้สิ่งเหล่านี้เพื่อสร้างภาพ placeholder ที่มีขนาดเหมาะสมสำหรับ Instagram, YouTube, TikTok, LinkedIn, X (Twitter) และจอแสดงผลมาตรฐาน

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

### ขนาดหน้าจอ

```
/preset/mobile/nature              # 375x812
/preset/tablet/nature              # 768x1024
/preset/desktop/nature             # 1920x1080
/preset/4k/nature                  # 3840x2160
```

### กรณีการใช้งานหางยาว: Instagram Story API

หากคุณกำลังสร้างเครื่องมือจัดการโซเชียลมีเดียและต้องการ **รูปภาพ placeholder ขนาด Instagram story** ให้ใช้ `/preset/instagram-story/{category}` รวมกับ `?fit=smart` สำหรับภาพบุคคลและ `?format=webp&quality=70` สำหรับการส่งมอบที่ได้รับการปรับแต่ง

## API ค้นหาตามสี

ทุกรูปภาพใน PlacePix จะถูกสแกนหา 3 สีที่โดดเด่นที่สุด คุณสามารถค้นหาทั้งห้องสมุดด้วยสี hex เพื่อหารูปภาพที่ตรงกับพาเลทแบรนด์ของคุณ

### เอ็นด์พอยต์

```
# รับรูปภาพที่ตรงกับสี hex ที่เฉพาะเจาะจง
/color/0ea5e9/400/300

# กรองเอ็นด์พอยต์ใดๆ ตามสีที่โดดเด่น
/400/300/nature?color=d97706

# รายการรูปภาพทั้งหมดที่ตรงกับสี
/api/color/3b82f6
```

### การสแกนสีทำงานอย่างไร

เมื่อเริ่มต้น PlacePix จะแยกสีที่พบบ่อยที่สุดจากแต่ละรูปภาพโดยใช้การจัดกลุ่ม k-means ในพื้นที่สี LAB ซึ่งผลิตการจับคู่ที่แม่นยำตามการรับรู้แทนที่จะเป็นค่าเฉลี่ย RGB ดิบ หน้าพาเลท (`/palette`) แสดงภาพสีเหล่านี้และให้คุณเรียกดูตามหมวดหมู่สี

## ตัวกรองและเอฟเฟกต์

ใช้ตัวกรองและเอฟเฟกต์แบบ real-time กับรูปภาพใดๆ ผ่านพารามิเตอร์ query การประมวลผลทั้งหมดทำที่ฝั่งเซิร์ฟเวอร์และแคชสำหรับคำขอต่อไป

### การปรับแต่งสี

```
?grayscale=1               # ขาวดำ
?sepia=1                   # โทนซีเปียอุ่น
?tint=0ea5e9               # การซ้อนทับสีฮกซ์
?brightness=1.3            # 0.0 ถึง 2.0
?contrast=1.2              # 0.0 ถึง 2.0
?saturation=2.0            # 0.0 ถึง 2.0
?invert=true               # กลับสี
?posterize=4               # ระดับสี (1-8)
?duotone=ff0000,0000ff     # แผนที่สีสองสี
```

### เอฟเฟกต์รูปภาพ

```
?blur=2                    # ความเบลอแบบเกาส์เซียน (1-10)
?sharpen=1.5               # จำนวนการเพิ่มความคม
?emboss=true               # นูน 3 มิติ
?edges=sobel               # การตรวจจับขอบ
?edges=canny               # ขอบแบบแคนนี่
?halftone=4                # รูปแบบจุด
?oil_painting=true         # สไตล์ภาพวาดสีน้ำมัน
?pencil_sketch=true        # ร่างดินสอ
?cartoon=true              # เอฟเฟกต์การ์ตูน
?vignette=0.5              # มืดขอบ (0-1)
```

### พารามิเตอร์การวางซ้อน

```
?text=Hello+World          # การวางซ้อนข้อความ
?border=4,ffffff           # ความกว้างและสีของขอบ
?watermark=1               # ใช้ลายน้ำที่กำหนดค่าไว้
?padding=20                # การเติมภายใน
```

## เครื่องมือสร้างอวตารตัวอักษร

สร้างอวตารตัวอักษรแบบกำหนดได้จากชื่อหรืออีเมลใดๆ เหมาะสำหรับตัวยึดตำแหน่งโปรไฟล์ผู้ใช้ ระบบความคิดเห็น และไดเรกทอรีทีม ชื่อแต่ละชื่อจะผลิตสีเดียวกันเสมอ ดังนั้นอวตารจะสอดคล้องกันในทุกเซสชัน

### เอ็นด์พอยต์

```
/avatar/{size}/{name}
/avatar/{size}/{name}.{ext}
```

### พารามิเตอร์

- `size` — ขนาดพิกเซล (เช่น `64`, `128`, `256`)
- `name` — สตริงใดๆ ตัวอักษรแรกจะถูกแยกออกมาสำหรับอวตาร
- `circle` — ครอปเป็นทรงกลม
- `border={width},{color}` — เพิ่มขอบ
- `bg={hex}` — แทนที่สีพื้นหลัง
- `fg={hex}` — แทนที่สีข้อความ/พื้นหน้า
- `single=true` — ใช้เฉพาะตัวอักษรแรก
- `uppercase=false` — รักษาตัวอักษรพิมพ์เล็ก
- `palette={name}` — เลือกจาก `flatui`, `material`, `pastel` หรือ `neon`

### ตัวอย่าง

```
# อวตาร 128px แบบง่าย
/avatar/128/John+Doe

# อวตารวงกลมพร้อมขอบแบบกำหนดเอง
/avatar/128/John+Doe?circle=true&border=2,ffffff

# ตัวอักษรแรกเดียว พาเลทพาสเทล
/avatar/64/Alice?single=true&palette=pastel

# เอาต์พุต SVG (สเกลได้ ภายใต้ 500 ไบต์)
/avatar/128/John+Doe.svg
```

### ทำไมต้องใช้อวตารตัวอักษร?

- ไม่มีการพึ่งพาภายนอก — ไม่มี Gravatar หรือบริการอวตารบุคคลที่สาม
- กำหนดได้ — ชื่อเดียวกันจะสร้างสีเดียวกันเสมอ
- รองรับ SVG — สเกลได้ไม่จำกัด เหมาะสำหรับจอแสดงผล HiDPI
- มีพาเลทสี่ชุดในตัวสำหรับทุกสไตล์แบรนด์

## คู่มืออ้างอิง REST API อย่างรวดเร็ว

ทุกเอนด์พอยท์รองรับ CORS และส่งคืนรูปภาพด้วยส่วนหัวแคชระยะยาว มีเอาต์พุต JSON แบบ Base64 สำหรับภาพขนาดย่อเล็กๆ

### เอ็นด์พอยต์รูปภาพ

- `GET /{width}/{height}/{category}` — รูปภาพสุ่มจากหมวดหมู่
- `GET /{width}/{height}` — รูปภาพสุ่มจากทุกหมวดหมู่
- `GET /id/{id}/{width}/{height}` — รูปภาพเฉพาะตาม ID
- `GET /ratio/{ratio}/{width}/{category}` — รูปภาพอัตราส่วนภาพ
- `GET /preset/{preset}/{category}` — พรีเซ็ตโซเชียลมีเดีย
- `GET /color/{hex}/{width}/{height}` — รูปภาพที่ตรงกับสี
- `GET /gradient/{w}/{h}/{from}/{to}` — รูปภาพไล่สี
- `GET /svg/{width}/{height}` — ตัวยึดตำแหน่ง SVG
- `GET /avatar/{size}/{name}` — อวตารตัวอักษร (PNG/SVG)

### เอ็นด์พอยต์ข้อมูลเมตา

- `GET /api/images` — รายการหมวดหมู่และรวม
- `GET /api/info/id/{id}` — ข้อมูลเมตารูปภาพ (ขนาด สี รูปแบบ)
- `GET /api/color/{hex}` — รูปภาพที่ตรงกับสี

### เอ็นด์พอยต์สถานะ

- `GET /health` — การตรวจสอบความมีชีวิต (Docker/K8s)
- `GET /ready` — การตรวจสอบความพร้อม (503 จนกว่ารูปภาพจะโหลด)

## ความเชี่ยวชาญและหลักฐานการรับรอง

- ผู้มีส่วนร่วมที่ใช้งานอยู่ในระบบนิเวศโอเพ่นซอร์สตั้งแต่ปี 2008
- โค้ดทั้งหมดเป็นโอเพ่นซอร์สภายใต้ MIT License และสามารถตรวจสอบได้บน <a href="https://github.com/riadvice/placepix" target="_blank" class="text-accent hover:underline">GitHub</a>

## คำถามที่พบบ่อย

### ฉันจะดำเนินการ PlacePix ด้วย Docker ได้อย่างไร?

รัน `docker run -d -p 3000:3000 -v ./images:/app/images riadvice/placepix:latest` ติดตั้งโฟลเดอร์รูปภาพของคุณและบริการเริ่มทำงานทันทีพร้อมเปิดใช้งานการสแกนอัจฉริยะ

### การตัดภาพอัจฉริยะที่ตรวจจับใบหน้าคืออะไร?

PlacePix ใช้ OpenCV Haar cascades เพื่อตรวจจับใบหน้าในรูปภาพ เมื่อคุณเพิ่ม `?fit=smart` ลงใน URL ใดๆ บริเวณครอบตัดจะเลื่อนไปจัดศูนย์กลางบนใบหน้าที่ตรวจพบแทนที่จะใช้ศูนย์กลางเรขาคณิต หากไม่พบใบหน้า จะกลับไปใช้การครอบตัดศูนย์กลางมาตรฐาน

### ฉันสามารถสร้างรูปภาพ placeholder แบบไล่สีได้โดยไม่ต้องอัปโหลดรูปภาพหรือไม่?

ใช่ เอนด์พอยท์ `/gradient/{width}/{height}/{from}/{to}` สร้างรูปภาพไล่สีทั้งหมดจากพารามิเตอร์ URL ไม่จำเป็นต้องมีรูปภาพที่อัปโหลด คุณยังสามารถสร้าง placeholder SVG ด้วย `/svg/{width}/{height}` ได้

### ฉันจะสร้างรูปภาพ placeholder ขนาด Instagram story ผ่าน API ได้อย่างไร?

ใช้เอนด์พอยท์ preset: `/preset/instagram-story/{category}` ส่งคืนรูปภาพ 1080x1920 รวมกับ `?format=webp&quality=70` สำหรับการส่งมอบที่ได้รับการปรับแต่งและ `?fit=smart` สำหรับการครอบตัดที่ปลอดภัยสำหรับภาพบุคคล

### PlacePix รองรับการจัดเก็บวัตถุที่เข้ากันได้กับ S3 หรือไม่?

ใช่ PlacePix ทำงานร่วมกับ OVHcloud Object Storage, AWS S3, MinIO และผู้ให้บริการที่เข้ากันได้กับ S3 ใดๆ กำหนดค่าเอนด์พอยท์ บักเก็ต คีย์การเข้าถึง และคีย์ลับผ่านตัวแปรสภาพแวดล้อม

### รองรับรูปแบบเอาต์พุตอะไรบ้าง?

WebP, AVIF, JPEG, PNG, SVG และ base64 JSON ใช้ `.webp`, `.avif` หรือ `.png` เป็นส่วนขยายไฟล์ หรือเพิ่ม `?format=webp` เป็นพารามิเตอร์การสืบค้น AVIF สร้างไฟล์ที่เล็กที่สุด PNG เป็นแบบไม่สูญเสียข้อมูล

### PlacePix ใช้ฟรีสำหรับการใช้งานเชิงพาณิชย์หรือไม่?

ใช่ PlacePix เผยแพร่ภายใต้ MIT License และฟรีสำหรับการใช้งานส่วนบุคคลและเชิงพาณิชย์ เนื่องจากเป็นแบบโฮสต์เอง จึงไม่มีข้อจำกัดการใช้งาน ไม่มีคีย์ API และไม่มีการเรียกเก็บเงินต่อคำขอ
