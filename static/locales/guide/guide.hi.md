---
title: PlacePix डेवलपर गाइड — सेल्फ-होस्टेड प्लेसहोल्डर इमेज API और फीचर रेफरेंस
description: पूर्ण PlacePix डेवलपर गाइड और API रेफरेंस। सीखें कि Docker के साथ प्लेसहोल्डर छवियों को कैसे डिप्लॉय करें, ग्रेडिएंट और SVG कैसे जनरेट करें, और Instagram, YouTube और अन्य के लिए सोशल मीडिया प्रीसेट का उपयोग कैसे करें।
keywords: स्वयं-होस्टित प्लेसहोल्डर छवि API, फेस-अवेयर क्रॉप प्लेसहोल्डर, ग्रेडिएंट प्लेसहोल्डर जनरेटर, Docker प्लेसहोल्डर छवि सेवा, Instagram स्टोरी प्लेसहोल्डर API, SVG प्लेसहोल्डर जनरेटर, डेवलपर छवि API
author: RIADVICE
robots: index, follow
og_title: PlacePix डेवलपर गाइड — सेल्फ-होस्टेड प्लेसहोल्डर इमेज API और फीचर रेफरेंस
og_description: पूर्ण डेवलपर गाइड जिसमें Docker डिप्लॉयमेंट, स्मार्ट क्रॉप, ग्रेडिएंट प्लेसहोल्डर, SVG जनरेशन और सोशल मीडिया प्रीसेट शामिल हैं।
twitter_title: PlacePix डेवलपर गाइड — सेल्फ-होस्टेड प्लेसहोल्डर इमेज API और फीचर रेफरेंस
twitter_description: पूर्ण डेवलपर गाइड जिसमें Docker डिप्लॉयमेंट, स्मार्ट क्रॉप, ग्रेडिएंट प्लेसहोल्डर, SVG जनरेशन और सोशल मीडिया प्रीसेट शामिल हैं।
jsonld_name: PlacePix डेवलपर गाइड — सेल्फ-होस्टेड प्लेसहोल्डर इमेज API और फीचर रेफरेंस
jsonld_description: PlacePix के लिए पूर्ण डेवलपर गाइड और API रेफरेंस, एक सेल्फ-होस्टेड प्लेसहोल्डर इमेज सेवा। Docker डिप्लॉयमेंट, फेस-अवेयर स्मार्ट क्रॉप, ग्रेडिएंट प्लेसहोल्डर, SVG जनरेशन और सोशल मीडिया प्रीसेट कवर करता है।
jsonld_proficiency: Expert
jsonld_dependencies: Docker, Python 3.12, FastAPI
header_title: PlacePix डेवलपर गाइड
header_subtitle: सेल्फ-होस्टेड प्लेसहोल्डर इमेज सेवा के लिए पूर्ण API रेफरेंस और फीचर डॉक्यूमेंटेशन। Docker डिप्लॉयमेंट, स्मार्ट क्रॉप, ग्रेडिएंट प्लेसहोल्डर, SVG जनरेशन, लेटर अवतार और सोशल मीडिया प्रीसेट कवर करता है।
author_label: द्वारा
updated_label: "अंतिम अपडेट: मई 2026"
github_label: GitHub पर ओपन सोर्स
toc_title: विषय सूची
---

## PlacePix क्या है?

PlacePix एक **सेल्फ-होस्टेड प्लेसहोल्डर इमेज सेवा** है जो डेवलपर्स और डिजाइन टीमों के लिए बनाई गई है। थर्ड-पार्टी प्लेसहोल्डर सेवाओं के विपरीत जो बाहरी नेटवर्क कॉल्स की आवश्यकता होती है और गायब हो सकती हैं, PlacePix पूरी तरह से आपके अपने इंफ्रास्ट्रक्चर पर चलती है। फ़ोल्डर में इमेज डालें, और तुरंत URL एंडपॉइंट्स प्राप्त करें जो resized, filtered और formatted इमेज सर्व करते हैं।

यह सेवा Python में FastAPI का उपयोग करके लिखी गई है, Pillow और OpenCV द्वारा पावर्ड इमेज प्रोसेसिंग के साथ। यह Docker डिप्लॉयमेंट और S3-कम्पैटिबल ऑब्जेक्ट स्टोरेज का समर्थन करती है।

### विशेषताएँ

- **ज़ीरो कॉन्फ़िगरेशन** — फ़ोल्डर में इमेज डालें और जाएं
- **फेस-अवेयर क्रॉपिंग** — OpenCV चेहरे का पता लगाता है और केंद्रित करता है
- **ग्रेडिएंट और SVG प्लेसहोल्डर** — कोई इमेज नहीं चाहिए
- **सोशल मीडिया प्रीसेट** — Instagram, YouTube, TikTok साइज़ built-in
- **कलर सर्च** — अपने ब्रांड पैलेट से मैच करती इमेज खोजें
- **लेटर अवतार** — नामों से निर्धारित प्रोफाइल इमेज

## Docker डिप्लॉयमेंट गाइड

PlacePix चलाने का सबसे तेज़ तरीका Docker के साथ है। एक कमांड पूरी सेवा को डिप्लॉय करता है जिसमें स्मार्ट स्कैनिंग, कलर एक्सट्रैक्शन और एम्बेडेड URL बिल्डर शामिल है।

### एक-पंक्ति डिप्लॉयमेंट

```bash
docker run -d -p 3000:3000 \
  -v ./images:/app/images \
  riadvice/placepix:latest
```

### Docker Compose (अनुशंसित)

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

### स्थायी डेटा और पर्यावरण

Container restarts में स्थिति संरक्षित करने के लिए `/app/images` (आपकी image library) और `/app/data` (scan cache और metadata) दोनों को mount करें। Environment variables या `.env` file के माध्यम से व्यवहार configure करें।

### OVHcloud S3-संगत स्टोरेज

PlacePix किसी भी S3-compatible backend का समर्थन करता है। OVHcloud Object Storage के लिए, set करें:

```
S3_ENABLED=true
S3_ENDPOINT=https://s3.rbx.io.cloud.ovh.net
S3_ACCESS_KEY=your-key
S3_SECRET_KEY=your-secret
S3_BUCKET=your-bucket
S3_REGION=rbx
```

## फेस-अवेयर स्मार्ट क्रॉपिंग

स्टैंडर्ड सेंटर क्रॉपिंग पोर्ट्रेट फोटोग्राफी में चेहरों को काट सकता है। PlacePix इसे OpenCV Haar cascades द्वारा संचालित **फेस-अवेयर स्मार्ट क्रॉपिंग** के साथ हल करता है।

### यह कैसे काम करता है

जब एक request में `?fit=smart` शामिल होता है, PlacePix OpenCV का उपयोग करके image को मानव चेहरों के लिए scan करता है। यदि चेहरे detected होते हैं, तो crop window को shift किया जाता है ताकि face centroid golden-ratio intersection points के यथासंभव करीब हो। यदि कोई चेहरा नहीं मिलता है, तो यह standard center cropping पर वापस आ जाता है।

### API उदाहरण

```
# Face-aware crop (चेहरों का पता लगाता है और केंद्रित करता है)
/400/300/people?fit=smart

# Standard center crop
/400/300/people?fit=crop

# Cover fill (stretch हो सकता है)
/400/300/people?fit=cover

# Contain (letterboxing)
/400/300/people?fit=contain
```

### स्मार्ट क्रॉप कब उपयोग करें

- पोर्ट्रेट फोटोग्राफी और हेडशॉट्स
- टीम पेज जहाँ चेहरे मायने रखते हैं
- सोशल मीडिया थंबनेल्स
- कोई भी परिदृश्य जहाँ ज्यामितीय सेंटर क्रॉपिंग कॉम्पोज़िशन बिगाड़ देता है

## ग्रेडिएंट प्लेसहोल्डर API

बिना किसी assets को upload किए on-the-fly linear और radial gradient images जनरेट करें। Hero backgrounds, loading states, और design mockups के लिए perfect।

### एंडपॉइंट सिंटैक्स

```
/gradient/{width}/{height}/{from_hex}/{to_hex}
```

### उदाहरण

```
# सरल linear gradient (ऊपर से नीचे)
/gradient/800/400/3b82f6/10b981

# 45-degree angled gradient
/gradient/800/400/e11d48/f59e0b?angle=45

# केंद्र से radial gradient
/gradient/800/400/1e293b/64748b?gradient_type=radial

# Output format के साथ
/gradient/800/400/0ea5e9/ffffff?format=webp&quality=80
```

### पैरामीटर संदर्भ

- `{from_hex}` / `{to_hex}` — # प्रिफिक्स के बिना hex रंग
- `?angle=45` — डिग्री में linear angle (0-360)
- `?gradient_type=radial` — radial gradient पर switch करता है
- `?format=webp` — WebP output (छोटा file size)

## SVG प्लेसहोल्डर जनरेटर

SVG placeholders के लिए कोई server-side image processing की आवश्यकता नहीं है। वे customizable background color, foreground color और text label के साथ inline SVG के रूप में generated होते हैं।

### एंडपॉइंट

```
/svg/{width}/{height}?bg={hex}&fg={hex}&text={label}
```

### उदाहरण

```
# Default wireframe placeholder
/svg/400/300

# Custom brand colors
/svg/400/300?bg=1c1917&fg=0ea5e9

# Custom text के साथ
/svg/400/300?bg=0ea5e9&fg=ffffff&text=Hero+Section
```

### SVG क्यों?

- File size 500 bytes से कम
- Quality loss के बिना infinitely scalable
- Zero server processing overhead
- Wireframes और low-fidelity prototypes के लिए perfect

## सोशल मीडिया प्रीसेट

PlacePix में popular social platforms और screen sizes के लिए predefined dimensions शामिल हैं। Instagram, YouTube, TikTok, LinkedIn, X (Twitter) और standard displays के लिए perfectly-sized placeholder images generate करने के लिए इनका उपयोग करें।

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

### स्क्रीन साइज़

```
/preset/mobile/nature              # 375x812
/preset/tablet/nature              # 768x1024
/preset/desktop/nature             # 1920x1080
/preset/4k/nature                  # 3840x2160
```

### लॉन्ग-टेल उपयोग का मामला: Instagram Story API

यदि आप एक सोशल मीडिया मैनेजमेंट टूल बना रहे हैं और आपको **Instagram story साइज़ placeholder इमेज** की आवश्यकता है, तो `/preset/instagram-story/{category}` का उपयोग करें। पोर्ट्रेट फोटो के लिए `?fit=smart` के साथ संयोजित करें और ऑप्टिमाइज्ड डिलीवरी के लिए `?format=webp&quality=70`।

## कलर सर्च API

PlacePix में हर इमेज को उसके शीर्ष 3 प्रभावी रंगों के लिए स्कैन किया जाता है। आप अपने ब्रांड पैलेट से मैच करती इमेज खोजने के लिए hex color द्वारा पूरी लाइब्रेरी खोज सकते हैं।

### एंडपॉइंट्स

```
# Get an image matching a specific hex color
/color/0ea5e9/400/300

# Filter any endpoint by dominant color
/400/300/nature?color=d97706

# List all images matching a color
/api/color/3b82f6
```

### How Color Scanning Works

स्टार्टअप पर, PlacePix LAB कलर स्पेस में k-means clustering का उपयोग करके प्रत्येक इमेज से सबसे अधिक बार आने वाले रंगों को निकालता है। यह raw RGB औसतों के बजाय perceptually सटीक मिलान उत्पन्न करता है। पैलेट पेज (`/palette`) इन रंगों को visualize करता है और hue श्रेणी के अनुसार ब्राउज़ करने देता है।

## फिल्टर और प्रभाव

query parameters के माध्यम से किसी भी इमेज पर real-time फिल्टर और प्रभाव लागू करें। सभी प्रोसेसिंग server-side की जाती है और बाद के अनुरोधों के लिए cached होती है।

### रंग समायोजन

```
?grayscale=1               # Black & white
?sepia=1                   # गर्म sepia tone
?tint=0ea5e9               # Hex color overlay
?brightness=1.3            # 0.0 से 2.0
?contrast=1.2              # 0.0 से 2.0
?saturation=2.0            # 0.0 से 2.0
?invert=true               # Invert colors
?posterize=4               # रंग स्तर (1-8)
?duotone=ff0000,0000ff     # दो-रंग मानचित्र
```

### इमेज प्रभाव

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

### Overlay Parameters

```
?text=Hello+World          # Text overlay
?border=4,ffffff           # Border width & color
?watermark=1               # Apply configured watermark
?padding=20                # Internal padding
```

## लेटर अवतार जनरेटर

किसी भी नाम या ईमेल से deterministic letter-based avatars जनरेट करें। यूज़र प्रोफाइल placeholders, कमेंट सिस्टम और टीम डायरेक्टरी के लिए परफेक्ट। हर नाम हमेशा एक ही रंग उत्पन्न करता है, इसलिए avatars सत्रों में सुसंगत होते हैं।

### एंडपॉइंट

```
/avatar/{size}/{name}
/avatar/{size}/{name}.{ext}
```

### Parameters

- `size` — pixel size (e.g. `64`, `128`, `256`)
- `name` — any string; first letters are extracted for the avatar
- `circle` — crop to a circle shape
- `border={width},{color}` — add a border
- `bg={hex}` — override background color
- `fg={hex}` — override text/foreground color
- `single=true` — use only the first letter
- `uppercase=false` — preserve lowercase letters
- `palette={name}` — choose from `flatui`, `material`, `pastel`, or `neon`

### उदाहरण

```
# सरल 128px अवतार
/avatar/128/John+Doe

# कस्टम बॉर्डर के साथ सर्कल अवतार
/avatar/128/John+Doe?circle=true&border=2,ffffff

# सिंगल initial, पेस्टेल पैलेट
/avatar/64/Alice?single=true&palette=pastel

# SVG आउटपुट (स्केलेबल, 500 बाइट से कम)
/avatar/128/John+Doe.svg
```

### लेटर अवतार क्यों उपयोग करें?

- शून्य बाहरी निर्भरता — कोई Gravatar या तृतीय-पक्ष अवतार सेवा नहीं
- निर्धारित — समान नाम हमेशा समान रंग उत्पन्न करता है
- SVG समर्थन — अनंत स्केलेबल, HiDPI डिस्प्ले के लिए परफेक्ट
- किसी भी ब्रांड सौंदर्यशास्त्र के लिए चार बuilt-in कलर पैलेट

## REST API क्विक रेफरेंस

सभी endpoints CORS का समर्थन करते हैं और दीर्घकालिक कैश हेडर के साथ इमेज लौटाते हैं। छोटे thumbnails के लिए Base64 JSON आउटपुट उपलब्ध है।

### इमेज एंडपॉइंट्स

- `GET /{width}/{height}/{category}` — श्रेणी से यादृच्छिक इमेज
- `GET /{width}/{height}` — सभी श्रेणियों से यादृच्छिक इमेज
- `GET /id/{id}/{width}/{height}` — ID द्वारा विशिष्ट इमेज
- `GET /ratio/{ratio}/{width}/{category}` — पहलू अनुपात इमेज
- `GET /preset/{preset}/{category}` — सोशल मीडिया प्रीसेट
- `GET /color/{hex}/{width}/{height}` — रंग-मिलान इमेज
- `GET /gradient/{w}/{h}/{from}/{to}` — ग्रेडिएंट इमेज
- `GET /svg/{width}/{height}` — SVG प्लेसहोल्डर
- `GET /avatar/{size}/{name}` — लेटर अवतार (PNG/SVG)

### मेटाडेटा एंडपॉइंट्स

- `GET /api/images` — श्रेणियां और कुल सूचीबद्ध करें
- `GET /api/info/id/{id}` — इमेज मेटाडेटा (आयाम, रंग, प्रारूप)
- `GET /api/color/{hex}` — रंग से मेल खाती इमेज

### हेल्थ एंडपॉइंट्स

- `GET /health` — लाइवनेस प्रोब (Docker/K8s)
- `GET /ready` — रेडिनेस प्रोब (503 जब तक इमेज लोड न हों)

## विशेषज्ञता और प्रमाण पत्र

- 2008 से open-source इकोसिस्टम में सक्रिय योगदानकर्ता
- सभी कोड MIT License के तहत open source हैं और <a href="https://github.com/riadvice/placepix" target="_blank" class="text-accent hover:underline">GitHub</a> पर ऑडिट योग्य हैं

## अक्सर पूछे जाने वाले प्रश्न

### मैं Docker के साथ PlacePix कैसे डिप्लॉय करूँ?

`docker run -d -p 3000:3000 -v ./images:/app/images riadvice/placepix:latest` चलाएं। अपना इमेज फ़ोल्डर माउंट करें और सेवा तुरंत स्मार्ट स्कैनिंग सक्षम के साथ शुरू होती है।

### फेस-अवेयर स्मार्ट क्रॉपिंग क्या है?

PlacePix इमेज में चेहरों का पता लगाने के लिए OpenCV Haar कैस्केड का उपयोग करता है। जब आप किसी भी URL में `?fit=smart` जोड़ते हैं, तो क्रॉप क्षेत्र को ज्यामितीय केंद्र का उपयोग करने के बजाय पता लगाए गए चेहरों पर केंद्रित करने के लिए स्थानांतरित किया जाता है। यदि कोई चेहरा नहीं मिलता है, तो यह मानक केंद्र क्रॉपिंग पर वापस आ जाता है।

### क्या मैं फोटो अपलोड किए बिना ग्रेडिएंट प्लेसहोल्डर इमेज जनरेट कर सकता हूँ?

हाँ। `/gradient/{width}/{height}/{from}/{to}` एंडपॉइंट पूरी तरह से URL पैरामीटर से ग्रेडिएंट इमेज जनरेट करता है। कोई अपलोड की गई इमेज आवश्यक नहीं है। आप `/svg/{width}/{height}` के साथ SVG प्लेसहोल्डर भी बना सकते हैं।

### मैं API के माध्यम से Instagram story साइज़ placeholder इमेज कैसे जनरेट करूँ?

प्रीसेट एंडपॉइंट का उपयोग करें: `/preset/instagram-story/{category}`। यह 1080x1920 इमेज लौटाता है। ऑप्टिमाइज्ड डिलीवरी के लिए `?format=webp&quality=70` और पोर्ट्रेट-सेफ क्रॉपिंग के लिए `?fit=smart` के साथ जोड़ें।

### क्या PlacePix S3-संगत ऑब्जेक्ट स्टोरेज का समर्थन करता है?

हाँ। PlacePix OVHcloud Object Storage, AWS S3, MinIO और किसी भी S3-संगत प्रदाता के साथ काम करता है। पर्यावरण चर के माध्यम से एंडपॉइंट, बाल्टी, एक्सेस कुंजी और गुप्त कुंजी कॉन्फ़िगर करें।

### कौन से आउटपुट प्रारूप समर्थित हैं?

WebP, AVIF, JPEG, PNG, SVG और base64 JSON। फ़ाइल एक्सटेंशन के रूप में `.webp`, `.avif`, या `.png` का उपयोग करें, या क्वेरी पैरामीटर के रूप में `?format=webp` जोड़ें। AVIF सबसे छोटी फाइलें बनाता है; PNG lossless है।

### क्या PlacePix वाणिज्यिक उपयोग के लिए निःशुल्क है?

हाँ। PlacePix MIT License के तहत जारी किया गया है और यह व्यक्तिगत और वाणिज्यिक दोनों उपयोग के लिए मुफ्त है। क्योंकि यह सेल्फ-होस्टेड है, कोई उपयोग सीमा नहीं है, कोई API कुंजी नहीं है, और कोई प्रति-अनुरोध बिलिंग नहीं है।
