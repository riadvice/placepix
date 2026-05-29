---
title: PlacePix ডেভেলপার গাইড — স্ব-হোস্ট করা প্লেসহোল্ডার ইমেজ API এবং ফিচার রেফারেন্স
description: সম্পূর্ণ PlacePix ডেভেলপার গাইড এবং API রেফারেন্স। Docker ব্যবহার করে placeholder ইমেজ কীভাবে ডিপ্লয় করবেন, গ্রেডিয়েন্ট এবং SVG কীভাবে জেনারেট করবেন, এবং Instagram, YouTube এবং আরও অনেক কিছুর জন্য সোশ্যাল মিডিয়া প্রিসেট ব্যবহার করতে শিখুন।
keywords: সেলফ-হোস্টেড প্লেসহোল্ডার ইমেজ API, ফেস-অ্যাওয়ার ক্রপ প্লেসহোল্ডার, গ্রেডিয়েন্ট প্লেসহোল্ডার জেনারেটর, ডকার প্লেসহোল্ডার ইমেজ সার্ভিস, ইনস্টাগ্রাম স্টোরি প্লেসহোল্ডার API, SVG প্লেসহোল্ডার জেনারেটর, ডেভেলপার ইমেজ API
author: RIADVICE
robots: index, follow
og_title: PlacePix Developer Guide — Self-Hosted Placeholder Image API & Feature Reference
og_description: Complete developer guide covering Docker deployment, smart crop, gradient placeholders, SVG generation, and social media presets.
twitter_title: PlacePix Developer Guide — Self-Hosted Placeholder Image API & Feature Reference
twitter_description: Complete developer guide covering Docker deployment, smart crop, gradient placeholders, SVG generation, and social media presets.
jsonld_name: PlacePix Developer Guide — Self-Hosted Placeholder Image API & Feature Reference
jsonld_description: Complete developer guide and API reference for PlacePix, a self-hosted placeholder image service. Covers Docker deployment, face-aware smart crop, gradient placeholders, SVG generation, and social media presets.
jsonld_proficiency: Expert
jsonld_dependencies: Docker, Python 3.12, FastAPI
header_title: PlacePix ডেভেলপার গাইড
header_subtitle: স্ব-হোস্ট করা প্লেসহোল্ডার ইমেজ সার্ভিসের জন্য সম্পূর্ণ API রেফারেন্স এবং ফিচার ডকুমেন্টেশন। Docker ডিপ্লয়মেন্ট, স্মার্ট ক্রপ, গ্রেডিয়েন্ট প্লেসহোল্ডার, SVG জেনারেশন, লেটার অ্যাভাটার এবং সোশ্যাল মিডিয়া প্রিসেট কভার করে।
author_label: দ্বারা
updated_label: "Last updated: May 2026"
github_label: GitHub-এ ওপেন সোর্স
toc_title: বিষয়বস্তুর তালিকা
---

## PlacePix কী?

PlacePix হল **সেলফ-হোস্টেড প্লেসহোল্ডার ইমেজ সার্ভিস** যা ডেভেলপার এবং ডিজাইন টিমের জন্য তৈরি। তৃতীয় পক্ষের প্লেসহোল্ডার সার্ভিসের বিপরীতে যা বাহ্যিক নেটওয়ার্ক কল প্রয়োজন এবং অদৃশ্য হতে পারে, PlacePix সম্পূর্ণ আপনার নিজের ইনফ্রাস্ট্রাকচারে চলে। ফোল্ডারে ইমেজ ড্রপ করুন, এবং তাৎক্ষণিকভাবে URL এন্ডপয়েন্ট পান যা আকার পরিবর্তন, ফিল্টার এবং ফরম্যাট করা ইমেজ সরবরাহ করে।

সার্ভিসটি Python ব্যবহার করে FastAPI দিয়ে লেখা হয়েছে Pillow এবং OpenCV দ্বারা চালিত ইমেজ প্রসেসিং সহ। এটি Docker ডিপ্লয়মেন্ট এবং S3-সংগত অবজেক্ট স্টোরেজ সমর্থন করে।

### বৈশিষ্ট্য

- **শূন্য কনফিগারেশন** — ফোল্ডারে ইমেজ ড্রপ করুন এবং চলুন
- **ফেস-অ্যাওয়ার ক্রপিং** — OpenCV মুখ সনাক্ত করে এবং কেন্দ্র করে
- **গ্রেডিয়েন্ট এবং SVG প্লেসহোল্ডার** — কোনো ইমেজ প্রয়োজন নেই
- **সোশ্যাল মিডিয়া প্রিসেট** — Instagram, YouTube, TikTok সাইজ বিল্ট-ইন
- **কালার সার্চ** — আপনার ব্র্যান্ড প্যালেটের সাথে মিল এমন ইমেজ খুঁজুন
- **লেটার অ্যাভাটার** — নাম থেকে নির্ধারণমূলক প্রোফাইল ইমেজ

## Docker ডিপ্লয়মেন্ট গাইড

PlacePix চালানোর সবচেয়ে দ্রুত উপায় হল Docker। একটি একক কমান্ড সম্পূর্ণ সার্ভিস ডিপ্লয় করে স্মার্ট স্ক্যানিং, কালার এক্সট্রাকশন এবং এমবেডেড URL বিল্ডার সহ।

### এক-লাইন ডিপ্লয়মেন্ট

```bash
docker run -d -p 3000:3000 \
  -v ./images:/app/images \
  riadvice/placepix:latest
```

### Docker Compose (সুপারিশকৃত)

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

### স্থায়ী ডেটা এবং এনভায়রনমেন্ট

কন্টেইনার রিস্টার্টের মধ্যে অবস্থা সংরক্ষণ করতে `/app/images` (আপনার ইমেজ লাইব্রেরি) এবং `/app/data` (স্ক্যান ক্যাশ এবং মেটাডেটা) উভয়ই মাউন্ট করুন। পরিবেশ ভেরিয়েবল বা `.env` ফাইলের মাধ্যমে আচরণ কনফিগার করুন।

### OVHcloud S3-সংগত স্টোরেজ

PlacePix যেকোনো S3-সংগত ব্যাকএন্ড সমর্থন করে। OVHcloud Object Storage-এর জন্য, সেট করুন:

```
S3_ENABLED=true
S3_ENDPOINT=https://s3.rbx.io.cloud.ovh.net
S3_ACCESS_KEY=your-key
S3_SECRET_KEY=your-secret
S3_BUCKET=your-bucket
S3_REGION=rbx
```

## ফেস-অ্যাওয়ার স্মার্ট ক্রপিং

পোর্ট্রেট ফটোগ্রাফিতে স্ট্যান্ডার্ড সেন্টার ক্রপিং মুখ কাটতে পারে। PlacePix এটি OpenCV Haar ক্যাসকেড দ্বারা চালিত **ফেস-অ্যাওয়ার স্মার্ট ক্রপিং** দিয়ে সমাধান করে।

### কীভাবে এটি কাজ করে

যখন একটি অনুরোধে `?fit=smart` অন্তর্ভুক্ত থাকে, PlacePix OpenCV ব্যবহার করে ছবিতে মানব মুখের জন্য স্ক্যান করে। যদি মুখ সনাক্ত হয়, তবে ক্রপ উইন্ডোটি সরিয়ে নেওয়া হয় যাতে মুখের কেন্দ্রবিন্দু গোল্ডেন-রেশিও ইন্টারসেকশন পয়েন্টগুলির যতটা সম্ভব কাছাকাছি থাকে। যদি কোনো মুখ না পাওয়া যায়, তবে এটি স্ট্যান্ডার্ড সেন্টার ক্রপিং-এ ফিরে আসে।

### API উদাহরণ

```
# ফেস-অ্যাওয়ার ক্রপ (মুখ সনাক্ত করে এবং কেন্দ্র করে)
/400/300/people?fit=smart

# স্ট্যান্ডার্ড সেন্টার ক্রপ
/400/300/people?fit=crop

# কভার ফিল (প্রসারিত হতে পারে)
/400/300/people?fit=cover

# কন্টেইন (লেটারবক্সিং)
/400/300/people?fit=contain
```

### কখন স্মার্ট ক্রপ ব্যবহার করবেন

- পোর্ট্রেট ফটোগ্রাফি এবং হেডশট
- টিম পেজ যেখানে মুখগুলি ম্যাটার করে
- সোশ্যাল মিডিয়া থাম্বনেইল
- যে কোনো পরিস্থিতি যেখানে জ্যামিতিক কেন্দ্র ক্রপিং কম্পোজিশন নষ্ট করে

## গ্রেডিয়েন্ট প্লেসহোল্ডার API

কোনো asset আপলোড না করেই on-the-fly লিনিয়ার এবং রেডিয়াল গ্রেডিয়েন্ট ইমেজ তৈরি করুন। Hero backgrounds, loading states, এবং design mockups-এর জন্য নিখুঁত।

### এন্ডপয়েন্ট সিনট্যাক্স

```
/gradient/{width}/{height}/{from_hex}/{to_hex}
```

### উদাহরণ

```
# সাধারণ লিনিয়ার গ্রেডিয়েন্ট (উপর থেকে নীচে)
/gradient/800/400/3b82f6/10b981

# 45-ডিগ্রি কোণ গ্রেডিয়েন্ট
/gradient/800/400/e11d48/f59e0b?angle=45

# কেন্দ্র থেকে রেডিয়াল গ্রেডিয়েন্ট
/gradient/800/400/1e293b/64748b?gradient_type=radial

# আউটপুট ফরম্যাট সহ
/gradient/800/400/0ea5e9/ffffff?format=webp&quality=80
```

### প্যারামিটার রেফারেন্স

- `{from_hex}` / `{to_hex}` — # প্রিফিক্স ছাড়া hex রং
- `?angle=45` — ডিগ্রিতে লিনিয়ার অ্যাঙ্গেল (0-360)
- `?gradient_type=radial` — রেডিয়াল গ্রেডিয়েন্টে পরিবর্তন করে
- `?format=webp` — WebP আউটপুট (ছোট ফাইল সাইজ)

## SVG প্লেসহোল্ডার জেনারেটর

SVG প্লেসহোল্ডারগুলির জন্য কোনো সার্ভার-সাইড ইমেজ প্রসেসিং প্রয়োজন হয় না। সেগুলি কাস্টমাইজযোগ্য ব্যাকগ্রাউন্ড রঙ, ফোরগ্রাউন্ড রঙ এবং টেক্সট লেবেল সহ ইনলাইন SVG হিসাবে তৈরি হয়।

### এন্ডপয়েন্ট

```
/svg/{width}/{height}?bg={hex}&fg={hex}&text={label}
```

### উদাহরণ

```
# ডিফল্ট ওয়্যারফ্রেম প্লেসহোল্ডার
/svg/400/300

# কাস্টম ব্র্যান্ড রঙ
/svg/400/300?bg=1c1917&fg=0ea5e9

# কাস্টম টেক্সট সহ
/svg/400/300?bg=0ea5e9&fg=ffffff&text=Hero+Section
```

### কেন SVG?

- ফাইল সাইজ ৫০০ বাইটের কম
- গুণগত মানের ক্ষতি ছাড়া অসীমভাবে স্কেলেবল
- শূন্য সার্ভার প্রসেসিং ওভারহেড
- ওয়্যারফ্রেম এবং কম-ফিডেলিটি প্রোটোটাইপের জন্য নিখুঁত

## সোশ্যাল মিডিয়া প্রিসেট

PlacePix জনপ্রিয় সোশ্যাল প্ল্যাটফর্ম এবং স্ক্রিন সাইজের জন্য পূর্বনির্ধারিত ডাইমেনশন অন্তর্ভুক্ত করে। Instagram, YouTube, TikTok, LinkedIn, X (Twitter) এবং স্ট্যান্ডার্ড ডিসপ্লেতে জন্য নিখুঁত সাইজের প্লেসহোল্ডার ইমেজ তৈরি করতে এগুলি ব্যবহার করুন।

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

### স্ক্রিন সাইজ

```
/preset/mobile/nature              # 375x812
/preset/tablet/nature              # 768x1024
/preset/desktop/nature             # 1920x1080
/preset/4k/nature                  # 3840x2160
```

### দীর্ঘ-লেজ ব্যবহারের ক্ষেত্র: Instagram Story API

আপনি যদি একটি সোশ্যাল মিডিয়া ম্যানেজমেন্ট টুল তৈরি করছেন এবং **Instagram story সাইজের placeholder ইমেজ** প্রয়োজন, তবে `/preset/instagram-story/{category}` ব্যবহার করুন। পোর্ট্রেট ফটোর জন্য `?fit=smart` এবং অপ্টিমাইজড ডেলিভারির জন্য `?format=webp&quality=70` এর সাথে সংমিশ্রণ করুন।


## অরিয়েন্টেশন ফিল্টারিং

নির্বাচনের আগে ছবির নেটিভ অ্যাসপেক্ট রেশিও অনুযায়ী এলোমেলো ছবি ফিল্টার করুন। এটি তখনই উপযোগী যখন আপনার এমন ছবি প্রয়োজন যা স্বাভাবিকভাবে একটি লেআউটে ফিট করে — হেডারের জন্য ল্যান্ডস্কেপ, কার্ডের জন্য পোর্ট্রেট, বা থাম্বনেইলের জন্য স্কয়ার।

### এন্ডপয়েন্ট

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

### কনফিগারেশন

`squarish` সহনশীলতা `ORIENTATION_SQUARISH_TOLERANCE` এনভায়রনমেন্ট ভেরিয়েবলের মাধ্যমে কনফিগারযোগ্য (ডিফল্ট: `0.15`)। `0.15` মান মানে অ্যাসপেক্ট রেশিও `0.85` থেকে `1.15` এর মধ্যে ছবিগুলোকে স্কয়ার বলে বিবেচনা করা হয়। কেবলমাত্র 1:1 এর জন্য `0.0` সেট করুন।

### কীভাবে কাজ করে

PlacePix প্রাথমিক স্ক্যানের সময় (স্থানীয় ফাইল) এবং ব্যাকগ্রাউন্ড মেটাডেটা স্ক্যানের সময় (S3 ছবি) ফাইল হেডার থেকে ছবির মাত্রা পড়ে। মাত্রাগুলো মেমরিতে সংরক্ষণ করা হয় এবং এলোমেলো বা নির্ধারিত নির্বাচনের আগে প্রার্থী পুল ফিল্টার করতে ব্যবহার করা হয়। অরিয়েন্টেশন অনুরোধ করা হলে কিন্তু কোনো মিলছে না, একটি `404` ফেরত দেওয়া হয়।

## কালার সার্চ API

PlacePix-এ প্রতিটি ইমেজ তার শীর্ষ 3টি প্রভাবশালী রঙের জন্য স্ক্যান করা হয়। আপনার ব্র্যান্ড প্যালেটের সাথে মিল এমন ইমেজ খুঁজে পেতে আপনি পুরো লাইব্রেরি hex রঙ দ্বারা অনুসন্ধান করতে পারেন।

### এন্ডপয়েন্ট

```
# একটি নির্দিষ্ট hex রঙের সাথে মিল এমন একটি ইমেজ পান
/color/0ea5e9/400/300

# যেকোনো এন্ডপয়েন্ট প্রভাবশালী রঙ অনুযায়ী ফিল্টার করুন
/400/300/nature?color=d97706

# একটি রঙের সাথে মিল এমন সমস্ত ইমেজের তালিকা দেখুন
/api/color/3b82f6
```

### কালার স্ক্যানিং কীভাবে কাজ করে

চালু হওয়ার সময়, PlacePix LAB কালার স্পেসে k-means ক্লাস্টারিং ব্যবহার করে প্রতিটি ইমেজ থেকে সবচেয়ে ঘন ঘন ব্যবহৃত রং বের করে। এটি কাঁচা RGB গড়ের পরিবর্তে উপলব্ধিগতভাবে সঠিক মিল তৈরি করে। প্যালেট পেজ (`/palette`) এই রংগুলি ভিজুয়ালাইজ করে এবং আপনাকে hue ক্যাটেগরি অনুযায়ী ব্রাউজ করতে দেয়।

## ফিল্টার এবং এফেক্ট

query প্যারামিটারের মাধ্যমে যেকোনো ইমেজে real-time ফিল্টার এবং এফেক্ট প্রয়োগ করুন। সমস্ত প্রসেসিং সার্ভার-সাইডে সম্পন্ন হয় এবং পরবর্তী অনুরোধের জন্য ক্যাশে করা হয়।

### কালার অ্যাডজাস্টমেন্ট

```
?grayscale=1               # কালো ও সাদা
?sepia=1                   # উষ্ণ সেপিয়া টোন
?tint=0ea5e9               # হেক্স রঙ ওভারলে
?brightness=1.3            # 0.0 থেকে 2.0
?contrast=1.2              # 0.0 থেকে 2.0
?saturation=2.0            # 0.0 থেকে 2.0
?invert=true               # রঙ উল্টান
?posterize=4               # রঙের স্তর (1-8)
?duotone=ff0000,0000ff     # দ্বি-রঙের মানচিত্র
```

### ইমেজ এফেক্ট

```
?blur=2                    # গাউসিয়ান ব্লার (1-10)
?sharpen=1.5               # শার্পেন পরিমাণ
?emboss=true               # 3D রিলিফ
?edges=sobel               # এজ ডিটেকশন
?edges=canny               # ক্যানি এজ
?halftone=4                # ডট প্যাটার্ন
?oil_painting=true         # তৈলচিত্র স্টাইল
?pencil_sketch=true        # পেন্সিল স্কেচ
?cartoon=true              # কার্টুন এফেক্ট
?vignette=0.5              # প্রান্ত অন্ধকার (0-1)
```

### ওভারলে প্যারামিটার

```
?text=Hello+World          # টেক্সট ওভারলে
?border=4,ffffff           # বর্ডার প্রস্থ এবং রঙ
?watermark=1               # কনফিগারড ওয়াটারমার্ক প্রয়োগ করুন
?padding=20                # অভ্যন্তরীণ প্যাডিং
```

## অবতার জেনারেটর

যেকোনো নাম বা ইমেইল থেকে নির্ধারণমূলক অবতার তৈরি করুন। PlacePix দুটি ধরনের অবতার সমর্থন করে: **অক্ষর অবতার** (রঙিন প্রথম অক্ষর) এবং **Multiavatar** (বহুসাংস্কৃতিক ভেক্টর অবতার)।

### এন্ডপয়েন্ট

```
/avatar/{size}/{name}
/avatar/{size}/{name}.{ext}
```

### প্যারামিটার

- `type` — avatar type: `letter` (default) or `multiavatar`
- `size` — pixel size (e.g. `64`, `128`, `256`)
- `name` — any string; used as seed for the avatar

#### অক্ষর অবতার (`type=letter`)

- `circle` — crop to a circle shape
- `border={width}` — বর্ডার যোগ করুন
- `border_color={hex}` — বর্ডারের রঙ
- `bg={hex}` — override background color
- `fg={hex}` — override text/foreground color
- `single=true` — use only the first letter
- `uppercase=false` — preserve lowercase letters
- `palette={name}` — choose from `flatui`, `material`, `pastel`, `neon`, `cool`, `warm`

#### Multiavatar (`type=multiavatar`)

- `env` — include environment background (`true` by default, `false` to omit)
- `part` — specific part code (optional, e.g. `11`)
- `theme` — specific theme code (optional, e.g. `C`)

### উদাহরণ

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

### অক্ষর অবতার কেন ব্যবহার করবেন?

- শূন্য বাহ্যিক নির্ভরশীলতা — কোনো Gravatar বা তৃতীয় পক্ষের অবতার সেবা নেই
- নির্ধারণমূলক — একই নাম সর্বদা একই রঙ তৈরি করে
- SVG সমর্থন — অসীমভাবে স্কেলযোগ্য, HiDPI ডিসপ্লের জন্য নিখুঁত
- যেকোনো ব্র্যান্ড এসথেটিকের জন্য ছয়টি অন্তর্নির্মিত রঙের প্যালেট

### Multiavatar কেন ব্যবহার করবেন?

- 12 বিলিয়ন অনন্য বহুসাংস্কৃতিক অবতার
- নির্ধারণমূলক — একই নাম সর্বদা একই অবতার তৈরি করে
- পিউর SVG আউটপুট — ছোট ফাইল সাইজ, অসীমভাবে স্কেলযোগ্য
- কোনো বাহ্যিক API কলের প্রয়োজন নেই

## REST API কুইক রেফারেন্স

সমস্ত এন্ডপয়েন্ট CORS সমর্থন করে এবং দীর্ঘমেয়াদী ক্যাশে হেডার সহ ইমেজ রিটার্ন করে। ছোট থাম্বনেইলের জন্য Base64 JSON আউটপুট উপলব্ধ।

### ইমেজ এন্ডপয়েন্ট

- `GET /{width}/{height}/{category}` — ক্যাটেগরি থেকে র্যান্ডম ইমেজ
- `GET /{width}/{height}` — সব ক্যাটেগরি থেকে র্যান্ডম ইমেজ
- `GET /id/{id}/{width}/{height}` — আইডি অনুযায়ী নির্দিষ্ট ইমেজ
- `GET /ratio/{ratio}/{width}/{category}` — অ্যাস্পেক্ট রেশিও ইমেজ
- `GET /preset/{preset}/{category}` — সোশ্যাল মিডিয়া প্রিসেট
- `GET /color/{hex}/{width}/{height}` — রঙ-ম্যাচড ইমেজ
- `GET /gradient/{w}/{h}/{from}/{to}` — গ্রেডিয়েন্ট ইমেজ
- `GET /svg/{width}/{height}` — SVG প্লেসহোল্ডার
- `GET /avatar/{size}/{name}` — লেটার অ্যাভাটার (PNG/SVG)

### মেটাডেটা এন্ডপয়েন্ট

- `GET /api/images` — ক্যাটেগরি এবং মোট তালিকা
- `GET /api/info/id/{id}` — ইমেজ মেটাডেটা (ডাইমেনশন, রঙ, ফরম্যাট)
- `GET /api/color/{hex}` — একটি রঙের সাথে ম্যাচ করা ইমেজ

### হেলথ এন্ডপয়েন্ট

- `GET /health` — লাইভনেস প্রোব (Docker/K8s)
- `GET /ready` — রেডিনেস প্রোব (ইমেজ লোড না হওয়া পর্যন্ত 503)

## দক্ষতা ও প্রমাণপত্র

- 2008 সাল থেকে ওপেন-সোর্স ইকোসিস্টেমে সক্রিয় অবদানকারী
- সমস্ত কোড MIT লাইসেন্সের অধীনে ওপেন সোর্স এবং <a href="https://github.com/riadvice/placepix" target="_blank" class="text-accent hover:underline">GitHub</a>-ে অডিটযোগ্য

## সাধারণ প্রশ্নাবলী

### কীভাবে Docker দিয়ে PlacePix ডিপ্লয় করব?

`docker run -d -p 3000:3000 -v ./images:/app/images riadvice/placepix:latest` চালান। আপনার ইমেজ ফোল্ডার মাউন্ট করুন এবং সার্ভিস স্মার্ট স্ক্যানিং সক্ষম নিয়ে তাৎক্ষণিকভাবে শুরু হয়।

### ফেস-অ্যাওয়ার স্মার্ট ক্রপিং কী?

PlacePix ইমেজে মুখ সনাক্ত করতে OpenCV Haar ক্যাসকেড ব্যবহার করে। যখন আপনি যেকোনো URL-এ `?fit=smart` যোগ করেন, জ্যামিতিক কেন্দ্র ব্যবহার করার পরিবর্তে সনাক্ত মুখের কেন্দ্রে ক্রপ অঞ্চল স্থানান্তরিত হয়। যদি কোনো মুখ না পাওয়া যায়, এটি স্ট্যান্ডার্ড সেন্টার ক্রপিং-এ ফিরে আসে।

### আমি কি কোনো ছবি আপলোড না করে গ্রেডিয়েন্ট প্লেসহোল্ডার ইমেজ তৈরি করতে পারি?

হ্যাঁ। `/gradient/{width}/{height}/{from}/{to}` এন্ডপয়েন্ট সম্পূর্ণ URL প্যারামিটার থেকে গ্রেডিয়েন্ট ইমেজ তৈরি করে। কোনো আপলোড করা ইমেজ প্রয়োজন নেই। আপনি `/svg/{width}/{height}` দিয়ে SVG প্লেসহোল্ডারও তৈরি করতে পারেন।

### API এর মাধ্যমে আমি কীভাবে Instagram story সাইজের প্লেসহোল্ডার ইমেজ তৈরি করব?

প্রিসেট এন্ডপয়েন্ট ব্যবহার করুন: `/preset/instagram-story/{category}`। এটি একটি 1080x1920 ইমেজ রিটার্ন করে। অপ্টিমাইজড ডেলিভারির জন্য `?format=webp&quality=70` এবং পোর্ট্রেট-সেফ ক্রপিংয়ের জন্য `?fit=smart` এর সাথে সংমিশ্রণ করুন।

### PlacePix কি S3-সংগত অবজেক্ট স্টোরেজ সমর্থন করে?

হ্যাঁ। PlacePix OVHcloud Object Storage, AWS S3, MinIO এবং যেকোনো S3-সংগত প্রোভাইডারের সাথে কাজ করে। এনভায়রনমেন্ট ভেরিয়েবলের মাধ্যমে এন্ডপয়েন্ট, বাকেট, অ্যাক্সেস কী এবং সিক্রেট কী কনফিগার করুন।

### কোন আউটপুট ফরম্যাটগুলি সমর্থিত?

WebP, AVIF, JPEG, PNG, SVG এবং base64 JSON। ফাইল এক্সটেনশন হিসাবে `.webp`, `.avif`, বা `.png` ব্যবহার করুন, বা ক্যুয়েরি প্যারামিটার হিসাবে `?format=webp` যোগ করুন। AVIF সবচেয়ে ছোট ফাইল তৈরি করে; PNG হল লসলেস।

### PlacePix কি বাণিজ্যিক ব্যবহারের জন্য বিনামূল্যে?

হ্যাঁ। PlacePix MIT লাইসেন্সের অধীনে রিলিজ করা হয়েছে এবং ব্যক্তিগত ও বাণিজ্যিক উভয় ব্যবহারের জন্য বিনামূল্যে। এটি স্ব-হোস্টেড হওয়ায়, কোনো ব্যবহার সীমা, কোনো API কী এবং কোনো প্রতি-অনুরোধ বিলিং নেই।