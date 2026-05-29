---
title: Hướng dẫn Nhà phát triển PlacePix — API Hình ảnh Placepoint Tự lưu trữ và Tài liệu tham khảo Tính năng
description: Hướng dẫn nhà phát triển PlacePix đầy đủ và tài liệu tham khảo API. Tìm hiểu cách triển khai hình ảnh placeholder với Docker, tạo gradient và SVG, và sử dụng cấu hình trước cho mạng xã hội Instagram, YouTube và hơn thế nữa.
keywords: API hình ảnh placeholder self-hosted, cắt ảnh thông minh nhận diện khuôn mặt, trình tạo placeholder gradient, dịch vụ hình ảnh placeholder Docker, API placeholder Instagram story, trình tạo placeholder SVG, API hình ảnh nhà phát triển
author: RIADVICE
robots: index, follow
og_title: PlacePix Developer Guide — Self-Hosted Placeholder Image API & Feature Reference
og_description: Hướng dẫn nhà phát triển đầy đủ bao gồm triển khai Docker, cắt ảnh thông minh, placeholder gradient, tạo SVG và cấu hình trước mạng xã hội.
twitter_title: PlacePix Developer Guide — Self-Hosted Placeholder Image API & Feature Reference
twitter_description: Hướng dẫn nhà phát triển đầy đủ bao gồm triển khai Docker, cắt ảnh thông minh, placeholder gradient, tạo SVG và cấu hình trước mạng xã hội.
jsonld_name: PlacePix Developer Guide — Self-Hosted Placeholder Image API & Feature Reference
jsonld_description: Hướng dẫn nhà phát triển đầy đủ và tài liệu tham khảo API cho PlacePix, dịch vụ hình ảnh placeholder self-hosted. Bao gồm triển khai Docker, cắt ảnh thông minh nhận diện khuôn mặt, placeholder gradient, tạo SVG và cấu hình trước mạng xã hội.
jsonld_proficiency: Expert
jsonld_dependencies: Docker, Python 3.12, FastAPI
header_title: Hướng dẫn Nhà phát triển PlacePix
header_subtitle: Tài liệu tham khảo API đầy đủ và tài liệu chức năng cho dịch vụ hình ảnh placeholder tự lưu trữ. Bao gồm triển khai Docker, cắt ảnh thông minh, placeholder chuyển màu, tạo SVG, avatar chữ cái và cấu hình trước mạng xã hội.
author_label: Bởi
updated_label: "Last updated: May 2026"
github_label: Mã nguồn mở trên GitHub
toc_title: Mục lục
---

## PlacePix là gì?

PlacePix là **dịch vụ hình ảnh placeholder tự lưu trữ** được xây dựng cho nhà phát triển và đội ngũ thiết kế. Không giống như các dịch vụ placeholder bên thứ ba yêu cầu các cuộc gọi mạng bên ngoài và có thể biến mất, PlacePix chạy hoàn toàn trên cơ sở hạ tầng của riêng bạn. Thả hình ảnh vào thư mục, và ngay lập tức nhận được các endpoint URL phục vụ hình ảnh đã thay đổi kích thước, được lọc và định dạng.

Dịch vụ được viết bằng Python sử dụng FastAPI với xử lý hình ảnh được cung cấp bởi Pillow và OpenCV. Nó hỗ trợ triển khai Docker, và lưu trữ đối tượng tương thích với S3.

### Tính năng

- **Cấu hình zero** — thả hình ảnh vào thư mục và chạy
- **Cắt ảnh nhận diện khuôn mặt** — OpenCV phát hiện và căn giữa khuôn mặt
- **Placeholder gradient và SVG** — không cần hình ảnh
- **Cấu hình sẵn mạng xã hội** — kích thước Instagram, YouTube, TikTok tích hợp
- **Tìm kiếm theo màu** — tìm hình ảnh phù hợp với bảng màu thương hiệu của bạn
- **Avatar chữ cái** — hình ảnh hồ sơ xác định từ tên

## Hướng dẫn triển khai Docker

Cách nhanh nhất để chạy PlacePix là với Docker. Một lệnh duy nhất triển khai toàn bộ dịch vụ với quét thông minh, trích xuất màu sắc, và trình tạo URL nhúng.

### Triển khai một dòng

```bash
docker run -d -p 3000:3000 \
  -v ./images:/app/images \
  riadvice/placepix:latest
```

### Docker Compose (Khuyến nghị)

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

### Dữ liệu liên tục và Môi trường

Mount both `/app/images` (your image library) and `/app/data` (scan cache and metadata) to preserve state across container restarts. Configure behavior via environment variables or a `.env` file.

### Lưu trữ tương thích S3 OVHcloud

PlacePix supports any S3-compatible backend. For OVHcloud Object Storage, set:

```
S3_ENABLED=true
S3_ENDPOINT=https://s3.rbx.io.cloud.ovh.net
S3_ACCESS_KEY=your-key
S3_SECRET_KEY=your-secret
S3_BUCKET=your-bucket
S3_REGION=rbx
```

## Cắt ảnh thông minh nhận diện khuôn mặt

Cắt ảnh trung tâm tiêu chuẩn có thể cắt xuyên qua khuôn mặt trong nhiếp ảnh chân dung. PlacePix giải quyết điều này bằng **cắt ảnh thông minh nhận diện khuôn mặt** được cung cấp bởi các khoảng Haar của OpenCV.

### Cách thức hoạt động

Khi một yêu cầu bao gồm `?fit=smart`, PlacePix quét hình ảnh để tìm khuôn mặt người bằng OpenCV. Nếu phát hiện khuôn mặt, cửa sổ cắt sẽ được chuyển để tâm khuôn mặt nằm gần nhất có thể với các điểm giao của tỷ lệ vàng. Nếu không tìm thấy khuôn mặt, nó sẽ quay lại cắt trung tâm tiêu chuẩn.

### Ví dụ API

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

### Khi nào sử dụng cắt ảnh thông minh

- Nhiếp ảnh chân dung và ảnh đầu
- Trang nhóm nơi khuôn mặt quan trọng
- Hình thu nhỏ mạng xã hội
- Bất kỳ kịch bản nào trong đó cắt trung tâm hình học làm hỏng bố cục

## API Placeholder Chuyển Màu

Tạo hình ảnh gradient tuyến tính và radial ngay lập tức mà không cần tải lên bất kỳ tài sản nào. Hoàn hảo cho nền hero, trạng thái loading và mockup thiết kế.

### Cú pháp endpoint

```
/gradient/{width}/{height}/{from_hex}/{to_hex}
```

### Ví dụ

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

### Tham chiếu tham số

- `{from_hex}` / `{to_hex}` — màu hex không có tiền tố #
- `?angle=45` — góc tuyến tính tính bằng độ (0-360)
- `?gradient_type=radial` — switches to radial gradient
- `?format=webp` — WebP output (smaller file size)

## Trình Tạo Placeholder SVG

SVG placeholders không yêu cầu xử lý hình ảnh phía máy chủ. Chúng được tạo dưới dạng inline SVG với màu nền, màu chữ và nhãn văn bản có thể tùy chỉnh.

### Endpoint

```
/svg/{width}/{height}?bg={hex}&fg={hex}&text={label}
```

### Ví dụ

```
# Default wireframe placeholder
/svg/400/300

# Custom brand colors
/svg/400/300?bg=1c1917&fg=0ea5e9

# With custom text
/svg/400/300?bg=0ea5e9&fg=ffffff&text=Hero+Section
```

### Tại sao SVG?

- Kích thước tệp dưới 500 byte
- Vô hạn khả năng mở rộng không mất chất lượng
- Không có chi phí xử lý máy chủ
- Hoàn hảo cho wireframes và nguyên mẫu độ trung thực thấp

## Cấu hình trước mạng xã hội

PlacePix bao gồm các kích thước được xác định trước cho các nền tảng xã hội phổ biến và kích thước màn hình. Sử dụng chúng để tạo hình ảnh placeholder có kích thước hoàn hảo cho Instagram, YouTube, TikTok, LinkedIn, X (Twitter) và màn hình tiêu chuẩn.

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

### Kích thước Màn hình

```
/preset/mobile/nature              # 375x812
/preset/tablet/nature              # 768x1024
/preset/desktop/nature             # 1920x1080
/preset/4k/nature                  # 3840x2160
```

### Trường hợp sử dụng đặc biệt: API Instagram Story

Nếu bạn đang xây dựng công cụ quản lý mạng xã hội và cần **hình ảnh placeholder kích thước Instagram story**, hãy sử dụng `/preset/instagram-story/{category}`. Kết hợp với `?fit=smart` cho ảnh chân dung và `?format=webp&quality=70` để tối ưu việc phân phối.


## Lọc theo Hướng

Lọc hình ảnh ngẫu nhiên theo tỷ lệ khung hình gốc của chúng trước khi chọn. Điều này hữu ích khi bạn cần hình ảnh tự nhiên phù hợp với bố cục — ngang cho tiêu đề, dọc cho thẻ hoặc vuông cho hình thu nhỏ.

### Điểm cuối

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

### Cấu hình

Độ dung sai `squarish` có thể cấu hình thông qua biến môi trường `ORIENTATION_SQUARISH_TOLERANCE` (mặc định: `0.15`). Giá trị `0.15` có nghĩa là hình ảnh có tỷ lệ khung hình từ `0.85` đến `1.15` được coi là vuông. Đặt thành `0.0` cho 1:1 chính xác.

### Cách thức hoạt động

PlacePix đọc kích thước hình ảnh từ tiêu đề tệp trong quá trình quét ban đầu (tệp cục bộ) và trong quá trình quét siêu dữ liệu nền (hình ảnh S3). Kích thước được lưu trữ trong bộ nhớ và được sử dụng để lọc nhóm ứng viên trước khi chọn ngẫu nhiên hoặc chọn theo seed. Nếu yêu cầu hướng nhưng không có hình ảnh phù hợp, `404` được trả về.
## Bộ lọc và Hiệu ứng

Áp dụng bộ lọc và hiệu ứng real-time cho bất kỳ hình ảnh nào thông qua tham số truy vấn. Tất cả xử lý được thực hiện phía máy chủ và được lưu cache cho các yêu cầu tiếp theo.

### Điều chỉnh Màu sắc

```
?grayscale=1               # Đen trắng
?sepia=1                   # Tông sepia ấm
?tint=0ea5e9               # Lớp phủ màu hex
?brightness=1.3            # 0.0 đến 2.0
?contrast=1.2              # 0.0 đến 2.0
?saturation=2.0            # 0.0 đến 2.0
?invert=true               # Đảo màu
?posterize=4               # Mức độ màu (1-8)
?duotone=ff0000,0000ff     # Bản đồ hai màu
```

### Hiệu ứng Hình ảnh

```
?blur=2                    # Làm mờ Gaussian (1-10)
?sharpen=1.5               # Mức độ làm nét
?emboss=true               # Nổi 3D
?edges=sobel               # Phát hiện cạnh
?edges=canny               # Cạnh Canny
?halftone=4                # Kiểu chấm
?oil_painting=true         # Phong cách tranh sơn dầu
?pencil_sketch=true        # Phác thảo bút chì
?cartoon=true              # Hiệu ứng hoạt hình
?vignette=0.5              # Làm tối viền (0-1)
```

### Tham số Overlay

```
?text=Hello+World          # Lớp phủ văn bản
?border=4,ffffff           # Chiều rộng & màu viền
?watermark=1               # Áp dụng watermark đã cấu hình
?padding=20                # Khoảng đệm bên trong
```

## Trình Tạo Avatar

Tạo avatar xác định từ bất kỳ tên hoặc email nào. PlacePix hỗ trợ hai loại avatar: **Avatar chữ cái** (chữ cái đầu màu sắc) và **Multiavatar** (avatar vector đa văn hóa).

### Endpoint

```
/avatar/{size}/{name}
/avatar/{size}/{name}.{ext}
```

### Tham số

- `type` — avatar type: `letter` (default) or `multiavatar`
- `size` — pixel size (e.g. `64`, `128`, `256`)
- `name` — any string; used as seed for the avatar

#### Avatar chữ cái (`type=letter`)

- `circle` — crop to a circle shape
- `border={width}` — thêm viền
- `border_color={hex}` — màu viền
- `bg={hex}` — override background color
- `fg={hex}` — override text/foreground color
- `single=true` — use only the first letter
- `uppercase=false` — preserve lowercase letters
- `palette={name}` — choose from `flatui`, `material`, `pastel`, `neon`, `cool`, `warm`

#### Multiavatar (`type=multiavatar`)

- `env` — include environment background (`true` by default, `false` to omit)
- `part` — specific part code (optional, e.g. `11`)
- `theme` — specific theme code (optional, e.g. `C`)

### Ví dụ

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

### Tại sao sử dụng avatar chữ cái?

- Không có phụ thuộc bên ngoài — không có Gravatar hay dịch vụ avatar bên thứ ba
- Xác định — cùng một tên luôn tạo ra cùng một màu
- Hỗ trợ SVG — có thể mở rộng vô hạn, hoàn hảo cho màn hình HiDPI
- Sáu bảng màu tích hợp cho mọi thẩm mỹ thương hiệu

### Tại sao sử dụng Multiavatar?

- 12 tỷ avatar đa văn hóa duy nhất
- Xác định — cùng một tên luôn tạo ra cùng một avatar
- Đầu ra SVG thuần — kích thước tệp nhỏ, có thể mở rộng vô hạn
- Không cần gọi API bên ngoài

## Tài liệu tham khảo nhanh REST API

Tất cả các endpoint đều hỗ trợ CORS và trả về hình ảnh với header cache dài hạn. Đầu ra Base64 JSON có sẵn cho thumbnail nhỏ.

### Endpoint Hình ảnh

- `GET /{width}/{height}/{category}` — Hình ảnh ngẫu nhiên từ danh mục
- `GET /{width}/{height}` — Hình ảnh ngẫu nhiên từ tất cả danh mục
- `GET /id/{id}/{width}/{height}` — Hình ảnh cụ thể theo ID
- `GET /ratio/{ratio}/{width}/{category}` — Hình ảnh tỷ lệ khung hình
- `GET /preset/{preset}/{category}` — Preset mạng xã hội
- `GET /color/{hex}/{width}/{height}` — Hình ảnh khớp màu
- `GET /gradient/{w}/{h}/{from}/{to}` — Hình ảnh gradient
- `GET /svg/{width}/{height}` — SVG placeholder
- `GET /avatar/{size}/{name}` — Avatar chữ cái (PNG/SVG)

### Endpoint Metadata

- `GET /api/images` — Liệt kê danh mục và tổng số
- `GET /api/info/id/{id}` — Metadata hình ảnh (kích thước, màu sắc, định dạng)
- `GET /api/color/{hex}` — Hình ảnh khớp với một màu

### Endpoint Health

- `GET /health` — Kiểm tra liveness (Docker/K8s)
- `GET /ready` — Kiểm tra readiness (503 cho đến khi hình ảnh được tải)

## Chuyên môn và chứng chỉ

- Những người đóng góp tích cực cho hệ sinh thái open-source từ năm 2008
- Toàn bộ mã nguồn mở theo Giấy phép MIT và có thể kiểm toán trên <a href="https://github.com/riadvice/placepix" target="_blank" class="text-accent hover:underline">GitHub</a>

## Câu hỏi thường gặp

### Làm thế nào để triển khai PlacePix với Docker?

Chạy `docker run -d -p 3000:3000 -v ./images:/app/images riadvice/placepix:latest`. Mount thư mục hình ảnh của bạn và dịch vụ sẽ khởi động ngay lập tức với quét thông minh được bật.

### Cắt ảnh thông minh nhận diện khuôn mặt là gì?

PlacePix sử dụng OpenCV Haar cascades để phát hiện khuôn mặt trong hình ảnh. Khi bạn thêm `?fit=smart` vào bất kỳ URL nào, vùng cắt được chuyển để tập trung vào khuôn mặt được phát hiện thay vì sử dụng trung tâm hình học. Nếu không tìm thấy khuôn mặt, nó sẽ quay lại cắt trung tâm tiêu chuẩn.

### Tôi có thể tạo hình ảnh placeholder gradient mà không cần tải lên ảnh không?

Có. Endpoint `/gradient/{width}/{height}/{from}/{to}` tạo hình ảnh gradient hoàn toàn từ các tham số URL. Không cần tải lên hình ảnh. Bạn cũng có thể tạo placeholder SVG với `/svg/{width}/{height}`.

### Làm thế nào để tạo hình ảnh placeholder kích thước Instagram story qua API?

Sử dụng endpoint preset: `/preset/instagram-story/{category}`. Điều này trả về hình ảnh 1080x1920. Kết hợp với `?format=webp&quality=70` để tối ưu việc phân phối và `?fit=smart` để cắt chân dung an toàn.

### PlacePix có hỗ trợ lưu trữ đối tượng tương thích S3 không?

Có. PlacePix hoạt động với OVHcloud Object Storage, AWS S3, MinIO và bất kỳ nhà cung cấp tương thích S3 nào. Cấu hình endpoint, bucket, khóa truy cập và khóa bí mật qua các biến môi trường.

### Định dạng đầu ra nào được hỗ trợ?

WebP, AVIF, JPEG, PNG, SVG và base64 JSON. Sử dụng `.webp`, `.avif` hoặc `.png` làm phần mở rộng tệp, hoặc thêm `?format=webp` làm tham số truy vấn. AVIF tạo ra các tệp nhỏ nhất; PNG là lossless.

### PlacePix có miễn phí cho sử dụng thương mại không?

Có. PlacePix được phát hành theo Giấy phép MIT và miễn phí cho cả sử dụng cá nhân và thương mại. Vì nó là self-hosted, không có giới hạn sử dụng, không có khóa API và không có thanh toán theo yêu cầu.