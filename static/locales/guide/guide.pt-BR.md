---
title: Guia do Desenvolvedor PlacePix — API de Imagens Placeholder Auto-hospedadas e Referência de Recursos
description: Guia completo do desenvolvedor PlacePix e referência de API. Aprenda a implantar imagens placeholder com Docker, gerar gradientes e SVG, e usar predefinições de redes sociais para Instagram, YouTube e mais.
keywords: self-hosted placeholder image API, face-aware crop placeholder, gradient placeholder generator, Docker placeholder image service, Instagram story placeholder API, SVG placeholder generator, developer image API
author: RIADVICE
robots: index, follow
og_title: Guia do Desenvolvedor PlacePix — API de Imagens Placeholder Auto-hospedadas e Referência de Recursos
og_description: Guia completo do desenvolvedor cobrindo implantação Docker, corte inteligente, placeholders de gradiente, geração SVG e predefinições de redes sociais.
twitter_title: Guia do Desenvolvedor PlacePix — API de Imagens Placeholder Auto-hospedadas e Referência de Recursos
twitter_description: Guia completo do desenvolvedor cobrindo implantação Docker, corte inteligente, placeholders de gradiente, geração SVG e predefinições de redes sociais.
jsonld_name: Guia do Desenvolvedor PlacePix — API de Imagens Placeholder Auto-hospedadas e Referência de Recursos
jsonld_description: Guia completo do desenvolvedor e referência de API para PlacePix, um serviço de imagens placeholder auto-hospedado. Cobre implantação Docker, corte inteligente com reconhecimento facial, placeholders de gradiente, geração SVG e predefinições de redes sociais.
jsonld_proficiency: Expert
jsonld_dependencies: Docker, Python 3.12, FastAPI
header_title: Guia do Desenvolvedor PlacePix
header_subtitle: Referência completa de API e documentação de recursos para o serviço de imagens placeholder auto-hospedado. Cobre implantação Docker, corte inteligente, placeholders de gradiente, geração de SVG, avatares de letra e predefinições de redes sociais.
author_label: Por
updated_label: "Última atualização: Maio de 2026"
github_label: Código Aberto no GitHub
toc_title: Sumário
---

## O que é o PlacePix?

PlacePix é um **serviço de imagens placeholder auto-hospedado** construído para desenvolvedores e equipes de design. Ao contrário dos serviços de placeholder de terceiros que exigem chamadas de rede externas e podem desaparecer, o PlacePix roda inteiramente em sua própria infraestrutura. Coloque imagens em pastas e obtenha instantaneamente endpoints de URL que servem imagens redimensionadas, filtradas e formatadas.

O serviço é escrito em Python usando FastAPI com processamento de imagem fornecido por Pillow e OpenCV. Ele suporta implantação Docker e armazenamento de objetos compatível com S3.

### Recursos

- **Configuração zero** — coloque imagens nas pastas e comece
- **Corte com reconhecimento facial** — OpenCV detecta e centraliza rostos
- **Placeholders de gradiente e SVG** — nenhuma imagem necessária
- **Predefinições de redes sociais** — tamanhos de Instagram, YouTube, TikTok integrados
- **Busca por cor** — encontre imagens que correspondam à paleta da sua marca
- **Avatares de letras** — imagens de perfil determinísticas a partir de nomes

## Guia de implantação do Docker

A maneira mais rápida de executar o PlacePix é com Docker. Um único comando implanta todo o serviço com escaneamento inteligente, extração de cores e o construtor de URL incorporado.

### Implantação de uma linha

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

### Dados Persistentes e Ambiente

Monte tanto `/app/images` (sua biblioteca de imagens) quanto `/app/data` (cache de escaneamento e metadados) para preservar o estado entre reinícios de contêiner. Configure o comportamento via variáveis de ambiente ou um arquivo `.env`.

### Armazenamento compatível com S3 da OVHcloud

PlacePix suporta qualquer backend compatível com S3. Para OVHcloud Object Storage, defina:

```
S3_ENABLED=true
S3_ENDPOINT=https://s3.rbx.io.cloud.ovh.net
S3_ACCESS_KEY=your-key
S3_SECRET_KEY=your-secret
S3_BUCKET=your-bucket
S3_REGION=rbx
```

## Corte inteligente com reconhecimento facial

O corte central padrão pode cortar rostos na fotografia de retrato. PlacePix resolve isso com **corte inteligente com reconhecimento facial** alimentado por cascatas Haar do OpenCV.

### Como funciona

Quando uma solicitação inclui `?fit=smart`, PlacePix escaneia a imagem por rostos humanos usando OpenCV. Se rostos forem detectados, a janela de corte é deslocada para que o centroide do rosto fique o mais próximo possível dos pontos de interseção da proporção áurea. Se nenhum rosto for encontrado, retorna ao corte central padrão.

### Exemplos de API

```
# Corte com reconhecimento facial (detecta e centraliza rostos)
/400/300/people?fit=smart

# Corte central padrão
/400/300/people?fit=crop

# Preenchimento de capa (pode esticar)
/400/300/people?fit=cover

# Conter (letterboxing)
/400/300/people?fit=contain
```

### Quando usar Smart Crop

- Fotografia de retrato e headshots
- Páginas de equipe onde rostos importam
- Miniaturas de redes sociais
- Qualquer cenário onde o corte geométrico central arruína a composição

## API de Placeholder de Gradiente

Gere imagens de gradiente linear e radial instantaneamente sem fazer upload de nenhum recurso. Perfeito para fundos hero, estados de carregamento e mockups de design.

### Sintaxe do endpoint

```
/gradient/{width}/{height}/{from_hex}/{to_hex}
```

### Exemplos

```
# Gradiente linear simples (de cima para baixo)
/gradient/800/400/3b82f6/10b981

# Gradiente em ângulo de 45 graus
/gradient/800/400/e11d48/f59e0b?angle=45

# Gradiente radial do centro
/gradient/800/400/1e293b/64748b?gradient_type=radial

# Com formato de saída
/gradient/800/400/0ea5e9/ffffff?format=webp&quality=80
```

### Referência de parâmetros

- `{from_hex}` / `{to_hex}` — cores hex sem o prefixo #
- `?angle=45` — ângulo linear em graus (0-360)
- `?gradient_type=radial` — muda para gradiente radial
- `?format=webp` — saída WebP (tamanho de arquivo menor)

## Gerador de Placeholder SVG

Placeholders SVG não requerem processamento de imagem no lado do servidor. Eles são gerados como SVG inline com cor de fundo personalizável, cor de primeiro plano e rótulo de texto.

### Endpoint

```
/svg/{width}/{height}?bg={hex}&fg={hex}&text={label}
```

### Exemplos

```
# Placeholder wireframe padrão
/svg/400/300

# Cores de marca personalizadas
/svg/400/300?bg=1c1917&fg=0ea5e9

# Com texto personalizado
/svg/400/300?bg=0ea5e9&fg=ffffff&text=Hero+Section
```

### Por que SVG?

- Tamanho de arquivo menor que 500 bytes
- Infinitamente escalável sem perda de qualidade
- Zero overhead de processamento do servidor
- Perfeito para wireframes e protótipos de baixa fidelidade

## Predefinições de Redes Sociais

PlacePix inclui dimensões predefinidas para plataformas sociais populares e tamanhos de tela. Use-as para gerar imagens placeholder perfeitamente dimensionadas para Instagram, YouTube, TikTok, LinkedIn, X (Twitter) e displays padrão.

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

### Tamanhos de Tela

```
/preset/mobile/nature              # 375x812
/preset/tablet/nature              # 768x1024
/preset/desktop/nature             # 1920x1080
/preset/4k/nature                  # 3840x2160
```

### Caso de Uso Long-Tail: Instagram Story API

Se você está construindo uma ferramenta de gerenciamento de redes sociais e precisa de **imagens placeholder do tamanho do story do Instagram**, use `/preset/instagram-story/{category}`. Combine com `?fit=smart` para fotos de retrato e `?format=webp&quality=70` para entrega otimizada.

## API de Busca por Cor

Cada imagem no PlacePix é escaneada para suas 3 cores dominantes principais. Você pode pesquisar toda a biblioteca por cor hex para encontrar imagens que correspondam à paleta da sua marca.

### Endpoints

```
# Obter uma imagem correspondente a uma cor hex específica
/color/0ea5e9/400/300

# Filtrar qualquer endpoint por cor dominante
/400/300/nature?color=d97706

# Listar todas as imagens correspondentes a uma cor
/api/color/3b82f6
```

### Como funciona o escaneamento de cores

Na inicialização, PlacePix extrai as cores mais frequentes de cada imagem usando clustering k-means no espaço de cor LAB. Isso produz correspondências perceptualmente precisas em vez de médias RGB brutas. A página de paleta (`/palette`) visualiza essas cores e permite navegar por categoria de matiz.

## Filtros e Efeitos

Aplique filtros e efeitos em tempo real a qualquer imagem via parâmetros de consulta. Todo o processamento é feito no lado do servidor e cacheado para solicitações subsequentes.

### Ajustes de Cor

```
?grayscale=1               # Preto e branco
?sepia=1                   # Tom sépia quente
?tint=0ea5e9               # Sobreposição de cor hex
?brightness=1.3            # 0.0 a 2.0
?contrast=1.2              # 0.0 a 2.0
?saturation=2.0            # 0.0 a 2.0
?invert=true               # Inverter cores
?posterize=4               # Níveis de cor (1-8)
?duotone=ff0000,0000ff     # Mapa de duas cores
```

### Efeitos de Imagem

```
?blur=2                    # Desfoque gaussiano (1-10)
?sharpen=1.5               # Quantidade de nitidez
?emboss=true               # Relevo 3D
?edges=sobel               # Detecção de bordas
?edges=canny               # Bordas Canny
?halftone=4                # Padrão de pontos
?oil_painting=true         # Estilo pintura a óleo
?pencil_sketch=true        # Esboço a lápis
?cartoon=true              # Efeito cartoon
?vignette=0.5              # Escurecer bordas (0-1)
```

### Parâmetros de Sobreposição

```
?text=Hello+World          # Sobreposição de texto
?border=4,ffffff           # Largura e cor da borda
?watermark=1               # Aplicar marca d'água configurada
?padding=20                # Preenchimento interno
```

## Gerador de Avatar de Letras

Gere avatares determinísticos baseados em letras de qualquer nome ou e-mail. Perfeito para placeholders de perfil de usuário, sistemas de comentários e diretórios de equipe. Cada nome sempre produz a mesma cor, então avatares são consistentes entre sessões.

### Endpoint

```
/avatar/{size}/{name}
/avatar/{size}/{name}.{ext}
```

### Parâmetros

- `size` — tamanho em pixels (ex: `64`, `128`, `256`)
- `name` — qualquer string; primeiras letras são extraídas para o avatar
- `circle` — cortar em formato circular
- `border={width},{color}` — adicionar borda
- `bg={hex}` — substituir cor de fundo
- `fg={hex}` — substituir cor de texto/primeiro plano
- `single=true` — usar apenas a primeira letra
- `uppercase=false` — preservar letras minúsculas
- `palette={name}` — escolher entre `flatui`, `material`, `pastel` ou `neon`

### Exemplos

```
# Avatar simples de 128px
/avatar/128/John+Doe

# Avatar circular com borda personalizada
/avatar/128/John+Doe?circle=true&border=2,ffffff

# Inicial única, paleta pastel
/avatar/64/Alice?single=true&palette=pastel

# Saída SVG (escalável, menos de 500 bytes)
/avatar/128/John+Doe.svg
```

### Por que usar avatares de letras?

- Zero dependências externas — nenhum Gravatar ou serviço de avatar de terceiros
- Determinístico — o mesmo nome sempre produz a mesma cor
- Suporte SVG — infinitamente escalável, perfeito para displays HiDPI
- Quatro paletas de cores integradas para qualquer estética de marca

## Referência Rápida da API REST

Todos os endpoints suportam CORS e retornam imagens com cabeçalhos de cache de longo prazo. Saída JSON Base64 está disponível para miniaturas pequenas.

### Endpoints de Imagem

- `GET /{width}/{height}/{category}` — Imagem aleatória da categoria
- `GET /{width}/{height}` — Imagem aleatória de todas as categorias
- `GET /id/{id}/{width}/{height}` — Imagem específica por ID
- `GET /ratio/{ratio}/{width}/{category}` — Imagem com proporção de aspecto
- `GET /preset/{preset}/{category}` — Preset de mídia social
- `GET /color/{hex}/{width}/{height}` — Imagem com cor correspondente
- `GET /gradient/{w}/{h}/{from}/{to}` — Imagem de gradiente
- `GET /svg/{width}/{height}` — Placeholder SVG
- `GET /avatar/{size}/{name}` — Avatar de letra (PNG/SVG)

### Endpoints de Metadados

- `GET /api/images` — Listar categorias e totais
- `GET /api/info/id/{id}` — Metadados da imagem (dimensões, cores, formato)
- `GET /api/color/{hex}` — Imagens correspondentes a uma cor

### Endpoints de Saúde

- `GET /health` — Sonda de vivacidade (Docker/K8s)
- `GET /ready` — Sonda de prontidão (503 até imagens carregadas)

## Expertise e credenciais

- Contribuidores ativos para o ecossistema open source desde 2008
- Todo o código é open source sob a licença MIT e auditável no <a href="https://github.com/riadvice/placepix" target="_blank" class="text-accent hover:underline">GitHub</a>

## Perguntas Frequentes

### Como faço a implantação do PlacePix com Docker?

Execute `docker run -d -p 3000:3000 -v ./images:/app/images riadvice/placepix:latest`. Monte sua pasta de imagens e o serviço inicia imediatamente com escaneamento inteligente habilitado.

### O que é o corte inteligente com reconhecimento facial?

PlacePix usa cascatas Haar do OpenCV para detectar rostos em imagens. Quando você adiciona `?fit=smart` a qualquer URL, a região de corte é deslocada para centralizar nos rostos detectados em vez de usar o centro geométrico. Se nenhum rosto for encontrado, retorna ao corte central padrão.

### Posso gerar imagens placeholder de gradiente sem fazer upload de fotos?

Sim. O endpoint `/gradient/{width}/{height}/{from}/{to}` gera imagens de gradiente inteiramente a partir de parâmetros de URL. Nenhuma imagem enviada é necessária. Você também pode criar placeholders SVG com `/svg/{width}/{height}`.

### Como gerar imagens placeholder do tamanho do story do Instagram via API?

Use o endpoint de preset: `/preset/instagram-story/{category}`. Isso retorna uma imagem 1080x1920. Combine com `?format=webp&quality=70` para entrega otimizada e `?fit=smart` para corte seguro de retratos.

### O PlacePix suporta armazenamento de objetos compatível com S3?

Sim. PlacePix funciona com OVHcloud Object Storage, AWS S3, MinIO e qualquer provedor compatível com S3. Configure endpoint, bucket, chave de acesso e chave secreta via variáveis de ambiente.

### Quais formatos de saída são suportados?

WebP, AVIF, JPEG, PNG, SVG e JSON base64. Use `.webp`, `.avif` ou `.png` como extensão de arquivo, ou adicione `?format=webp` como parâmetro de consulta. AVIF produz os arquivos menores; PNG é sem perda.

### O PlacePix é gratuito para uso comercial?

Sim. PlacePix é lançado sob a licença MIT e é gratuito tanto para uso pessoal quanto comercial. Por ser auto-hospedado, não há limites de uso, chaves de API ou cobrança por solicitação.
