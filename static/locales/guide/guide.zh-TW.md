---
title: PlacePix 開發者指南 — 自託管佔位符圖像 API 和功能參考
description: 完整的 PlacePix 開發者指南和 API 參考。了解如何使用 Docker 部署佔位符圖像、生成漸層和 SVG，以及使用 Instagram、YouTube 等社群媒體預設。
keywords: 自託管佔位符圖像 API, 人臉感知裁切佔位符, 漸層佔位符生成器, Docker 佔位符圖像服務, Instagram 故事佔位符 API, SVG 佔位符生成器, 開發者圖像 API
author: RIADVICE
robots: index, follow
og_title: PlacePix 開發者指南 — 自託管佔位符圖像 API 和功能參考
og_description: 完整的開發者指南，涵蓋 Docker 部署、智慧裁切、漸層佔位符、SVG 生成和社群媒體預設。
twitter_title: PlacePix 開發者指南 — 自託管佔位符圖像 API 和功能參考
twitter_description: 完整的開發者指南，涵蓋 Docker 部署、智慧裁切、漸層佔位符、SVG 生成和社群媒體預設。
jsonld_name: PlacePix 開發者指南 — 自託管佔位符圖像 API 和功能參考
jsonld_description: PlacePix 的完整開發者指南和 API 參考，這是一個自託管的佔位符圖像服務。涵蓋 Docker 部署、人臉感知智慧裁切、漸層佔位符、SVG 生成和社群媒體預設。
jsonld_proficiency: Expert
jsonld_dependencies: Docker, Python 3.12, FastAPI
header_title: PlacePix 開發者指南
header_subtitle: 自託管佔位符圖像服務的完整 API 參考和功能文件。涵蓋 Docker 部署、智慧裁切、漸層佔位符、SVG 生成、字母頭像和社群媒體預設。
author_label: 作者
updated_label: "最後更新：2026年5月"
github_label: GitHub 上的開源專案
toc_title: 目錄
---

## 什麼是 PlacePix？

PlacePix 是一個為開發者和設計團隊構建的**自託管佔位符圖像服務**。與需要外部網絡調用且可能消失的第三方佔位符服務不同，PlacePix 完全在您自己的基礎設施上運行。將圖像拖放到文件夾中，即可立即獲得提供調整大小、過濾和格式化圖像的 URL 端點。

該服務使用 Python 編寫，採用 FastAPI，圖像處理由 Pillow 和 OpenCV 提供支持。它支持 Docker 部署和兼容 S3 的對象存儲。

### 功能

- **零配置** — 將圖像拖放到文件夾即可開始
- **人臉感知裁切** — OpenCV 檢測並居中人臉
- **漸層和 SVG 佔位符** — 無需圖像
- **社群媒體預設** — 內建 Instagram、YouTube、TikTok 尺寸
- **顏色搜索** — 査找與您的品牌調色盤匹配的圖像
- **字母頭像** — 從姓名生成確定性個人資料圖像

## Docker 部署指南

運行 PlacePix 最快的方式是使用 Docker。一個命令即可部署整個服務，包含智慧掃描、顏色提取和嵌入式 URL 構建器。

### 一行部署

```bash
docker run -d -p 3000:3000 \
  -v ./images:/app/images \
  riadvice/placepix:latest
```

### Docker Compose（推薦）

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

### 持久資料和環境

同時掛載 `/app/images`（您的圖像庫）和 `/app/data`（掃描緩存和元數據）以在容器重啟時保留狀態。通過環境變量或 `.env` 文件配置行為。

### OVHcloud S3 兼容存儲

PlacePix 支持任何兼容 S3 的後端。對於 OVHcloud 對象存儲，請設置：

```
S3_ENABLED=true
S3_ENDPOINT=https://s3.rbx.io.cloud.ovh.net
S3_ACCESS_KEY=your-key
S3_SECRET_KEY=your-secret
S3_BUCKET=your-bucket
S3_REGION=rbx
```

## 人臉感知智慧裁切

標準中心裁切可能會在肖像攝影中切到人臉。PlacePix 通過由 OpenCV Haar 級聯驅動的**人臉感知智慧裁切**解決了這個問題。

### 工作原理

當請求包含 `?fit=smart` 時，PlacePix 使用 OpenCV 掃描圖像以査找人臉。如果檢測到人臉，裁切窗口會移動，使人臉質心盡可能接近黃金比例交點。如果未找到人臉，則回退到標準中心裁切。

### API 範例

```
# 人臉感知裁切（檢測並居中人臉）
/400/300/people?fit=smart

# 標準中心裁切
/400/300/people?fit=crop

# 封面填充（可能拉伸）
/400/300/people?fit=cover

# 包含（信箱格式）
/400/300/people?fit=contain
```

### 何時使用智慧裁切

- 肖像攝影和頭像
- 人臉重要的團隊頁面
- 社交媒體縮略圖
- 幾何中心裁切破壞構圖的任何場景

## 漸層佔位符 API

無需上傳任何資源即可即時生成線性和徑向漸層圖像。非常適合主視覺背景、加載狀態和設計模型。

### 端點語法

```
/gradient/{width}/{height}/{from_hex}/{to_hex}
```

### 範例

```
# 簡單線性漸層（從上到下）
/gradient/800/400/3b82f6/10b981

# 45度角漸層
/gradient/800/400/e11d48/f59e0b?angle=45

# 從中心開始的徑向漸層
/gradient/800/400/1e293b/64748b?gradient_type=radial

# 帶輸出格式
/gradient/800/400/0ea5e9/ffffff?format=webp&quality=80
```

### 參數參考

- `{from_hex}` / `{to_hex}` — 不帶 # 前綴的十六進制顏色
- `?angle=45` — 線性角度，單位為度（0-360）
- `?gradient_type=radial` — 切換到徑向漸層
- `?format=webp` — WebP 輸出（文件更小）

## SVG 佔位符生成器

SVG 佔位符不需要服務器端圖像處理。它們以內聯 SVG 形式生成，具有可自定義的背景色、前景色和文本標籤。

### 端點

```
/svg/{width}/{height}?bg={hex}&fg={hex}&text={label}
```

### 範例

```
# 默認線框佔位符
/svg/400/300

# 自定義品牌顏色
/svg/400/300?bg=1c1917&fg=0ea5e9

# 帶自定義文本
/svg/400/300?bg=0ea5e9&fg=ffffff&text=Hero+Section
```

### 為什麼使用 SVG？

- 文件大小小於 500 字節
- 無限可縮放且無損質量
- 零服務器處理開銷
- 非常適合線框圖和低保真原型

## 社群媒體預設

PlacePix 包含流行社交媒體平台和屏幕尺寸的預定義尺寸。使用這些可為 Instagram、YouTube、TikTok、LinkedIn、X（Twitter）和標準顯示器生成尺寸完美的佔位符圖像。

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

### X（Twitter）

```
/preset/twitter-header/nature      # 1500x500
```

### 屏幕尺寸

```
/preset/mobile/nature              # 375x812
/preset/tablet/nature              # 768x1024
/preset/desktop/nature             # 1920x1080
/preset/4k/nature                  # 3840x2160
```

### 長尾使用案例：Instagram Story API

如果您正在構建社交媒體管理工具並需要 **Instagram 故事尺寸的佔位符圖像**，請使用 `/preset/instagram-story/{category}`。結合 `?fit=smart` 用於肖像照片，`?format=webp&quality=70` 用於優化交付。


## 方向篩選

在選擇之前，按圖像的原始寬高比篩選隨機圖像。當您需要自然適合佈局的圖像時，這很有用——橫向用於頁首，縱向用於卡片，或方形用於縮圖。

### 端點

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

### 設定

`squarish` 容差可透過環境變數 `ORIENTATION_SQUARISH_TOLERANCE` 設定（預設：`0.15`）。`0.15` 的值表示寬高比在 `0.85` 到 `1.15` 之間的圖像被視為方形。設定為 `0.0` 以獲得精確的 1:1。

### 運作原理

PlacePix 在初始掃描期間（本機檔案）和後台元資料掃描期間（S3 圖像）從檔案標頭讀取圖像尺寸。尺寸儲存在記憶體中，用於在隨機或種子選擇之前篩選候選池。如果請求了方向但沒有匹配的圖像，則返回 `404`。

## 顏色搜尋 API

PlacePix 中的每張圖像都會被掃描其前 3 種主導色。您可以通過十六進制顏色搜索整個庫，以査找與您的品牌調色盤匹配的圖像。

### 端點

```
# 獲取與特定十六進制顏色匹配的圖像
/color/0ea5e9/400/300

# 按主導色過濾任何端點
/400/300/nature?color=d97706

# 列出與顏色匹配的所有圖像
/api/color/3b82f6
```

### 顏色掃描如何工作

啟動時，PlacePix 使用 LAB 顏色空間中的 k-means 聚類從每張圖像中提取最頻繁的顏色。這會產生感知上準確的匹配，而不是原始 RGB 平均值。調色盤頁面 (`/palette`) 將這些顏色可視化，並讓您按色調類別瀏覽。

## 濾鏡和效果

通過査詢參數對任何圖像應用實時濾鏡和效果。所有處理都在服務器端完成，並緩存以供後續請求使用。

### 顏色調整

```
?grayscale=1               # 黑白
?sepia=1                   # 暖色調棕褐色
?tint=0ea5e9               # 十六進制顏色疊加
?brightness=1.3            # 0.0 到 2.0
?contrast=1.2              # 0.0 到 2.0
?saturation=2.0            # 0.0 到 2.0
?invert=true               # 反轉顏色
?posterize=4               # 顏色級別（1-8）
?duotone=ff0000,0000ff     # 雙色映射
```

### 圖像效果

```
?blur=2                    # 高斯模糊（1-10）
?sharpen=1.5               # 銳化量
?emboss=true               # 3D 浮雕
?edges=sobel               # 邊緣檢測
?edges=canny               # Canny 邊緣
?halftone=4                # 點狀圖案
?oil_painting=true         # 油畫風格
?pencil_sketch=true        # 鉛筆素描
?cartoon=true              # 卡通效果
?vignette=0.5              # 暗角（0-1）
```

### 疊加參數

```
?text=Hello+World          # 文本疊加
?border=4,ffffff           # 邊框寬度和顏色
?watermark=1               # 應用配置的水印
?padding=20                # 內部填充
```

## 字母頭像生成器

從任何姓名或電子郵件生成確定性的基於字母的頭像。非常適合用戶個人資料佔位符、評論系統和團隊目錄。每個姓名總是產生相同的顏色，因此跨會話的頭像保持一致。

### 端點

```
/avatar/{size}/{name}
/avatar/{size}/{name}.{ext}
```

### 參數

- `size` — 像素大小（例如 `64`、`128`、`256`）
- `name` — 任意字符串；為首字母頭像提取首字母
- `circle` — 裁剪為圓形
- `border={width},{color}` — 添加邊框
- `bg={hex}` — 覆蓋背景顏色
- `fg={hex}` — 覆蓋文本/前景顏色
- `single=true` — 僅使用第一個字母
- `uppercase=false` — 保留小寫字母
- `palette={name}` — 從 `flatui`、`material`、`pastel` 或 `neon` 中選擇

### 範例

```
# 簡單的 128px 頭像
/avatar/128/John+Doe

# 帶自定義邊框的圓形頭像
/avatar/128/John+Doe?circle=true&border=2,ffffff

# 單個首字母，粉彩調色板
/avatar/64/Alice?single=true&palette=pastel

# SVG 輸出（可縮放，小於 500 字節）
/avatar/128/John+Doe.svg
```

### 為什麼使用字母頭像？

- 零外部依賴 — 無需 Gravatar 或第三方頭像服務
- 確定性 — 相同的姓名總是產生相同的顏色
- SVG 支持 — 無限可縮放，非常適合 HiDPI 顯示器
- 四種內置調色板，適合任何品牌美學

## REST API 快速參考

所有端點都支持 CORS，並返回帶有長期緩存標頭的圖像。Base64 JSON 輸出可用於小縮略圖。

### 圖像端點

- `GET /{width}/{height}/{category}` — 從分類中隨機獲取圖像
- `GET /{width}/{height}` — 從所有分類中隨機獲取圖像
- `GET /id/{id}/{width}/{height}` — 通過 ID 獲取特定圖像
- `GET /ratio/{ratio}/{width}/{category}` — 寬高比圖像
- `GET /preset/{preset}/{category}` — 社交媒體預設
- `GET /color/{hex}/{width}/{height}` — 顏色匹配圖像
- `GET /gradient/{w}/{h}/{from}/{to}` — 漸層圖像
- `GET /svg/{width}/{height}` — SVG 佔位符
- `GET /avatar/{size}/{name}` — 字母頭像（PNG/SVG）

### 元數據端點

- `GET /api/images` — 列出分類和總數
- `GET /api/info/id/{id}` — 圖像元數據（尺寸、顏色、格式）
- `GET /api/color/{hex}` — 與顏色匹配的圖像

### 健康端點

- `GET /health` — 活性探針（Docker/K8s）
- `GET /ready` — 就緒探針（503 直到圖像加載完成）

## 專業知識和資質

- 自 2008 年以來積极參与開源生態系統
- 所有代碼均在 MIT 許可證下開源，可在 <a href="https://github.com/riadvice/placepix" target="_blank" class="text-accent hover:underline">GitHub</a> 上審計

## 常見問題

### 如何使用 Docker 部署 PlacePix？

運行 `docker run -d -p 3000:3000 -v ./images:/app/images riadvice/placepix:latest`。掛載您的圖像文件夾，服務將立即啟動並啟用智慧掃描。

### 什麼是人臉感知智慧裁切？

PlacePix 使用 OpenCV Haar 級聯檢測圖像中的人臉。當您在任何 URL 中添加 `?fit=smart` 時，裁切區域會移動以居中於檢測到的人臉，而不是使用幾何中心。如果未找到人臉，則回退到標準中心裁切。

### 我可以不上傳照片就生成漸層佔位符圖像嗎？

是的。`/gradient/{width}/{height}/{from}/{to}` 端點完全從 URL 參數生成漸層圖像。不需要上傳圖像。您還可以使用 `/svg/{width}/{height}` 創建 SVG 佔位符。

### 如何通過 API 生成 Instagram 故事尺寸的佔位符圖像？

使用預設端點：`/preset/instagram-story/{category}`。這將返回 1080x1920 的圖像。結合 `?format=webp&quality=70` 用於優化交付，`?fit=smart` 用於肖像安全裁切。

### PlacePix 是否支援 S3 相容物件儲存？

是的。PlacePix 可與 OVHcloud 對象存儲、AWS S3、MinIO 以及任何 S3 兼容提供商配合使用。通過環境變量配置端點、存儲桶、訪問密鑰和秘密密鑰。

### 支援哪些輸出格式？

WebP、AVIF、JPEG、PNG、SVG 和 base64 JSON。使用 `.webp`、`.avif` 或 `.png` 作為文件擴展名，或添加 `?format=webp` 作為查詢參數。AVIF 產生最小的文件；PNG 是無損的。

### PlacePix 可以免費用於商業用途嗎？

是的。PlacePix 在 MIT 許可證下發布，可免費用於個人和商業用途。由於它是自託管的，因此沒有使用限制、沒有 API 密鑰，也沒有按請求計費。
