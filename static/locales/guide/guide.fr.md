---
title: Guide du Développeur PlacePix — API d'Images Placeholder Auto-hébergées et Référence des Fonctionnalités
description: Guide complet du développeur PlacePix et référence d'API. Apprenez à déployer des images placeholder avec Docker, générer des dégradés et SVG, et utiliser des presets de réseaux sociaux pour Instagram, YouTube et plus.
keywords: API d'images placeholder auto-hébergée, placeholder avec recadrage intelligent, générateur de placeholder dégradé, service d'images placeholder Docker, API placeholder Instagram story, générateur de placeholder SVG, API images développeur
author: RIADVICE
robots: index, follow
og_title: Guide du Développeur PlacePix — API d'Images Placeholder Auto-Hébergée & Référence des Fonctionnalités
og_description: Guide complet couvrant le déploiement Docker, le recadrage intelligent, les placeholders de dégradé, la génération SVG et les préréglages réseaux sociaux.
twitter_title: Guide du Développeur PlacePix — API d'Images Placeholder Auto-Hébergée & Référence des Fonctionnalités
twitter_description: Guide complet couvrant le déploiement Docker, le recadrage intelligent, les placeholders de dégradé, la génération SVG et les préréglages réseaux sociaux.
jsonld_name: Guide du Développeur PlacePix — API d'Images Placeholder Auto-Hébergée & Référence des Fonctionnalités
jsonld_description: Guide complet et référence API pour PlacePix, un service d'images placeholder auto-hébergé. Couvre le déploiement Docker, le recadrage intelligent de visages, les placeholders de dégradé, la génération SVG et les préréglages réseaux sociaux.
jsonld_proficiency: Expert
jsonld_dependencies: Docker, Python 3.12, FastAPI
header_title: Guide du Développeur PlacePix
header_subtitle: Référence API complète et documentation des fonctionnalités du service d'images placeholder auto-hébergé. Couvre le déploiement Docker, le recadrage intelligent, les placeholders à dégradé, la génération SVG, les avatars à lettres et les presets de réseaux sociaux.
author_label: Par
updated_label: "Dernière mise à jour : Mai 2026"
github_label: Open Source sur GitHub
toc_title: Table des Matières
---

## Qu'est-ce que PlacePix ?

PlacePix est un **service d'images placeholder auto-hébergé** conçu pour les développeurs et les équipes de design. Contrairement aux services placeholder tiers qui nécessitent des appels réseau externes et peuvent disparaître, PlacePix fonctionne entièrement sur votre propre infrastructure. Déposez des images dans des dossiers et obtenez instantanément des points de terminaison URL qui servent des images redimensionnées, filtrées et formatées.

Le service est écrit en Python avec FastAPI et le traitement d'images est propulsé par Pillow et OpenCV. Il prend en charge le déploiement Docker et le stockage d'objets compatible S3.

### Fonctionnalités

- **Zéro configuration** — déposez les images dans des dossiers et commencez
- **Recadrage intelligent de visages** — OpenCV détecte et centre les visages
- **Placeholders de dégradé et SVG** — aucune image requise
- **Préréglages réseaux sociaux** — tailles Instagram, YouTube, TikTok intégrées
- **Recherche par couleur** — trouvez des images correspondant à votre palette de marque
- **Avatars lettres** — images de profil déterministes à partir de noms

## Guide de Déploiement Docker

Le moyen le plus rapide d'exécuter PlacePix est avec Docker. Une seule commande déploie l'ensemble du service avec scan intelligent, extraction de couleurs et le constructeur d'URL intégré.

### Déploiement en une ligne

```bash
docker run -d -p 3000:3000 \
  -v ./images:/app/images \
  riadvice/placepix:latest
```

### Docker Compose (Recommandé)

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

### Données persistantes et environnement

Montez à la fois `/app/images` (votre bibliothèque d'images) et `/app/data` (cache de scan et métadonnées) pour préserver l'état entre les redémarrages de conteneurs. Configurez le comportement via des variables d'environnement ou un fichier `.env`.

### Stockage compatible S3 OVHcloud

PlacePix prend en charge n'importe quel backend compatible S3. Pour OVHcloud Object Storage, configurez :

```
S3_ENABLED=true
S3_ENDPOINT=https://s3.rbx.io.cloud.ovh.net
S3_ACCESS_KEY=votre-clé
S3_SECRET_KEY=votre-secret
S3_BUCKET=votre-bucket
S3_REGION=rbx
```

## Recadrage Intelligent de Visages

Le recadrage central standard peut couper les visages en photographie de portrait. PlacePix résout cela avec un **recadrage intelligent de visages** propulsé par les cascades de Haar d'OpenCV.

### Comment ça marche

Lorsqu'une requête inclut `?fit=smart`, PlacePix scanne l'image pour des visages humains en utilisant OpenCV. Si des visages sont détectés, la fenêtre de recadrage est déplacée pour que le centroïde du visage soit aussi proche que possible des points d'intersection du nombre d'or. Si aucun visage n'est trouvé, il revient au recadrage central standard.

### Exemples d'API

```
# Recadrage intelligent de visages (détecte et centre les visages)
/400/300/people?fit=smart

# Recadrage central standard
/400/300/people?fit=crop

# Remplissage couverture (peut étirer)
/400/300/people?fit=cover

# Contain (letterboxing)
/400/300/people?fit=contain
```

### Quand utiliser le Recadrage Intelligent

- Photographie de portrait et portraits
- Pages d'équipe où les visages sont importants
- Miniatures de réseaux sociaux
- Tout scénario où le recadrage géométrique central ruine la composition

## API de Placeholders à Dégradé

Générez des images de dégradé linéaire et radial à la volée sans télécharger de ressources. Parfait pour les arrière-plans hero, les états de chargement et les maquettes de design.

### Syntaxe du Point de Terminaison

```
/gradient/{width}/{height}/{from_hex}/{to_hex}
```

### Exemples

```
# Dégradé linéaire simple (haut vers bas)
/gradient/800/400/3b82f6/10b981

# Dégradé à angle de 45 degrés
/gradient/800/400/e11d48/f59e0b?angle=45

# Dégradé radial depuis le centre
/gradient/800/400/1e293b/64748b?gradient_type=radial

# Avec format de sortie
/gradient/800/400/0ea5e9/ffffff?format=webp&quality=80
```

### Référence des Paramètres

- `{from_hex}` / `{to_hex}` — couleurs hexadécimales sans le préfixe #
- `?angle=45` — angle linéaire en degrés (0-360)
- `?gradient_type=radial` — passe en dégradé radial
- `?format=webp` — sortie WebP (taille de fichier plus petite)

## Générateur de Placeholders SVG

Les placeholders SVG nécessitent zéro traitement d'image côté serveur. Ils sont générés en SVG inline avec couleur de fond, couleur de premier plan et étiquette de texte personnalisables.

### Point de Terminaison

```
/svg/{width}/{height}?bg={hex}&fg={hex}&text={label}
```

### Exemples

```
# Placeholder wireframe par défaut
/svg/400/300

# Couleurs de marque personnalisées
/svg/400/300?bg=1c1917&fg=0ea5e9

# Avec texte personnalisé
/svg/400/300?bg=0ea5e9&fg=ffffff&text=Hero+Section
```

### Pourquoi SVG ?

- Taille de fichier inférieure à 500 octets
- Infiniment scalable sans perte de qualité
- Zéro surcharge de traitement serveur
- Parfait pour les wireframes et prototypes basse fidélité

## Préréglages Réseaux Sociaux

PlacePix inclut des dimensions prédéfinies pour les plateformes sociales populaires et les tailles d'écran. Utilisez-les pour générer des images placeholder parfaitement dimensionnées pour Instagram, YouTube, TikTok, LinkedIn, X (Twitter) et les affichages standards.

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

### Tailles d'Écran

```
/preset/mobile/nature              # 375x812
/preset/tablet/nature              # 768x1024
/preset/desktop/nature             # 1920x1080
/preset/4k/nature                  # 3840x2160
```

### Cas d'Usage Longue Traîne : API Instagram Story

Si vous créez un outil de gestion de réseaux sociaux et avez besoin **d'images placeholder de taille story Instagram**, utilisez `/preset/instagram-story/{category}`. Combinez avec `?fit=smart` pour les photos de portrait et `?format=webp&quality=70` pour une livraison optimisée.

## API de Recherche par Couleur

Chaque image dans PlacePix est scannée pour ses 3 couleurs dominantes principales. Vous pouvez rechercher l'ensemble de la bibliothèque par couleur hexadécimale pour trouver des images correspondant à votre palette de marque.

### Points de Terminaison

```
# Obtenir une image correspondant à une couleur hexadécimale spécifique
/color/0ea5e9/400/300

# Filtrer n'importe quel point de terminaison par couleur dominante
/400/300/nature?color=d97706

# Lister toutes les images correspondant à une couleur
/api/color/3b82f6
```

### Comment Fonctionne le Scan de Couleurs

Au démarrage, PlacePix extrait les couleurs les plus fréquentes de chaque image en utilisant le clustering k-means dans l'espace couleur LAB. Cela produit des correspondances perceptuellement précises plutôt que des moyennes RGB brutes. La page palette (`/palette`) visualise ces couleurs et vous permet de naviguer par catégorie de teinte.

## Filtrage par orientation

Filtrez les images aléatoires selon leur rapport d'aspect natif avant la sélection. C'est utile lorsque vous avez besoin d'images qui s'intègrent naturellement à une mise en page — paysage pour les en-têtes, portrait pour les cartes, ou carré pour les vignettes.

### Points de terminaison

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

La tolérance `squarish` est configurable via la variable d'environnement `ORIENTATION_SQUARISH_TOLERANCE` (défaut : `0.15`). Une valeur de `0.15` signifie que les images avec un rapport d'aspect entre `0.85` et `1.15` sont considérées comme carrées. Réglez sur `0.0` pour un rapport exact de 1:1.

### Fonctionnement

PlacePix lit les dimensions des images à partir des en-têtes de fichiers lors du scan initial (fichiers locaux) et lors du scan de métadonnées en arrière-plan (images S3). Les dimensions sont stockées en mémoire et utilisées pour filtrer le pool de candidats avant la sélection aléatoire ou déterministe. Si une orientation est demandée mais qu'aucune image ne correspond, un `404` est retourné.
## Filtres et Effets

Appliquez des filtres et effets en temps réel à n'importe quelle image via des paramètres de requête. Tout le traitement est fait côté serveur et mis en cache pour les requêtes suivantes.

### Ajustements de Couleur

```
?grayscale=1               # Noir & blanc
?sepia=1                   # Ton sépia chaud
?tint=0ea5e9               # Superposition de couleur hexadécimale
?brightness=1.3            # 0,0 à 2,0
?contrast=1.2              # 0,0 à 2,0
?saturation=2.0            # 0,0 à 2,0
?invert=true               # Inverser les couleurs
?posterize=4               # Niveaux de couleur (1-8)
?duotone=ff0000,0000ff     # Carte deux couleurs
```

### Effets d'Image

```
?blur=2                    # Flou gaussien (1-10)
?sharpen=1.5               # Quantité de netteté
?emboss=true               # Relief 3D
?edges=sobel               # Détection de contours
?edges=canny               # Contours Canny
?halftone=4                # Motif de points
?oil_painting=true         # Style peinture à l'huile
?pencil_sketch=true        # Croquis au crayon
?cartoon=true              # Effet cartoon
?vignette=0.5              # Assombrir les bords (0-1)
```

### Paramètres de Superposition

```
?text=Hello+World          # Superposition de texte
?border=4,ffffff           # Largeur et couleur de bordure
?watermark=1               # Appliquer le filigrane configuré
?padding=20                # Remplissage interne
```

## Générateur d'Avatars à Lettres

Générez des avatars déterministes basés sur des lettres à partir de n'importe quel nom ou email. Parfait pour les placeholders de profil utilisateur, les systèmes de commentaires et les annuaires d'équipe. Chaque nom produit toujours la même couleur, donc les avatars sont cohérents entre les sessions.

### Point de Terminaison

```
/avatar/{size}/{name}
/avatar/{size}/{name}.{ext}
```

### Paramètres

- `size` — taille en pixels (ex. `64`, `128`, `256`)
- `name` — n'importe quelle chaîne ; les premières lettres sont extraites pour l'avatar
- `circle` — recadrer en forme de cercle
- `border={width},{color}` — ajouter une bordure
- `bg={hex}` — remplacer la couleur de fond
- `fg={hex}` — remplacer la couleur de texte/premier plan
- `single=true` — utiliser seulement la première lettre
- `uppercase=false` — préserver les lettres minuscules
- `palette={name}` — choisir parmi `flatui`, `material`, `pastel` ou `neon`

### Exemples

```
# Avatar simple 128px
/avatar/128/John+Doe

# Avatar circulaire avec bordure personnalisée
/avatar/128/John+Doe?circle=true&border=2,ffffff

# Initiale unique, palette pastel
/avatar/64/Alice?single=true&palette=pastel

# Sortie SVG (scalable, moins de 500 octets)
/avatar/128/John+Doe.svg
```

### Pourquoi Utiliser des Avatars à Lettres ?

- Zéro dépendance externe — pas de Gravatar ou de service d'avatar tiers
- Déterministe — le même nom produit toujours la même couleur
- Support SVG — infiniment scalable, parfait pour les affichages HiDPI
- Quatre palettes de couleurs intégrées pour toute esthétique de marque

## Référence Rapide de l'API REST

Tous les points de terminaison prennent en charge CORS et retournent des images avec des en-têtes de cache à long terme. La sortie JSON Base64 est disponible pour les petites vignettes.

### Points de Terminaison d'Image

- `GET /{width}/{height}/{category}` — Image aléatoire de la catégorie
- `GET /{width}/{height}` — Image aléatoire de toutes les catégories
- `GET /id/{id}/{width}/{height}` — Image spécifique par ID
- `GET /ratio/{ratio}/{width}/{category}` — Image avec ratio d'aspect
- `GET /preset/{preset}/{category}` — Préréglage réseau social
- `GET /color/{hex}/{width}/{height}` — Image avec correspondance de couleur
- `GET /gradient/{w}/{h}/{from}/{to}` — Image de dégradé
- `GET /svg/{width}/{height}` — Placeholder SVG
- `GET /avatar/{size}/{name}` — Avatar à lettres (PNG/SVG)

### Points de Terminaison de Métadonnées

- `GET /api/images` — Lister les catégories et totaux
- `GET /api/info/id/{id}` — Métadonnées de l'image (dimensions, couleurs, format)
- `GET /api/color/{hex}` — Images correspondant à une couleur

### Points de Terminaison de Santé

- `GET /health` — Sonde de vivacité (Docker/K8s)
- `GET /ready` — Sonde de disponibilité (503 jusqu'à ce que les images soient chargées)

## Expertise et Références

- Contributeurs actifs à l'écosystème open source depuis 2008
- Tout le code est open source sous la licence MIT et vérifiable sur <a href="https://github.com/riadvice/placepix" target="_blank" class="text-accent hover:underline">GitHub</a>

## Questions Fréquemment Posées

### Comment déployer PlacePix avec Docker ?

Exécutez `docker run -d -p 3000:3000 -v ./images:/app/images riadvice/placepix:latest`. Montez votre dossier d'images et le service démarre immédiatement avec le scan intelligent activé.

### Qu'est-ce que le recadrage intelligent de visages ?

PlacePix utilise les cascades de Haar d'OpenCV pour détecter les visages dans les images. Lorsque vous ajoutez `?fit=smart` à n'importe quelle URL, la région de recadrage est déplacée pour centrer sur les visages détectés plutôt que d'utiliser le centre géométrique. Si aucun visage n'est trouvé, il revient au recadrage central standard.

### Puis-je générer des images placeholder de dégradé sans télécharger de photos ?

Oui. Le point de terminaison `/gradient/{width}/{height}/{from}/{to}` génère des images de dégradé entièrement à partir de paramètres URL. Aucune image téléchargée n'est requise. Vous pouvez également créer des placeholders SVG avec `/svg/{width}/{height}`.

### Comment générer des images placeholder de taille story Instagram via l'API ?

Utilisez le point de terminaison préréglé : `/preset/instagram-story/{category}`. Cela retourne une image 1080x1920. Combinez avec `?format=webp&quality=70` pour une livraison optimisée et `?fit=smart` pour un recadrage sûr en portrait.

### PlacePix prend-il en charge le stockage d'objets compatible S3 ?

Oui. PlacePix fonctionne avec OVHcloud Object Storage, AWS S3, MinIO et tout fournisseur compatible S3. Configurez le point de terminaison, le bucket, la clé d'accès et la clé secrète via des variables d'environnement.

### Quels formats de sortie sont pris en charge ?

WebP, AVIF, JPEG, PNG, SVG et JSON base64. Utilisez `.webp`, `.avif` ou `.png` comme extension de fichier, ou ajoutez `?format=webp` comme paramètre de requête. AVIF produit les fichiers les plus petits ; PNG est sans perte.

### PlacePix est-il gratuit pour un usage commercial ?

Oui. PlacePix est publié sous la licence MIT et est gratuit pour un usage personnel et commercial. Comme il est auto-hébergé, il n'y a pas de limites d'utilisation, pas de clés API et pas de facturation par requête.
