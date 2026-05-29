---
title: PlacePix 개발자 가이드 — 셀프 호스팅 플레이스홀더 이미지 API 및 기능 참조
description: 완전한 PlacePix 개발자 가이드 및 API 참조. Docker를 사용하여 플레이스홀더 이미지를 배포하고, 그라데이션과 SVG를 생성하며, Instagram, YouTube 등을 위한 소셜 미디어 프리셋을 사용하는 방법을 알아보세요.
keywords: self-hosted placeholder image API, face-aware crop placeholder, gradient placeholder generator, Docker placeholder image service, Instagram story placeholder API, SVG placeholder generator, developer image API
author: RIADVICE
robots: index, follow
og_title: PlacePix 개발자 가이드 — 셀프 호스팅 플레이스홀더 이미지 API 및 기능 참조
og_description: Docker 배포, 스마트 크롭, 그라데이션 플레이스홀더, SVG 생성 및 소셜 미디어 프리셋을 다루는 완전한 개발자 가이드.
twitter_title: PlacePix 개발자 가이드 — 셀프 호스팅 플레이스홀더 이미지 API 및 기능 참조
twitter_description: Docker 배포, 스마트 크롭, 그라데이션 플레이스홀더, SVG 생성 및 소셜 미디어 프리셋을 다루는 완전한 개발자 가이드.
jsonld_name: PlacePix 개발자 가이드 — 셀프 호스팅 플레이스홀더 이미지 API 및 기능 참조
jsonld_description: PlacePix(셀프 호스팅 플레이스홀더 이미지 서비스)의 완전한 개발자 가이드 및 API 참조. Docker 배포, 얼굴 인식 스마트 크롭, 그라데이션 플레이스홀더, SVG 생성 및 소셜 미디어 프리셋을 다룹니다.
jsonld_proficiency: Expert
jsonld_dependencies: Docker, Python 3.12, FastAPI
header_title: PlacePix 개발자 가이드
header_subtitle: 셀프 호스팅 플레이스홀더 이미지 서비스에 대한 완전한 API 참조 및 기능 문서. Docker 배포, 스마트 크롭, 그라데이션 플레이스홀더, SVG 생성, 글자 아바타, 소셜 미디어 프리셋을 다룹니다.
author_label: 작성자
updated_label: "마지막 업데이트: 2026년 5월"
github_label: GitHub에서 오픈 소스
toc_title: 목차
---

## PlacePix란 무엇인가?

PlacePix는 개발자와 디자인 팀을 위해 구축된 **셀프 호스팅 플레이스홀더 이미지 서비스**입니다. 외부 네트워크 호출이 필요하고 사라질 수 있는 타사 플레이스홀더 서비스와 달리 PlacePix는 완전히 자신의 인프라에서 실행됩니다. 이미지를 폴더에 넣으면 즉시 크기 조정, 필터링 및 형식화된 이미지를 제공하는 URL 엔드포인트를 얻을 수 있습니다.

이 서비스는 Python으로 작성되었으며 FastAPI를 사용하고 Pillow와 OpenCV로 이미지 처리를 제공합니다. Docker 배포 및 S3 호환 객체 스토리지를 지원합니다.

### 기능

- **제로 구성** — 이미지를 폴더에 넣고 시작
- **얼굴 인식 크롭** — OpenCV가 얼굴을 감지하고 중앙에 배치
- **그라데이션 및 SVG 플레이스홀더** — 이미지 불필요
- **소셜 미디어 프리셋** — Instagram, YouTube, TikTok 크기 내장
- **색상 검색** — 브랜드 팔레트와 일치하는 이미지 찾기
- **글자 아바타** — 이름에서 결정론적 프로필 이미지 생성

## Docker 배포 가이드

PlacePix를 실행하는 가장 빠른 방법은 Docker입니다. 단일 명령으로 스마트 스캐닝, 색상 추출 및 임베디드 URL 빌더가 포함된 전체 서비스를 배포합니다.

### 한 줄 배포

```bash
docker run -d -p 3000:3000 \
  -v ./images:/app/images \
  riadvice/placepix:latest
```

### Docker Compose (권장)

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

### 지속적인 데이터 및 환경

컨테이너 재시작 시 상태를 보존하기 위해 `/app/images`(이미지 라이브러리)와 `/app/data`(스캔 캐시 및 메타데이터)를 모두 마운트하세요. 환경 변수 또는 `.env` 파일을 통해 동작을 구성하세요.

### OVHcloud S3 호환 스토리지

PlacePix는 모든 S3 호환 백엔드를 지원합니다. OVHcloud Object Storage의 경우 다음을 설정하세요:

```
S3_ENABLED=true
S3_ENDPOINT=https://s3.rbx.io.cloud.ovh.net
S3_ACCESS_KEY=your-key
S3_SECRET_KEY=your-secret
S3_BUCKET=your-bucket
S3_REGION=rbx
```

## 얼굴 인식 스마트 크롭

표준 중앙 크롭은 초상 사진에서 얼굴을 자를 수 있습니다. PlacePix는 OpenCV Haar 캐스케이드를 통해 구동되는 **얼굴 인식 스마트 크롭**으로 이 문제를 해결합니다.

### 작동 방식

요청에 `?fit=smart`가 포함되면 PlacePix는 OpenCV를 사용하여 이미지에서 사람 얼굴을 스캔합니다. 얼굴이 감지되면 크롭 창이 이동하여 얼굴 중심점이 황금비 교차점에 가능한 한 가깝게 위치하도록 합니다. 얼굴을 찾지 못하면 표준 중앙 크롭으로 폴백합니다.

### API 예제

```
# 얼굴 인식 크롭(얼굴 감지 및 중앙 배치)
/400/300/people?fit=smart

# 표준 중앙 크롭
/400/300/people?fit=crop

# 커버 채우기(늘어날 수 있음)
/400/300/people?fit=cover

# 컨테인(레터박싱)
/400/300/people?fit=contain
```

### 스마트 크롭을 사용할 때

- 초상 사진 및 헤드샷
- 얼굴이 중요한 팀 페이지
- 소셜 미디어 썸네일
- 기하학적 중앙 크롭이 구도를 망치는 모든 시나리오

## 그라데이션 플레이스홀더 API

리소스를 업로드하지 않고 즉석에서 선형 및 방사형 그라데이션 이미지를 생성하세요. 히어로 배경, 로딩 상태 및 디자인 목업에 완벽합니다.

### 엔드포인트 구문

```
/gradient/{width}/{height}/{from_hex}/{to_hex}
```

### 예제

```
# 간단한 선형 그라데이션(위에서 아래로)
/gradient/800/400/3b82f6/10b981

# 45도 각도 그라데이션
/gradient/800/400/e11d48/f59e0b?angle=45

# 중심에서 방사형 그라데이션
/gradient/800/400/1e293b/64748b?gradient_type=radial

# 출력 형식 포함
/gradient/800/400/0ea5e9/ffffff?format=webp&quality=80
```

### 매개변수 참조

- `{from_hex}` / `{to_hex}` — # 접두사 없는 16진수 색상
- `?angle=45` — 선형 각도(도 단위, 0-360)
- `?gradient_type=radial` — 방사형 그라데이션으로 전환
- `?format=webp` — WebP 출력(더 작은 파일 크기)

## SVG 플레이스홀더 생성기

SVG 플레이스홀더는 서버 측 이미지 처리가 필요 없습니다. 사용자 지정 가능한 배경색, 전경색 및 텍스트 레이블을 가진 인라인 SVG로 생성됩니다.

### 엔드포인트

```
/svg/{width}/{height}?bg={hex}&fg={hex}&text={label}
```

### 예제

```
# 기본 와이어프레임 플레이스홀더
/svg/400/300

# 사용자 지정 브랜드 색상
/svg/400/300?bg=1c1917&fg=0ea5e9

# 사용자 지정 텍스트 포함
/svg/400/300?bg=0ea5e9&fg=ffffff&text=Hero+Section
```

### 왜 SVG인가?

- 파일 크기 500바이트 미만
- 품질 손실 없이 무한 확장 가능
- 제로 서버 처리 오버헤드
- 와이어프레임 및 저충실도 프로토타입에 완벽

## 소셜 미디어 프리셋

PlacePix에는 인기 있는 소셜 플랫폼과 화면 크기에 대해 미리 정의된 치수가 포함되어 있습니다. 이를 사용하여 Instagram, YouTube, TikTok, LinkedIn, X(Twitter) 및 표준 디스플레이에 맞는 완벽한 크기의 플레이스홀더 이미지를 생성하세요.

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

### 화면 크기

```
/preset/mobile/nature              # 375x812
/preset/tablet/nature              # 768x1024
/preset/desktop/nature             # 1920x1080
/preset/4k/nature                  # 3840x2160
```

### 롱테일 사용 사례: Instagram Story API

소셜 미디어 관리 도구를 구축하고 **Instagram 스토리 크기 플레이스홀더 이미지**가 필요한 경우 `/preset/instagram-story/{category}`를 사용하세요. 초상 사진에는 `?fit=smart`를, 최적화된 전달에는 `?format=webp&quality=70`를 조합하세요.

## 색상 검색 API

PlacePix의 모든 이미지는 상위 3개의 지배적인 색상으로 스캔됩니다. 16진수 색상으로 전체 라이브러리를 검색하여 브랜드 팔레트와 일치하는 이미지를 찾을 수 있습니다.

### 엔드포인트

```
# 특정 16진수 색상과 일치하는 이미지 가져오기
/color/0ea5e9/400/300

# 지배적인 색상으로 엔드포인트 필터링
/400/300/nature?color=d97706

# 색상과 일치하는 모든 이미지 나열
/api/color/3b82f6
```

### 색상 스캔 작동 방식

시작 시 PlacePix는 LAB 색상 공간에서 k-means 클러스터링을 사용하여 각 이미지에서 가장 빈번한 색상을 추출합니다. 이는 원시 RGB 평균이 아닌 지각적으로 정확한 일치를 생성합니다. 팔레트 페이지(`/palette`)는 이러한 색상을 시각화하고 색조 카테고리별로 검색할 수 있게 합니다.

## 방향 필터링

선택하기 전에 이미지의 기본 가로세로 비율로 무작위 이미지를 필터링합니다. 이는 헤더용 가로, 카드용 세로 또는 썸네일용 정사각형 등 레이아웃에 자연스럽게 맞는 이미지가 필요할 때 유용합니다.

### 엔드포인트

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

### 설정

`squarish` 허용 오차는 환경 변수 `ORIENTATION_SQUARISH_TOLERANCE`를 통해 구성할 수 있습니다(기본값: `0.15`). `0.15` 값은 가로세로 비율이 `0.85`에서 `1.15` 사이인 이미지를 정사각형으로 간주합니다. 정확한 1:1의 경우 `0.0`으로 설정하세요.

### 작동 방식

PlacePix는 초기 스캔 중(로컬 파일)과 백그라운드 메타데이터 스캔 중(S3 이미지)에 파일 헤더에서 이미지 크기를 읽습니다. 크기는 메모리에 저장되어 무작위 또는 시드 선택 전에 후보 풀을 필터링하는 데 사용됩니다. 방향이 요청되었지만 일치하는 이미지가 없으면 `404`가 반환됩니다.
## 필터 및 효과

쿼리 매개변수를 통해 모든 이미지에 실시간 필터와 효과를 적용하세요. 모든 처리는 서버 측에서 수행되며 후속 요청을 위해 캐싱됩니다.

### 색상 조정

```
?grayscale=1               # 흑백
?sepia=1                   # 따뜻한 세피아 톤
?tint=0ea5e9               # 16진수 색상 오버레이
?brightness=1.3            # 0.0에서 2.0
?contrast=1.2              # 0.0에서 2.0
?saturation=2.0            # 0.0에서 2.0
?invert=true               # 색상 반전
?posterize=4               # 색상 레벨(1-8)
?duotone=ff0000,0000ff     # 이중색 맵
```

### 이미지 효과

```
?blur=2                    # 가우시안 블러(1-10)
?sharpen=1.5               # 선명도 강도
?emboss=true               # 3D 릴리프
?edges=sobel               # 엣지 감지
?edges=canny               # Canny 엣지
?halftone=4                # 도트 패턴
?oil_painting=true         # 유화 스타일
?pencil_sketch=true        # 연필 스케치
?cartoon=true              # 만화 효과
?vignette=0.5              # 가장자리 어둡게(0-1)
```

### 오버레이 매개변수

```
?text=Hello+World          # 텍스트 오버레이
?border=4,ffffff           # 테두리 너비 및 색상
?watermark=1               # 구성된 워터마크 적용
?padding=20                # 내부 패딩
```

## 글자 아바타 생성기

모든 이름이나 이메일에서 결정론적 문자 기반 아바타를 생성하세요. 사용자 프로필 플레이스홀더, 댓글 시스템 및 팀 디렉토리에 완벽합니다. 각 이름은 항상 동일한 색상을 생성하므로 세션 간에 아바타가 일관됩니다.

### 엔드포인트

```
/avatar/{size}/{name}
/avatar/{size}/{name}.{ext}
```

### 매개변수

- `size` — 픽셀 크기(예: `64`, `128`, `256`)
- `name` — 모든 문자열; 아바타를 위해 첫 글자가 추출됨
- `circle` — 원 모양으로 자르기
- `border={width},{color}` — 테두리 추가
- `bg={hex}` — 배경색 재정의
- `fg={hex}` — 텍스트/전경색 재정의
- `single=true` — 첫 번째 글자만 사용
- `uppercase=false` — 소문자 보존
- `palette={name}` — `flatui`, `material`, `pastel` 또는 `neon` 중 선택

### 예제

```
# 간단한 128px 아바타
/avatar/128/John+Doe

# 사용자 지정 테두리가 있는 원형 아바타
/avatar/128/John+Doe?circle=true&border=2,ffffff

# 단일 이니셜, 파스텔 팔레트
/avatar/64/Alice?single=true&palette=pastel

# SVG 출력(확장 가능, 500바이트 미만)
/avatar/128/John+Doe.svg
```

### 왜 글자 아바타를 사용하나요?

- 제로 외부 종속성 — Gravatar 또는 서드파티 아바타 서비스 없음
- 결정론적 — 동일한 이름은 항상 동일한 색상을 생성
- SVG 지원 — 무한 확장 가능, HiDPI 디스플레이에 완벽
- 모든 브랜드 미학을 위한 4개의 내장 색상 팔레트

## REST API 퀵 레퍼런스

모든 엔드포인트는 CORS를 지원하고 장기 캐시 헤더가 있는 이미지를 반환합니다. Base64 JSON 출력은 작은 썸네일에 사용할 수 있습니다.

### 이미지 엔드포인트

- `GET /{width}/{height}/{category}` — 카테고리에서 랜덤 이미지
- `GET /{width}/{height}` — 모든 카테고리에서 랜덤 이미지
- `GET /id/{id}/{width}/{height}` — ID로 특정 이미지
- `GET /ratio/{ratio}/{width}/{category}` — 가로세로 비율 이미지
- `GET /preset/{preset}/{category}` — 소셜 미디어 프리셋
- `GET /color/{hex}/{width}/{height}` — 색상 일치 이미지
- `GET /gradient/{w}/{h}/{from}/{to}` — 그라데이션 이미지
- `GET /svg/{width}/{height}` — SVG 플레이스홀더
- `GET /avatar/{size}/{name}` — 글자 아바타(PNG/SVG)

### 메타데이터 엔드포인트

- `GET /api/images` — 카테고리 및 합계 나열
- `GET /api/info/id/{id}` — 이미지 메타데이터(치수, 색상, 형식)
- `GET /api/color/{hex}` — 색상과 일치하는 이미지

### 상태 엔드포인트

- `GET /health` — 활성 프로브(Docker/K8s)
- `GET /ready` — 준비 프로브(이미지가 로드될 때까지 503)

## 전문 지식 및 자격

- 2008년부터 오픈 소스 생태계에 적극적으로 기여
- 모든 코드는 MIT 라이선스 하에 오픈 소스이며 <a href="https://github.com/riadvice/placepix" target="_blank" class="text-accent hover:underline">GitHub</a>에서 감사 가능

## 자주 묻는 질문

### Docker로 PlacePix를 어떻게 배포하나요?

`docker run -d -p 3000:3000 -v ./images:/app/images riadvice/placepix:latest`를 실행하세요. 이미지 폴더를 마운트하면 서비스가 즉시 스마트 스캐닝이 활성화된 상태로 시작됩니다.

### 얼굴 인식 스마트 크롭이란 무엇인가?

PlacePix는 OpenCV Haar 캐스케이드를 사용하여 이미지에서 얼굴을 감지합니다. URL에 `?fit=smart`를 추가하면 기하학적 중심을 사용하는 대신 감지된 얼굴을 중심으로 하여 크롭 영역이 이동됩니다. 얼굴을 찾지 못하면 표준 중앙 크롭으로 폴백합니다.

### 사진을 업로드하지 않고 그라데이션 플레이스홀더 이미지를 생성할 수 있나요?

예. `/gradient/{width}/{height}/{from}/{to}` 엔드포인트는 URL 매개변수에서 완전히 그라데이션 이미지를 생성합니다. 업로드된 이미지가 필요하지 않습니다. `/svg/{width}/{height}`로 SVG 플레이스홀더도 생성할 수 있습니다.

### API를 통해 Instagram 스토리 크기 플레이스홀더 이미지를 어떻게 생성하나요?

프리셋 엔드포인트를 사용하세요: `/preset/instagram-story/{category}`. 1080x1920 이미지를 반환합니다. 최적화된 전달을 위해 `?format=webp&quality=70`를, 세로 안전 크롭을 위해 `?fit=smart`를 조합하세요.

### PlacePix는 S3 호환 객체 스토리지를 지원하나요?

예. PlacePix는 OVHcloud Object Storage, AWS S3, MinIO 및 모든 S3 호환 제공업체와 함께 작동합니다. 환경 변수를 통해 엔드포인트, 버킷, 액세스 키 및 비밀 키를 구성하세요.

### 어떤 출력 형식이 지원되나요?

WebP, AVIF, JPEG, PNG, SVG 및 base64 JSON. `.webp`, `.avif` 또는 `.png`를 파일 확장자로 사용하거나 `?format=webp`를 쿼리 매개변수로 추가하세요. AVIF는 가장 작은 파일을 생성합니다. PNG는 무손실입니다.

### PlacePix는 상업용으로 무료인가요?

예. PlacePix는 MIT 라이선스 하에 출시되었으며 개인 및 상업용으로 무료입니다. 자체 호스팅되므로 사용 제한, API 키, 요청당 과금이 없습니다.
