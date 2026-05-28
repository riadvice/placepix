---
title: Guía del Desarrollador de PlacePix — API de Imágenes Placeholder Autoalojadas y Referencia de Funciones
description: Guía completa del desarrollador de PlacePix y referencia de API. Aprenda a implementar imágenes placeholder con Docker, generar degradados y SVG, y utilizar preajustes de redes sociales para Instagram, YouTube y más.
keywords: API de imágenes placeholder autoalojada, placeholder con recorte inteligente, generador de placeholder degradado, servicio de imágenes placeholder Docker, API placeholder Instagram story, generador de placeholder SVG, API de imágenes desarrollador
author: RIADVICE
robots: index, follow
og_title: Guía del Desarrollador PlacePix — API de Imágenes Placeholder Autoalojadas & Referencia de Funciones
og_description: Guía completa del desarrollador que cubre despliegue Docker, recorte inteligente, placeholders de degradado, generación SVG y preajustes de redes sociales.
twitter_title: Guía del Desarrollador PlacePix — API de Imágenes Placeholder Autoalojadas & Referencia de Funciones
twitter_description: Guía completa del desarrollador que cubre despliegue Docker, recorte inteligente, placeholders de degradado, generación SVG y preajustes de redes sociales.
jsonld_name: Guía del Desarrollador PlacePix — API de Imágenes Placeholder Autoalojadas & Referencia de Funciones
jsonld_description: Guía completa del desarrollador y referencia API para PlacePix, un servicio de imágenes placeholder autoalojado. Cubre despliegue Docker, recorte inteligente de rostros, placeholders de degradado, generación SVG y preajustes de redes sociales.
jsonld_proficiency: Expert
jsonld_dependencies: Docker, Python 3.12, FastAPI
header_title: Guía del Desarrollador de PlacePix
header_subtitle: Referencia completa de API y documentación de funciones para el servicio de imágenes placeholder autoalojado. Cubre implementación con Docker, recorte inteligente, placeholders de degradado, generación de SVG, avatares con letras y preajustes de redes sociales.
author_label: Por
updated_label: "Última actualización: Mayo 2026"
github_label: Código Abierto en GitHub
toc_title: Tabla de Contenidos
---

## ¿Qué es PlacePix?

PlacePix es un **servicio de imágenes placeholder autoalojado** creado para desarrolladores y equipos de diseño. A diferencia de los servicios placeholder de terceros que requieren llamadas de red externas y pueden desaparecer, PlacePix funciona completamente en su propia infraestructura. Coloque imágenes en carpetas y obtenga instantáneamente puntos finales URL que sirven imágenes redimensionadas, filtradas y formateadas.

El servicio está escrito en Python usando FastAPI con procesamiento de imágenes impulsado por Pillow y OpenCV. Admite despliegue Docker y almacenamiento de objetos compatible S3.

### Características

- **Configuración cero** — coloque imágenes en carpetas y comience
- **Recorte inteligente de rostros** — OpenCV detecta y centra rostros
- **Placeholders de degradado y SVG** — no se requieren imágenes
- **Preajustes de redes sociales** — tamaños de Instagram, YouTube, TikTok integrados
- **Búsqueda por color** — encuentre imágenes que coincidan con su paleta de marca
- **Avatares de letras** — imágenes de perfil deterministas a partir de nombres

## Guía de Despliegue con Docker

La forma más rápida de ejecutar PlacePix es con Docker. Un solo comando despliega todo el servicio con escaneo inteligente, extracción de colores y el constructor de URL integrado.

### Despliegue en una línea

```bash
docker run -d -p 3000:3000 \
  -v ./images:/app/images \
  riadvice/placepix:latest
```

### Docker Compose (Recomendado)

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

### Datos persistentes y entorno

Monte tanto `/app/images` (su biblioteca de imágenes) como `/app/data` (caché de escaneo y metadatos) para preservar el estado entre reinicios de contenedores. Configure el comportamiento mediante variables de entorno o un archivo `.env`.

### Almacenamiento compatible S3 de OVHcloud

PlacePix admite cualquier backend compatible S3. Para OVHcloud Object Storage, configure:

```
S3_ENABLED=true
S3_ENDPOINT=https://s3.rbx.io.cloud.ovh.net
S3_ACCESS_KEY=su-clave
S3_SECRET_KEY=su-secreto
S3_BUCKET=su-bucket
S3_REGION=rbx
```

## Recorte Inteligente con Reconocimiento Facial

El recorte central estándar puede cortar a través de rostros en fotografía de retrato. PlacePix resuelve esto con **recorte inteligente de rostros** impulsado por cascadas Haar de OpenCV.

### Cómo funciona

Cuando una solicitud incluye `?fit=smart`, PlacePix escanea la imagen en busca de rostros humanos usando OpenCV. Si se detectan rostros, la ventana de recorte se desplaza para que el centroide del rostro esté lo más cerca posible de los puntos de intersección de la proporción áurea. Si no se encuentran rostros, vuelve al recorte central estándar.

### Ejemplos de API

```
# Recorte con reconocimiento de rostros (detecta y centra rostros)
/400/300/people?fit=smart

# Recorte central estándar
/400/300/people?fit=crop

# Relleno de portada (puede estirar)
/400/300/people?fit=cover

# Contain (letterboxing)
/400/300/people?fit=contain
```

### Cuándo usar Recorte Inteligente

- Fotografía de retrato y fotos de cabeza
- Páginas de equipo donde los rostros importan
- Miniaturas de redes sociales
- Cualquier escenario donde el recorte geométrico central arruina la composición

## API de Placeholders de Degradado

Genere imágenes de degradado lineal y radial sobre la marcha sin subir ningún recurso. Perfecto para fondos hero, estados de carga y maquetas de diseño.

### Sintaxis del punto final

```
/gradient/{width}/{height}/{from_hex}/{to_hex}
```

### Ejemplos

```
# Degradado lineal simple (arriba a abajo)
/gradient/800/400/3b82f6/10b981

# Degradado en ángulo de 45 grados
/gradient/800/400/e11d48/f59e0b?angle=45

# Degradado radial desde el centro
/gradient/800/400/1e293b/64748b?gradient_type=radial

# Con formato de salida
/gradient/800/400/0ea5e9/ffffff?format=webp&quality=80
```

### Referencia de parámetros

- `{from_hex}` / `{to_hex}` — colores hexadecimales sin el prefijo #
- `?angle=45` — ángulo lineal en grados (0-360)
- `?gradient_type=radial` — cambia a degradado radial
- `?format=webp` — salida WebP (tamaño de archivo más pequeño)

## Generador de Placeholders SVG

Los placeholders SVG no requieren procesamiento de imágenes del lado del servidor. Se generan como SVG inline con color de fondo, color de primer plano y etiqueta de texto personalizables.

### Punto final

```
/svg/{width}/{height}?bg={hex}&fg={hex}&text={label}
```

### Ejemplos

```
# Placeholder wireframe predeterminado
/svg/400/300

# Colores de marca personalizados
/svg/400/300?bg=1c1917&fg=0ea5e9

# Con texto personalizado
/svg/400/300?bg=0ea5e9&fg=ffffff&text=Hero+Section
```

### ¿Por qué SVG?

- Tamaño de archivo menor a 500 bytes
- Infinitamente escalable sin pérdida de calidad
- Cero sobrecarga de procesamiento del servidor
- Perfecto para wireframes y prototipos de baja fidelidad

## Preajustes de Redes Sociales

PlacePix incluye dimensiones predefinidas para plataformas sociales populares y tamaños de pantalla. Úselos para generar imágenes placeholder perfectamente dimensionadas para Instagram, YouTube, TikTok, LinkedIn, X (Twitter) y pantallas estándar.

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

### Tamaños de Pantalla

```
/preset/mobile/nature              # 375x812
/preset/tablet/nature              # 768x1024
/preset/desktop/nature             # 1920x1080
/preset/4k/nature                  # 3840x2160
```

### Caso de Uso de Cola Larga: API de Instagram Story

Si está construyendo una herramienta de gestión de redes sociales y necesita **imágenes placeholder de tamaño story de Instagram**, use `/preset/instagram-story/{category}`. Combine con `?fit=smart` para fotos de retrato y `?format=webp&quality=70` para entrega optimizada.

## API de Búsqueda por Color

Cada imagen en PlacePix es escaneada para sus 3 colores dominantes principales. Puede buscar toda la biblioteca por color hexadecimal para encontrar imágenes que coincidan con su paleta de marca.

### Puntos finales

```
# Obtener una imagen que coincida con un color hexadecimal específico
/color/0ea5e9/400/300

# Filtrar cualquier punto final por color dominante
/400/300/nature?color=d97706

# Listar todas las imágenes que coinciden con un color
/api/color/3b82f6
```

### Cómo funciona el escaneo de colores

Al iniciar, PlacePix extrae los colores más frecuentes de cada imagen usando agrupamiento k-means en el espacio de color LAB. Esto produce coincidencias perceptualmente precisas en lugar de promedios RGB brutos. La página de paleta (`/palette`) visualiza estos colores y le permite navegar por categoría de matiz.

## Filtros y Efectos

Aplique filtros y efectos en tiempo real a cualquier imagen mediante parámetros de consulta. Todo el procesamiento se realiza del lado del servidor y se almacena en caché para solicitudes posteriores.

### Ajustes de Color

```
?grayscale=1               # Blanco y negro
?sepia=1                   # Tono sepia cálido
?tint=0ea5e9               # Superposición de color hexadecimal
?brightness=1.3            # 0,0 a 2,0
?contrast=1.2              # 0,0 a 2,0
?saturation=2.0            # 0,0 a 2,0
?invert=true               # Invertir colores
?posterize=4               # Niveles de color (1-8)
?duotone=ff0000,0000ff     # Mapa de dos colores
```

### Efectos de Imagen

```
?blur=2                    # Desenfoque gaussiano (1-10)
?sharpen=1.5               # Cantidad de nitidez
?emboss=true               # Relieve 3D
?edges=sobel               # Detección de bordes
?edges=canny               # Bordes Canny
?halftone=4                # Patrón de puntos
?oil_painting=true         # Estilo pintura al óleo
?pencil_sketch=true        # Boceto a lápiz
?cartoon=true              # Efecto cartoon
?vignette=0.5              # Oscurecer bordes (0-1)
```

### Parámetros de Superposición

```
?text=Hello+World          # Superposición de texto
?border=4,ffffff           # Ancho y color de borde
?watermark=1               # Aplicar marca de agua configurada
?padding=20                # Relleno interno
```

## Generador de Avatares con Letras

Genere avatares deterministas basados en letras a partir de cualquier nombre o correo electrónico. Perfecto para placeholders de perfil de usuario, sistemas de comentarios y directorios de equipo. Cada nombre siempre produce el mismo color, por lo que los avatares son consistentes entre sesiones.

### Punto final

```
/avatar/{size}/{name}
/avatar/{size}/{name}.{ext}
```

### Parámetros

- `size` — tamaño en píxeles (ej. `64`, `128`, `256`)
- `name` — cualquier cadena; las primeras letras se extraen para el avatar
- `circle` — recortar a forma de círculo
- `border={width},{color}` — agregar un borde
- `bg={hex}` — anular color de fondo
- `fg={hex}` — anular color de texto/primer plano
- `single=true` — usar solo la primera letra
- `uppercase=false` — preservar letras minúsculas
- `palette={name}` — elegir entre `flatui`, `material`, `pastel` o `neon`

### Ejemplos

```
# Avatar simple de 128px
/avatar/128/John+Doe

# Avatar circular con borde personalizado
/avatar/128/John+Doe?circle=true&border=2,ffffff

# Inicial única, paleta pastel
/avatar/64/Alice?single=true&palette=pastel

# Salida SVG (escalable, menos de 500 bytes)
/avatar/128/John+Doe.svg
```

### ¿Por qué usar Avatares de Letras?

- Cero dependencias externas — sin Gravatar ni servicio de avatar de terceros
- Determinista — el mismo nombre siempre produce el mismo color
- Soporte SVG — infinitamente escalable, perfecto para pantallas HiDPI
- Cuatro paletas de colores integradas para cualquier estética de marca

## Referencia Rápida de la API REST

Todos los puntos finales admiten CORS y devuelven imágenes con encabezados de caché a largo plazo. La salida JSON Base64 está disponible para miniaturas pequeñas.

### Puntos Finales de Imagen

- `GET /{width}/{height}/{category}` — Imagen aleatoria de la categoría
- `GET /{width}/{height}` — Imagen aleatoria de todas las categorías
- `GET /id/{id}/{width}/{height}` — Imagen específica por ID
- `GET /ratio/{ratio}/{width}/{category}` — Imagen con relación de aspecto
- `GET /preset/{preset}/{category}` — Preajuste de red social
- `GET /color/{hex}/{width}/{height}` — Imagen con coincidencia de color
- `GET /gradient/{w}/{h}/{from}/{to}` — Imagen de degradado
- `GET /svg/{width}/{height}` — Placeholder SVG
- `GET /avatar/{size}/{name}` — Avatar de letras (PNG/SVG)

### Puntos Finales de Metadatos

- `GET /api/images` — Listar categorías y totales
- `GET /api/info/id/{id}` — Metadatos de imagen (dimensiones, colores, formato)
- `GET /api/color/{hex}` — Imágenes que coinciden con un color

### Puntos Finales de Salud

- `GET /health` — Sonda de vivacidad (Docker/K8s)
- `GET /ready` — Sonda de disponibilidad (503 hasta que las imágenes estén cargadas)

## Experiencia y Credenciales

- Contribuyentes activos al ecosistema de código abierto desde 2008
- Todo el código es código abierto bajo la licencia MIT y verificable en <a href="https://github.com/riadvice/placepix" target="_blank" class="text-accent hover:underline">GitHub</a>

## Preguntas Frecuentes

### ¿Cómo despliego PlacePix con Docker?

Ejecute `docker run -d -p 3000:3000 -v ./images:/app/images riadvice/placepix:latest`. Monte su carpeta de imágenes y el servicio se inicia inmediatamente con el escaneo inteligente habilitado.

### ¿Qué es el recorte inteligente con reconocimiento facial?

PlacePix usa cascadas Haar de OpenCV para detectar rostros en imágenes. Cuando agrega `?fit=smart` a cualquier URL, la región de recorte se desplaza para centrar en los rostros detectados en lugar de usar el centro geométrico. Si no se encuentra ningún rostro, vuelve al recorte central estándar.

### ¿Puedo generar imágenes placeholder de degradado sin subir fotos?

Sí. El punto final `/gradient/{width}/{height}/{from}/{to}` genera imágenes de degradado completamente a partir de parámetros URL. No se requieren imágenes subidas. También puede crear placeholders SVG con `/svg/{width}/{height}`.

### ¿Cómo genero imágenes placeholder de tamaño story de Instagram vía API?

Use el punto final de preajuste: `/preset/instagram-story/{category}`. Esto devuelve una imagen de 1080x1920. Combine con `?format=webp&quality=70` para entrega optimizada y `?fit=smart` para recorte seguro en retrato.

### ¿PlacePix admite almacenamiento de objetos compatible S3?

Sí. PlacePix funciona con OVHcloud Object Storage, AWS S3, MinIO y cualquier proveedor compatible S3. Configure el punto final, bucket, clave de acceso y clave secreta mediante variables de entorno.

### ¿Qué formatos de salida se admiten?

WebP, AVIF, JPEG, PNG, SVG y JSON base64. Use `.webp`, `.avif` o `.png` como extensión de archivo, o agregue `?format=webp` como parámetro de consulta. AVIF produce los archivos más pequeños; PNG es sin pérdida.

### ¿PlacePix es gratuito para uso comercial?

Sí. PlacePix se publica bajo la Licencia MIT y es gratuito tanto para uso personal como comercial. Al ser autoalojado, no hay límites de uso, claves API ni facturación por solicitud.
