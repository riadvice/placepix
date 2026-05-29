---
title: PlacePix 开发者指南 — 自托管占位符图像 API 和功能参考
description: 完整的 PlacePix 开发者指南和 API 参考。了解如何使用 Docker 部署占位符图像、生成渐变和 SVG，以及使用 Instagram、YouTube 等社交媒体预设。
keywords: 自托管占位符图像 API, 人脸感知裁剪占位符, 渐变占位符生成器, Docker 占位符图像服务, Instagram 故事占位符 API, SVG 占位符生成器, 开发者图像 API
author: RIADVICE
robots: index, follow
og_title: PlacePix 开发者指南 — 自托管占位符图像 API 和功能参考
og_description: 完整的开发者指南，涵盖 Docker 部署、智能裁剪、渐变占位符、SVG 生成和社交媒体预设。
twitter_title: PlacePix 开发者指南 — 自托管占位符图像 API 和功能参考
twitter_description: 完整的开发者指南，涵盖 Docker 部署、智能裁剪、渐变占位符、SVG 生成和社交媒体预设。
jsonld_name: PlacePix 开发者指南 — 自托管占位符图像 API 和功能参考
jsonld_description: PlacePix 的完整开发者指南和 API 参考，这是一个自托管的占位符图像服务。涵盖 Docker 部署、人脸感知智能裁剪、渐变占位符、SVG 生成和社交媒体预设。
jsonld_proficiency: Expert
jsonld_dependencies: Docker, Python 3.12, FastAPI
header_title: PlacePix 开发者指南
header_subtitle: 自托管占位符图像服务的完整 API 参考和功能文档。涵盖 Docker 部署、智能裁剪、渐变占位符、SVG 生成、字母头像和社交媒体预设。
author_label: 作者
updated_label: "最后更新：2026年5月"
github_label: GitHub 上的开源项目
toc_title: 目录
---

## 什么是 PlacePix？

PlacePix 是一个为开发者和设计团队构建的**自托管占位符图像服务**。与需要外部网络调用且可能消失的第三方占位符服务不同，PlacePix 完全在您自己的基础设施上运行。将图像拖放到文件夹中，即可立即获得提供调整大小、过滤和格式化图像的 URL 端点。

该服务使用 Python 编写，采用 FastAPI，图像处理由 Pillow 和 OpenCV 提供支持。它支持 Docker 部署和兼容 S3 的对象存储。

### 功能

- **零配置** — 将图像拖放到文件夹即可开始
- **人脸感知裁剪** — OpenCV 检测并居中人脸
- **渐变和 SVG 占位符** — 无需图像
- **社交媒体预设** — 内置 Instagram、YouTube、TikTok 尺寸
- **颜色搜索** — 查找与您的品牌调色板匹配的图像
- **字母头像** — 从姓名生成确定性个人资料图像

## Docker 部署指南

运行 PlacePix 最快的方式是使用 Docker。一个命令即可部署整个服务，包含智能扫描、颜色提取和嵌入式 URL 构建器。

### 一行部署

```bash
docker run -d -p 3000:3000 \
  -v ./images:/app/images \
  riadvice/placepix:latest
```

### Docker Compose（推荐）

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

### 持久数据和环境

同时挂载 `/app/images`（您的图像库）和 `/app/data`（扫描缓存和元数据）以在容器重启时保留状态。通过环境变量或 `.env` 文件配置行为。

### OVHcloud S3 兼容存储

PlacePix 支持任何兼容 S3 的后端。对于 OVHcloud 对象存储，请设置：

```
S3_ENABLED=true
S3_ENDPOINT=https://s3.rbx.io.cloud.ovh.net
S3_ACCESS_KEY=your-key
S3_SECRET_KEY=your-secret
S3_BUCKET=your-bucket
S3_REGION=rbx
```

## 人脸感知智能裁剪

标准中心裁剪可能会在肖像摄影中切到人脸。PlacePix 通过由 OpenCV Haar 级联驱动的**人脸感知智能裁剪**解决了这个问题。

### 工作原理

当请求包含 `?fit=smart` 时，PlacePix 使用 OpenCV 扫描图像以查找人脸。如果检测到人脸，裁剪窗口会移动，使人脸质心尽可能接近黄金比例交点。如果未找到人脸，则回退到标准中心裁剪。

### API 示例

```
# 人脸感知裁剪（检测并居中人脸）
/400/300/people?fit=smart

# 标准中心裁剪
/400/300/people?fit=crop

# 封面填充（可能拉伸）
/400/300/people?fit=cover

# 包含（信箱格式）
/400/300/people?fit=contain
```

### 何时使用智能裁剪

- 肖像摄影和头像
- 人脸重要的团队页面
- 社交媒体缩略图
- 几何中心裁剪破坏构图的任何场景

## 渐变占位符 API

无需上传任何资源即可即时生成线性和径向渐变图像。非常适合主视觉背景、加载状态和设计模型。

### 端点语法

```
/gradient/{width}/{height}/{from_hex}/{to_hex}
```

### 示例

```
# 简单线性渐变（从上到下）
/gradient/800/400/3b82f6/10b981

# 45度角渐变
/gradient/800/400/e11d48/f59e0b?angle=45

# 从中心开始的径向渐变
/gradient/800/400/1e293b/64748b?gradient_type=radial

# 带输出格式
/gradient/800/400/0ea5e9/ffffff?format=webp&quality=80
```

### 参数参考

- `{from_hex}` / `{to_hex}` — 不带 # 前缀的十六进制颜色
- `?angle=45` — 线性角度，单位为度（0-360）
- `?gradient_type=radial` — 切换到径向渐变
- `?format=webp` — WebP 输出（文件更小）

## SVG 占位符生成器

SVG 占位符不需要服务器端图像处理。它们以内联 SVG 形式生成，具有可自定义的背景色、前景色和文本标签。

### 端点

```
/svg/{width}/{height}?bg={hex}&fg={hex}&text={label}
```

### 示例

```
# 默认线框占位符
/svg/400/300

# 自定义品牌颜色
/svg/400/300?bg=1c1917&fg=0ea5e9

# 带自定义文本
/svg/400/300?bg=0ea5e9&fg=ffffff&text=Hero+Section
```

### 为什么使用 SVG？

- 文件大小小于 500 字节
- 无限缩放且无损质量
- 零服务器处理开销
- 非常适合线框图和低保真原型

## 社交媒体预设

PlacePix 包含流行社交媒体平台和屏幕尺寸的预定义尺寸。使用这些可为 Instagram、YouTube、TikTok、LinkedIn、X（Twitter）和标准显示器生成尺寸完美的占位符图像。

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

### 长尾使用案例：Instagram Story API

如果您正在构建社交媒体管理工具并需要 **Instagram 故事尺寸的占位符图像**，请使用 `/preset/instagram-story/{category}`。结合 `?fit=smart` 用于肖像照片，`?format=webp&quality=70` 用于优化交付。


## 方向筛选

在选择之前，按图像的原始宽高比筛选随机图像。当您需要自然适合布局的图像时，这很有用——横向用于页眉，纵向用于卡片，或方形用于缩略图。

### 端点

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

### 配置

`squarish` 容差可通过环境变量 `ORIENTATION_SQUARISH_TOLERANCE` 配置（默认：`0.15`）。`0.15` 的值表示宽高比在 `0.85` 到 `1.15` 之间的图像被视为方形。设置为 `0.0` 以获得精确的 1:1。

### 工作原理

PlacePix 在初始扫描期间（本地文件）和后台元数据扫描期间（S3 图像）从文件头读取图像尺寸。尺寸存储在内存中，用于在随机或种子选择之前筛选候选池。如果请求了方向但没有匹配的图像，则返回 `404`。

## 颜色搜索 API

PlacePix 中的每张图像都会被扫描其前 3 种主导色。您可以通过十六进制颜色搜索整个库，以查找与您的品牌调色板匹配的图像。

### 端点

```
# 获取与特定十六进制颜色匹配的图像
/color/0ea5e9/400/300

# 按主导色过滤任何端点
/400/300/nature?color=d97706

# 列出与颜色匹配的所有图像
/api/color/3b82f6
```

### 颜色扫描如何工作

启动时，PlacePix 使用 LAB 颜色空间中的 k-means 聚类从每张图像中提取最频繁的颜色。这会产生感知上准确的匹配，而不是原始 RGB 平均值。调色板页面 (`/palette`) 将这些颜色可视化，并让您按色调类别浏览。

## 滤镜和效果

通过查询参数对任何图像应用实时滤镜和效果。所有处理都在服务器端完成，并缓存以供后续请求使用。

### 颜色调整

```
?grayscale=1               # 黑白
?sepia=1                   # 暖色调棕褐色
?tint=0ea5e9               # 十六进制颜色叠加
?brightness=1.3            # 0.0 到 2.0
?contrast=1.2              # 0.0 到 2.0
?saturation=2.0            # 0.0 到 2.0
?invert=true               # 反转颜色
?posterize=4               # 颜色级别（1-8）
?duotone=ff0000,0000ff     # 双色映射
```

### 图像效果

```
?blur=2                    # 高斯模糊（1-10）
?sharpen=1.5               # 锐化量
?emboss=true               # 3D 浮雕
?edges=sobel               # 边缘检测
?edges=canny               # Canny 边缘
?halftone=4                # 点状图案
?oil_painting=true         # 油画风格
?pencil_sketch=true        # 铅笔素描
?cartoon=true              # 卡通效果
?vignette=0.5              # 暗角（0-1）
```

### 叠加参数

```
?text=Hello+World          # 文本叠加
?border=4,ffffff           # 边框宽度和颜色
?watermark=1               # 应用配置的水印
?padding=20                # 内部填充
```

## 头像生成器

从任何姓名或电子邮件生成确定性头像。PlacePix 支持两种头像类型：**字母头像**（彩色首字母）和 **Multiavatar**（多元文化矢量头像）。

### 端点

```
/avatar/{size}/{name}
/avatar/{size}/{name}.{ext}
```

### 参数

- `type` — avatar type: `letter` (default) or `multiavatar`
- `size` — pixel size (e.g. `64`, `128`, `256`)
- `name` — any string; used as seed for the avatar

#### 字母头像 (`type=letter`)

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

### 示例

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

### 为什么要使用字母头像？

- 零外部依赖 — 无需 Gravatar 或第三方头像服务
- 确定性 — 相同姓名始终生成相同颜色
- SVG 支持 — 无限可缩放，非常适合 HiDPI 显示器
- 六种内置调色板，适合任何品牌美学

### 为什么要使用 Multiavatar？

- 120 亿个独特的多元文化头像
- 确定性 — 相同姓名始终生成相同头像
- 纯 SVG 输出 — 文件大小极小，无限可缩放
- 无需外部 API 调用

## REST API 快速参考

所有端点都支持 CORS，并返回带有长期缓存标头的图像。Base64 JSON 输出可用于小缩略图。

### 图像端点

- `GET /{width}/{height}/{category}` — 从分类中随机获取图像
- `GET /{width}/{height}` — 从所有分类中随机获取图像
- `GET /id/{id}/{width}/{height}` — 通过 ID 获取特定图像
- `GET /ratio/{ratio}/{width}/{category}` — 宽高比图像
- `GET /preset/{preset}/{category}` — 社交媒体预设
- `GET /color/{hex}/{width}/{height}` — 颜色匹配图像
- `GET /gradient/{w}/{h}/{from}/{to}` — 渐变图像
- `GET /svg/{width}/{height}` — SVG 占位符
- `GET /avatar/{size}/{name}` — 字母头像（PNG/SVG）

### 元数据端点

- `GET /api/images` — 列出分类和总数
- `GET /api/info/id/{id}` — 图像元数据（尺寸、颜色、格式）
- `GET /api/color/{hex}` — 与颜色匹配的图像

### 健康端点

- `GET /health` — 活性探针（Docker/K8s）
- `GET /ready` — 就绪探针（503 直到图像加载完成）

## 专业知识和资质

- 自 2008 年以来积极参与开源生态系统
- 所有代码均在 MIT 许可证下开源，可在 <a href="https://github.com/riadvice/placepix" target="_blank" class="text-accent hover:underline">GitHub</a> 上审计

## 常见问题

### 如何使用 Docker 部署 PlacePix？

运行 `docker run -d -p 3000:3000 -v ./images:/app/images riadvice/placepix:latest`。挂载您的图像文件夹，服务将立即启动并启用智能扫描。

### 什么是人脸感知智能裁剪？

PlacePix 使用 OpenCV Haar 级联检测图像中的人脸。当您在任何 URL 中添加 `?fit=smart` 时，裁剪区域会移动以居中于检测到的人脸，而不是使用几何中心。如果未找到人脸，则回退到标准中心裁剪。

### 我可以不上传照片就生成渐变占位符图像吗？

是的。`/gradient/{width}/{height}/{from}/{to}` 端点完全从 URL 参数生成渐变图像。不需要上传图像。您还可以使用 `/svg/{width}/{height}` 创建 SVG 占位符。

### 如何通过 API 生成 Instagram 故事尺寸的占位符图像？

使用预设端点：`/preset/instagram-story/{category}`。这将返回 1080x1920 的图像。结合 `?format=webp&quality=70` 用于优化交付，`?fit=smart` 用于肖像安全裁剪。

### PlacePix 是否支持 S3 兼容对象存储？

是的。PlacePix 可与 OVHcloud 对象存储、AWS S3、MinIO 以及任何 S3 兼容提供商配合使用。通过环境变量配置端点、存储桶、访问密钥和秘密密钥。

### 支持哪些输出格式？

WebP、AVIF、JPEG、PNG、SVG 和 base64 JSON。使用 `.webp`、`.avif` 或 `.png` 作为文件扩展名，或添加 `?format=webp` 作为查询参数。AVIF 产生最小的文件；PNG 是无损的。

### PlacePix 可以免费用于商业用途吗？

是的。PlacePix 在 MIT 许可证下发布，可免费用于个人和商业用途。由于它是自托管的，因此没有使用限制、没有 API 密钥，也没有按请求计费。