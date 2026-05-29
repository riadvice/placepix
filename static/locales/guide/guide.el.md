---
title: Οδηγός προγραμματιστή PlacePix — API αυτοδιαχειριζόμενων εικόνων placeholder και αναφορά λειτουργιών
description: Πλήρης οδηγός προγραμματιστή PlacePix και αναφορά API. Μάθετε πώς να αναπτύσσετε εικόνες placeholder με Docker, να δημιουργείτε gradients και SVG, και να χρησιμοποιείτε προεπιλογές κοινωνικών δικτύων για Instagram, YouTube και άλλα.
keywords: self-hosted placeholder image API, face-aware crop placeholder, gradient placeholder generator, Docker placeholder image service, Instagram story placeholder API, SVG placeholder generator, developer image API
author: RIADVICE
robots: index, follow
og_title: Οδηγός προγραμματιστή PlacePix — API αυτοδιαχειριζόμενων εικόνων placeholder και αναφορά λειτουργιών
og_description: Πλήρης οδηγός προγραμματιστή που καλύπτει ανάπτυξη Docker, έξυπνη περικοπή, gradient placeholder, δημιουργία SVG και προεπιλογές κοινωνικών δικτύων.
twitter_title: Οδηγός προγραμματιστή PlacePix — API αυτοδιαχειριζόμενων εικόνων placeholder και αναφορά λειτουργιών
twitter_description: Πλήρης οδηγός προγραμματιστή που καλύπτει ανάπτυξη Docker, έξυπνη περικοπή, gradient placeholder, δημιουργία SVG και προεπιλογές κοινωνικών δικτύων.
jsonld_name: Οδηγός προγραμματιστή PlacePix — API αυτοδιαχειριζόμενων εικόνων placeholder και αναφορά λειτουργιών
jsonld_description: Πλήρης οδηγός προγραμματιστή και αναφορά API για το PlacePix, μια αυτοδιαχειριζόμενη υπηρεσία εικόνων placeholder. Καλύπτει ανάπτυξη Docker, έξυπνη περικοπή με αναγνώριση προσώπου, gradient placeholder, δημιουργία SVG και προεπιλογές κοινωνικών δικτύων.
jsonld_proficiency: Expert
jsonld_dependencies: Docker, Python 3.12, FastAPI
header_title: Οδηγός προγραμματιστή PlacePix
header_subtitle: Πλήρης αναφορά API και τεκμηρίωση λειτουργιών για την αυτοδιαχειριζόμενη υπηρεσία εικόνων placeholder. Καλύπτει ανάπτυξη Docker, έξυπνη περικοπή, gradient placeholder, δημιουργία SVG, avatars με γράμματα και προεπιλογές κοινωνικών δικτύων.
author_label: Από
updated_label: "Τελευταία ενημέρωση: Μάιος 2026"
github_label: Ανοικτού Κώδικα στο GitHub
toc_title: Πίνακας Περιεχομένων
---

## Τι είναι το PlacePix;

Το PlacePix είναι μια **αυτοδιαχειριζόμενη υπηρεσία εικόνων placeholder** που δημιουργήθηκε για προγραμματιστές και ομάδες σχεδιασμού. Σε αντίθεση με τις υπηρεσίες placeholder τρίτων που απαιτούν εξωτερικές κλήσεις δικτύου και μπορεί να εξαφανιστούν, το PlacePix λειτουργεί εξ ολοκλήρου στη δική σας υποδομή. Αποθέστε εικόνες σε φακέλους και λάβετε αμέσως URL endpoints που παρέχουν εικόνες με αλλαγμένο μέγεθος, φιλτραρισμένες και μορφοποιημένες.

Η υπηρεσία είναι γραμμένη σε Python με FastAPI με επεξεργασία εικόνων που υποστηρίζεται από Pillow και OpenCV. Υποστηρίζει ανάπτυξη Docker και αποθήκευση αντικειμένων συμβατή με S3.

### Χαρακτηριστικά

- **Μηδενική διαμόρφωση** — αποθέστε εικόνες σε φακέλους και ξεκινήστε
- **Περικοπή με αναγνώριση προσώπου** — Το OpenCV ανιχνεύει και κεντράρει πρόσωπα
- **Gradient και SVG placeholder** — δεν απαιτούνται εικόνες
- **Προεπιλογές κοινωνικών δικτύων** — ενσωματωμένα μεγέθη Instagram, YouTube, TikTok
- **Αναζήτηση χρώματος** — βρείτε εικόνες που ταιριάζουν με την παλέτα της μάρκας σας
- **Avatars με γράμματα** — ντετερμινιστικές εικόνες προφίλ από ονόματα

## Οδηγός ανάπτυξης Docker

Ο πιο γρήγορος τρόπος για να εκτελέσετε το PlacePix είναι με Docker. Μία μόνο εντολή αναπτύσσει ολόκληρη την υπηρεσία με έξυπνη σάρωση, εξαγωγή χρωμάτων και τον ενσωματωμένο URL builder.

### Ανάπτυξη με μία γραμμή

```bash
docker run -d -p 3000:3000 \
  -v ./images:/app/images \
  riadvice/placepix:latest
```

### Docker Compose (Συνιστάται)

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

### Μόνιμα δεδομένα και περιβάλλον

Mount τόσο το `/app/images` (τη βιβλιοθήκη εικόνων σας) όσο και το `/app/data` (cache σάρωσης και μεταδεδομένα) για να διατηρήσετε την κατάσταση κατά την επανεκκίνηση των containers. Διαμορφώστε τη συμπεριφορά μέσω μεταβλητών περιβάλλοντος ή ενός αρχείου `.env`.

### OVHcloud S3-συμβατή αποθήκευση

Το PlacePix υποστηρίζει οποιοδήποτε S3-συμβατό backend. Για το OVHcloud Object Storage, ορίστε:

```
S3_ENABLED=true
S3_ENDPOINT=https://s3.rbx.io.cloud.ovh.net
S3_ACCESS_KEY=your-key
S3_SECRET_KEY=your-secret
S3_BUCKET=your-bucket
S3_REGION=rbx
```

## Έξυπνη περικοπή με αναγνώριση προσώπου

Το τυπικό κεντρικό κόψιμο μπορεί να κόψει πρόσωπα στη φωτογραφία πορτρέτου. Το PlacePix το λύνει αυτό με **έξυπνη περικοπή με αναγνώριση προσώπου** που υποστηρίζεται από τα cascades Haar του OpenCV.

### Πώς λειτουργεί

Όταν ένα αίτημα περιλαμβάνει `?fit=smart`, το PlacePix σαρώνει την εικόνα για ανθρώπινα πρόσωπα χρησιμοποιώντας OpenCV. Εάν εντοπιστούν πρόσωπα, το παράθυρο περικοπής μετακινείται έτσι ώστε το κέντρο του προσώπου να βρίσκεται όσο το δυνατόν πιο κοντά στα σημεία τομής της χρυσής τομής. Εάν δεν βρεθούν πρόσωπα, επιστρέφει στο τυπικό κεντρικό κόψιμο.

### Παραδείγματα API

```
# Περικοπή με αναγνώριση προσώπου (εντοπίζει και κεντράρει πρόσωπα)
/400/300/people?fit=smart

# Τυπικό κεντρικό κόψιμο
/400/300/people?fit=crop

# Γέμισμα εξώφυλλου (μπορεί να τεντωθεί)
/400/300/people?fit=cover

# Περιορισμός (letterboxing)
/400/300/people?fit=contain
```

### Πότε να χρησιμοποιήσετε Smart Crop

- Φωτογραφία πορτρέτου και headshots
- Σελίδες ομάδων όπου τα πρόσωπα έχουν σημασία
- Thumbnails κοινωνικών δικτύων
- Οποιοδήποτε σενάριο όπου το γεωμετρικό κεντρικό κόψιμο καταστρέφει τη σύνθεση

## API για placeholder gradient

Δημιουργήστε γραμμικές και ακτινωτές εικόνες gradient on-the-fly χωρίς να ανεβάσετε περιουσιακά στοιχεία. Ιδανικό για hero backgrounds, καταστάσεις φόρτωσης και design mockups.

### Σύνταξη endpoint

```
/gradient/{width}/{height}/{from_hex}/{to_hex}
```

### Παραδείγματα

```
# Απλό γραμμικό gradient (από πάνω προς τα κάτω)
/gradient/800/400/3b82f6/10b981

# 45 μοιρών γωνιακό gradient
/gradient/800/400/e11d48/f59e0b?angle=45

# Ακτινωτό gradient από το κέντρο
/gradient/800/400/1e293b/64748b?gradient_type=radial

# Με format εξόδου
/gradient/800/400/0ea5e9/ffffff?format=webp&quality=80
```

### Αναφορά παραμέτρων

- `{from_hex}` / `{to_hex}` — hex χρώματα χωρίς το πρόθεμα #
- `?angle=45` — γραμμική γωνία σε μοίρες (0-360)
- `?gradient_type=radial` — μεταβαίνει σε ακτινωτό gradient
- `?format=webp` — WebP output (μικρότερο μέγεθος αρχείου)

## Γεννήτρια placeholder SVG

Τα SVG placeholders δεν απαιτούν επεξεργασία εικόνων στον server. Δημιουργούνται ως inline SVG με προσαρμόσιμο χρώμα φόντου, χρώμα προσκηνίου και ετικέτα κειμένου.

### Endpoint

```
/svg/{width}/{height}?bg={hex}&fg={hex}&text={label}
```

### Παραδείγματα

```
# Προεπιλεγμένο wireframe placeholder
/svg/400/300

# Προσαρμοσμένα χρώματα brand
/svg/400/300?bg=1c1917&fg=0ea5e9

# Με προσαρμοσμένο κείμενο
/svg/400/300?bg=0ea5e9&fg=ffffff&text=Hero+Section
```

### Γιατί SVG;

- Μέγεθος αρχείου κάτω από 500 bytes
- Άπειρα κλιμακώσιμο χωρίς απώλεια ποιότητας
- Μηδενικό κόστος επεξεργασίας στον server
- Τέλειο για wireframes και πρωτότυπα χαμηλής πιστότητας

## Προεπιλογές κοινωνικών δικτύων

Το PlacePix περιλαμβάνει προκαθορισμένες διαστάσεις για δημοφιλείς κοινωνικές πλατφόρμες και μεγέθη οθονών. Χρησιμοποιήστε τις για να δημιουργήσετε εικόνες placeholder με τέλειες διαστάσεις για Instagram, YouTube, TikTok, LinkedIn, X (Twitter) και τυπικές οθόνες.

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

### Μεγέθη οθόνης

```
/preset/mobile/nature              # 375x812
/preset/tablet/nature              # 768x1024
/preset/desktop/nature             # 1920x1080
/preset/4k/nature                  # 3840x2160
```

### Περίπτωση Χρήσης Long-Tail: Instagram Story API

Εάν δημιουργείτε ένα εργαλείο διαχείρισης κοινωνικών δικτύων και χρειάζεστε **εικόνες placeholder μεγέθους Instagram story**, χρησιμοποιήστε το `/preset/instagram-story/{category}`. Συνδυάστε με `?fit=smart` για φωτογραφίες πορτρέτου και `?format=webp&quality=70` για βελτιστοποιημένη παράδοση.

## API αναζήτησης με χρώμα

Κάθε εικόνα στο PlacePix σαρώνεται για τα 3 κυρίαρχα χρώματά της. Μπορείτε να αναζητήσετε ολόκληρη τη βιβλιοθήκη με χρώμα hex για να βρείτε εικόνες που ταιριάζουν με την παλέτα της μάρκας σας.

### Endpoints

```
# Get an image matching a specific hex color
/color/0ea5e9/400/300

# Filter any endpoint by dominant color
/400/300/nature?color=d97706

# List all images matching a color
/api/color/3b82f6
```

### How Color Scanning Works

Κατά την εκκίνηση, το PlacePix εξάγει τα πιο συχνά χρώματα από κάθε εικόνα χρησιμοποιώντας k-means clustering στο LAB color space. Αυτό παράγει αντιληπτικά ακριβείς αντιστοιχίες αντί για raw RGB μέσους όρους. Η σελίδα παλέτας (`/palette`) οπτικοποιεί αυτά τα χρώματα και σας επιτρέπει να περιηγηθείτε ανά κατηγορία απόχρωσης.

## Orientation Filtering

Filter random images by their native aspect ratio before selection. This is useful when you need images that naturally fit a layout — landscape for headers, portrait for cards, or squarish for thumbnails.

### Endpoints

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

### Configuration

The `squarish` tolerance is configurable via the `ORIENTATION_SQUARISH_TOLERANCE` environment variable (default: `0.15`). A value of `0.15` means images with an aspect ratio between `0.85` and `1.15` are considered squarish. Set to `0.0` for exact 1:1 only.

### How It Works

PlacePix reads image dimensions from file headers during the initial scan (local files) and during the background metadata scan (S3 images). The dimensions are stored in memory and used to filter the candidate pool before random or seeded selection. If orientation is requested but no images match, a `404` is returned.

## Φίλτρα και εφέ

Εφαρμόστε real-time φίλτρα και εφέ σε οποιαδήποτε εικόνα μέσω query παραμέτρων. Όλη η επεξεργασία γίνεται server-side και cacheάρεται για τις επόμενες αιτήσεις.

### Προσαρμογές χρώματος

```
?grayscale=1               # Ασπρόμαυρο
?sepia=1                   # Θερμός τόνος sepia
?tint=0ea5e9               # Hex χρώμα overlay
?brightness=1.3            # 0,0 έως 2,0
?contrast=1.2              # 0,0 έως 2,0
?saturation=2.0            # 0,0 έως 2,0
?invert=true               # Αντιστροφή χρωμάτων
?posterize=4               # Επίπεδα χρώματος (1-8)
?duotone=ff0000,0000ff     # Χάρτης δύο χρωμάτων
```

### Εφέ εικόνας

```
?blur=2                    # Gaussian blur (1-10)
?sharpen=1.5               # Ποσότητα εκκόνησης
?emboss=true               # 3D ανάγλυφο
?edges=sobel               # Ανίχνευση ακμών
?edges=canny               # Canny ακμές
?halftone=4                # Μοτίβο κουκκίδων
?oil_painting=true         # Στυλ ελαιογραφίας
?pencil_sketch=true        # Σκίτσο με μολύβι
?cartoon=true              # Εφέ καρτούν
?vignette=0.5              # Σκούρυνμα ακμών (0-1)
```

### Παράμετροι overlay

```
?text=Hello+World          # Overlay κειμένου
?border=4,ffffff           # Πλάτος & χρώμα περιγράμματος
?watermark=1               # Εφαρμογή διαμορφωμένου υδατογραφήματος
?padding=20                # Εσωτερικό padding
```

## Γεννήτρια Avatar

Δημιουργήστε ντετερμινιστικά avatar από οποιοδήποτε όνομα ή email. Το PlacePix υποστηρίζει δύο τύπους avatar: **Avatar με γράμμα** (έγχρωμα αρχικά) και **Multiavatar** (πολυπολιτισμικά διανυσματικά avatar).

### Endpoint

```
/avatar/{size}/{name}
/avatar/{size}/{name}.{ext}
```

### Παράμετροι

- `type` — avatar type: `letter` (default) or `multiavatar`
- `size` — pixel size (e.g. `64`, `128`, `256`)
- `name` — any string; used as seed for the avatar

#### Avatar με γράμμα (`type=letter`)

- `circle` — crop to a circle shape
- `border={width}` — προσθήκη περιγράμματος
- `border_color={hex}` — χρώμα περιγράμματος
- `bg={hex}` — override background color
- `fg={hex}` — override text/foreground color
- `single=true` — use only the first letter
- `uppercase=false` — preserve lowercase letters
- `palette={name}` — choose from `flatui`, `material`, `pastel`, `neon`, `cool`, `warm`

#### Multiavatar (`type=multiavatar`)

- `env` — include environment background (`true` by default, `false` to omit)
- `part` — specific part code (optional, e.g. `11`)
- `theme` — specific theme code (optional, e.g. `C`)

### Παραδείγματα

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

### Γιατί να χρησιμοποιήσετε avatar με γράμμα;

- Μηδενικές εξωτερικές εξαρτήσεις — κανένα Gravatar ή υπηρεσία avatar τρίτου
- Ντετερμινιστικό — το ίδιο όνομα παράγει πάντα το ίδιο χρώμα
- Υποστήριξη SVG — άπειρα κλιμακώσιμο, ιδανικό για οθόνες HiDPI
- Έξι ενσωματωμένες παλέτες χρωμάτων για κάθε αισθητική επωνυμίας

### Γιατί να χρησιμοποιήσετε Multiavatar;

- 12 δισεκατομμύρια μοναδικά πολυπολιτισμικά avatar
- Ντετερμινιστικό — το ίδιο όνομα παράγει πάντα το ίδιο avatar
- Καθαρή έξοδος SVG — μικρό μέγεθος αρχείου, άπειρα κλιμακώσιμο
- Δεν απαιτούνται εξωτερικά API calls

## Σύντομη αναφορά REST API

Όλα τα endpoints υποστηρίζουν CORS και επιστρέφουν εικόνες με headers μακροπρόθεσμης cache. Base64 JSON output είναι διαθέσιμο για μικρά thumbnails.

### Endpoints εικόνων

- `GET /{width}/{height}/{category}` — Τυχαία εικόνα από κατηγορία
- `GET /{width}/{height}` — Τυχαία εικόνα από όλες τις κατηγορίες
- `GET /id/{id}/{width}/{height}` — Συγκεκριμένη εικόνα κατά ID
- `GET /ratio/{ratio}/{width}/{category}` — Εικόνα αναλογίας διαστάσεων
- `GET /preset/{preset}/{category}` — Προεπιλογή κοινωνικών δικτύων
- `GET /color/{hex}/{width}/{height}` — Εικόνα με αντιστοιχία χρώματος
- `GET /gradient/{w}/{h}/{from}/{to}` — Εικόνα gradient
- `GET /svg/{width}/{height}` — SVG placeholder
- `GET /avatar/{size}/{name}` — Avatar με γράμμα (PNG/SVG)

### Metadata Endpoints

- `GET /api/images` — Λίστα κατηγοριών και συνόλων
- `GET /api/info/id/{id}` — Μεταδεδομένα εικόνας (διαστάσεις, χρώματα, μορφή)
- `GET /api/color/{hex}` — Εικόνες που αντιστοιχούν σε χρώμα

### Health Endpoints

- `GET /health` — Liveness probe (Docker/K8s)
- `GET /ready` — Readiness probe (503 έως ότου φορτωθούν οι εικόνες)

## Εμπειρία και διαπιστεύσεις

- Ενεργοί συνεισφέροντες στο open-source οικοσύστημα από το 2008
- Όλος ο κώδικας είναι open source υπό την MIT License και ελεγχόμενος στο <a href="https://github.com/riadvice/placepix" target="_blank" class="text-accent hover:underline">GitHub</a>

## Συχνές ερωτήσεις

### Πώς αναπτύσσω το PlacePix με Docker;

Εκτελέστε `docker run -d -p 3000:3000 -v ./images:/app/images riadvice/placepix:latest`. Mount τον φάκελο εικόνων σας και η υπηρεσία ξεκινά αμέσως με ενεργοποιημένη έξυπνη σάρωση.

### Τι είναι η έξυπνη περικοπή με αναγνώριση προσώπου;

Το PlacePix χρησιμοποιεί cascades Haar του OpenCV για να ανιχνεύσει πρόσωπα σε εικόνες. Όταν προσθέτετε `?fit=smart` σε οποιοδήποτε URL, η περιοχή περικοπής μετακινείται για να κεντράρει στα ανιχνευμένα πρόσωπα αντί να χρησιμοποιεί το γεωμετρικό κέντρο. Εάν δεν βρεθεί πρόσωπο, επιστρέφει στο τυπικό κεντρικό κόψιμο.

### Μπορώ να δημιουργήσω εικόνες placeholder gradient χωρίς να ανεβάσω φωτογραφίες;

Ναι. Το endpoint `/gradient/{width}/{height}/{from}/{to}` παράγει εικόνες gradient εξ ολοκλήρου από παραμέτρους URL. Δεν απαιτούνται ανεβασμένες εικόνες. Μπορείτε επίσης να δημιουργήσετε SVG placeholders με `/svg/{width}/{height}`.

### Πώς δημιουργώ εικόνες placeholder μεγέθους Instagram story μέσω API;

Χρησιμοποιήστε το endpoint preset: `/preset/instagram-story/{category}`. Αυτό επιστρέφει μια εικόνα 1080x1920. Συνδυάστε με `?format=webp&quality=70` για βελτιστοποιημένη παράδοση και `?fit=smart` για ασφαλή περικοπή πορτρέτου.

### Υποστηρίζει το PlacePix S3-συμβατή αποθήκευση αντικειμένων;

Ναι. Το PlacePix λειτουργεί με OVHcloud Object Storage, AWS S3, MinIO και οποιονδήποτε S3-συμβατό πάροχο. Διαμορφώστε endpoint, bucket, κλειδί πρόσβασης και μυστικό κλειδί μέσω μεταβλητών περιβάλλοντος.

### Ποιες μορφές εξόδου υποστηρίζονται;

WebP, AVIF, JPEG, PNG, SVG και base64 JSON. Χρησιμοποιήστε `.webp`, `.avif` ή `.png` ως επέκταση αρχείου, ή προσθέστε `?format=webp` ως query παράμετρο. Το AVIF παράγει τα μικρότερα αρχεία· το PNG είναι lossless.

### Είναι το PlacePix δωρεάν για εμπορική χρήση;

Ναι. Το PlacePix κυκλοφορεί υπό την MIT License και είναι δωρεάν τόσο για προσωπική όσο και για εμπορική χρήση. Επειδή είναι self-hosted, δεν υπάρχουν όρια χρήσης, κλειδιά API ή χρέωση ανά αίτημα.