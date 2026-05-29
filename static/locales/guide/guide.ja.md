---
title: PlacePix 開発者ガイド — セルフホスト型プレースホルダー画像APIと機能リファレンス
description: 完全なPlacePix開発者ガイドおよびAPIリファレンス。Dockerを使用したプレースホルダー画像のデプロイ、グラデーションとSVGの生成、InstagramやYouTubeなどのソーシャルメディアプリセットの使用方法を学びます。
keywords: セルフホスト型プレースホルダー画像API, 顔認識クロッププレースホルダー, グラデーションプレースホルダージェネレーター, Dockerプレースホルダー画像サービス, InstagramストーリープレースホルダーAPI, SVGプレースホルダージェネレーター, 開発者画像API
author: RIADVICE
robots: index, follow
og_title: PlacePix 開発者ガイド — セルフホスト型プレースホルダー画像API＆機能リファレンス
og_description: Dockerデプロイ、スマートクロップ、グラデーションプレースホルダー、SVG生成、ソーシャルメディアプリセットを網羅した完全な開発者ガイド。
twitter_title: PlacePix 開発者ガイド — セルフホスト型プレースホルダー画像API＆機能リファレンス
twitter_description: Dockerデプロイ、スマートクロップ、グラデーションプレースホルダー、SVG生成、ソーシャルメディアプリセットを網羅した完全な開発者ガイド。
jsonld_name: PlacePix 開発者ガイド — セルフホスト型プレースホルダー画像API＆機能リファレンス
jsonld_description: PlacePix（セルフホスト型プレースホルダー画像サービス）の完全な開発者ガイドとAPIリファレンス。Dockerデプロイ、顔認識スマートクロップ、グラデーションプレースホルダー、SVG生成、ソーシャルメディアプリセットを網羅。
jsonld_proficiency: Expert
jsonld_dependencies: Docker, Python 3.12, FastAPI
header_title: PlacePix 開発者ガイド
header_subtitle: セルフホスト型プレースホルダー画像サービスの完全なAPIリファレンスと機能ドキュメント。Dockerデプロイメント、スマートクロップ、グラデーションプレースホルダー、SVG生成、レターアバター、ソーシャルメディアプリセットをカバーしています。
author_label: 作成者
updated_label: "最終更新日：2026年5月"
github_label: GitHubでオープンソース
toc_title: 目次
---

## PlacePixとは？

PlacePixは、開発者とデザインチームのために構築された**セルフホスト型プレースホルダー画像サービス**です。外部ネットワーク呼び出しを必要とし、消える可能性があるサードパーティのプレースホルダーサービスとは異なり、PlacePixは完全に独自のインフラストラクチャ上で実行されます。フォルダに画像をドロップするだけで、リサイズ・フィルタリング・フォーマットされた画像を提供するURLエンドポイントを即座に取得できます。

このサービスはPythonでFastAPIを使用して書かれ、画像処理はPillowとOpenCVで駆動されています。DockerデプロイメントとS3互換オブジェクトストレージをサポートしています。

### 機能

- **ゼロ設定** — フォルダに画像をドロップするだけで開始
- **顔認識クロッピング** — OpenCVが顔を検出し中心に配置
- **グラデーション＆SVGプレースホルダー** — 画像は不要
- **ソーシャルメディアプリセット** — Instagram、YouTube、TikTokサイズを内蔵
- **カラーサーチ** — ブランドパレットに一致する画像を検索
- **レターアバター** — 名前から決定論的なプロフィール画像を生成

## Dockerデプロイメントガイド

PlacePixを実行する最速の方法はDockerです。1つのコマンドで、スマートスキャン、カラー抽出、埋め込みURLビルダーを備えたサービス全体をデプロイします。

### ワンラインデプロイメント

```bash
docker run -d -p 3000:3000 \
  -v ./images:/app/images \
  riadvice/placepix:latest
```

### Docker Compose（推奨）

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

### 永続データと環境

コンテナの再起動時に状態を保持するため、`/app/images`（画像ライブラリ）と`/app/data`（スキャンキャッシュとメタデータ）の両方をマウントしてください。環境変数または`.env`ファイルで動作を設定できます。

### OVHcloud S3互換ストレージ

PlacePixはS3互換バックエンドをサポートしています。OVHcloud Object Storageの場合は以下を設定してください：

```
S3_ENABLED=true
S3_ENDPOINT=https://s3.rbx.io.cloud.ovh.net
S3_ACCESS_KEY=your-key
S3_SECRET_KEY=your-secret
S3_BUCKET=your-bucket
S3_REGION=rbx
```

## 顔認識スマートクロッピング

標準の中心クロップは、ポートレート写真で顔を切り取ってしまう可能性があります。PlacePixはOpenCV Haarカスケードを活用した**顔認識スマートクロッピング**でこれを解決します。

### 仕組み

リクエストに`?fit=smart`が含まれる場合、PlacePixはOpenCVを使用して画像から人間の顔をスキャンします。顔が検出されると、クロップウィンドウが移動され、顔の重心が黄金比の交点にできるだけ近くなるようにします。顔が見つからない場合は、標準の中心クロップにフォールバックします。

### API例

```
# 顔認識クロップ（顔を検出し中心に配置）
/400/300/people?fit=smart

# 標準中心クロップ
/400/300/people?fit=crop

# カバー充填（伸びる可能性あり）
/400/300/people?fit=cover

# コンテイン（レターボックス）
/400/300/people?fit=contain
```

### スマートクロップを使用する場合

- ポートレート写真とヘッドショット
- 顔が重要なチームページ
- ソーシャルメディアサムネイル
- 幾何学的中心クロップが構図を損なうシナリオ

## グラデーションプレースホルダーAPI

アセットをアップロードせずに、即座に線形および放射状のグラデーション画像を生成します。ヒーロー背景、読み込み状態、デザインモックアップに最適です。

### エンドポイント構文

```
/gradient/{width}/{height}/{from_hex}/{to_hex}
```

### 例

```
# シンプルな線形グラデーション（上から下）
/gradient/800/400/3b82f6/10b981

# 45度角グラデーション
/gradient/800/400/e11d48/f59e0b?angle=45

# 中心からの放射状グラデーション
/gradient/800/400/1e293b/64748b?gradient_type=radial

# 出力形式付き
/gradient/800/400/0ea5e9/ffffff?format=webp&quality=80
```

### パラメータリファレンス

- `{from_hex}` / `{to_hex}` — #プレフィックスなしの16進カラー
- `?angle=45` — 度単位の線形角度（0-360）
- `?gradient_type=radial` — 放射状グラデーションに切り替え
- `?format=webp` — WebP出力（ファイルサイズが小さい）

## SVGプレースホルダージェネレーター

SVGプレースホルダーはサーバーサイド画像処理を必要としません。カスタマイズ可能な背景色、前景色、テキストラベルを持つインラインSVGとして生成されます。

### エンドポイント

```
/svg/{width}/{height}?bg={hex}&fg={hex}&text={label}
```

### 例

```
# デフォルトのワイヤーフレームプレースホルダー
/svg/400/300

# カスタムブランドカラー
/svg/400/300?bg=1c1917&fg=0ea5e9

# カスタムテキスト付き
/svg/400/300?bg=0ea5e9&fg=ffffff&text=Hero+Section
```

### なぜSVG？

- ファイルサイズ500バイト未満
- 品質損失なく無限にスケーラブル
- サーバー処理オーバーヘッドゼロ
- ワイヤーフレームや低忠実度プロトタイプに最適

## ソーシャルメディアプリセット

PlacePixには、人気のソーシャルプラットフォームと画面サイズの定義済みサイズが含まれています。これらを使用して、Instagram、YouTube、TikTok、LinkedIn、X（Twitter）、標準ディスプレイに最適なサイズのプレースホルダー画像を生成できます。

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

### 画面サイズ

```
/preset/mobile/nature              # 375x812
/preset/tablet/nature              # 768x1024
/preset/desktop/nature             # 1920x1080
/preset/4k/nature                  # 3840x2160
```

### ロングテールユースケース：InstagramストーリーAPI

ソーシャルメディア管理ツールを構築していて、**Instagramストーリーサイズのプレースホルダー画像**が必要な場合は、`/preset/instagram-story/{category}`を使用してください。ポートレート写真には`?fit=smart`を、最適化された配信には`?format=webp&quality=70`を組み合わせてください。


## 向きによるフィルタリング

選択前に、画像のネイティブなアスペクト比でランダム画像をフィルタリングします。これは、ヘッダー用の横長、カード用の縦長、サムネイル用の正方形など、レイアウトに自然にフィットする画像が必要な場合に便利です。

### エンドポイント

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

`squarish` の許容値は環境変数 `ORIENTATION_SQUARISH_TOLERANCE` で設定可能です（デフォルト: `0.15`）。`0.15` の値は、アスペクト比が `0.85` から `1.15` の間にある画像を正方形と見なします。厳密な 1:1 にする場合は `0.0` に設定してください。

### 仕組み

PlacePix は、初期スキャン中（ローカルファイル）およびバックグラウンドメタデータスキャン中（S3画像）にファイルヘッダーから画像の寸法を読み取ります。寸法はメモリに保存され、ランダムまたはシード選択前に候補プールをフィルタリングするために使用されます。向きが要求されたが一致する画像がない場合、`404` が返されます。
## フィルターとエフェクト

クエリパラメータを介して、任意の画像にリアルタイムフィルターとエフェクトを適用します。すべての処理はサーバーサイドで行われ、後続のリクエストのためにキャッシュされます。

### カラー調整

```
?grayscale=1               # 白黒
?sepia=1                   # 暖かいセピアトーン
?tint=0ea5e9               # 16進カラーオーバーレイ
?brightness=1.3            # 0.0～2.0
?contrast=1.2              # 0.0～2.0
?saturation=2.0            # 0.0～2.0
?invert=true               # カラー反転
?posterize=4               # カラーレベル（1-8）
?duotone=ff0000,0000ff     # 2色マップ
```

### 画像エフェクト

```
?blur=2                    # ガウスブラー（1-10）
?sharpen=1.5               # シャープ量
?emboss=true               # 3Dエンボス
?edges=sobel               # エッジ検出
?edges=canny               # Cannyエッジ
?halftone=4                # ドットパターン
?oil_painting=true         # 油絵スタイル
?pencil_sketch=true        # 鉛筆スケッチ
?cartoon=true              # カートゥーンエフェクト
?vignette=0.5              # エッジ暗化（0-1）
```

### オーバーレイパラメータ

```
?text=Hello+World          # テキストオーバーレイ
?border=4,ffffff           # ボーダー幅とカラー
?watermark=1               # 設定済みウォーターマークを適用
?padding=20                # 内部パディング
```

## アバタージェネレーター

任意の名前やメールアドレスから決定論的なアバターを生成します。PlacePixは2種類のアバターをサポートしています: **レターアバター**（カラーイニシャル）と**Multiavatar**（マルチカルチャルベクターアバター）。

### エンドポイント

```
/avatar/{size}/{name}
/avatar/{size}/{name}.{ext}
```

### パラメータ

- `type` — avatar type: `letter` (default) or `multiavatar`
- `size` — pixel size (e.g. `64`, `128`, `256`)
- `name` — any string; used as seed for the avatar

#### レターアバター (`type=letter`)

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

### 例

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

### レターアバターを使う理由

- 外部依存ゼロ — Gravatarや第三者のアバターサービス不要
- 決定論的 — 同じ名前は常に同じ色を生成する
- SVG対応 — 無限にスケーラブル、HiDPIディスプレイに最適
- あらゆるブランドエステティック向けの6つの組み込みカラーパレット

### Multiavatarを使う理由

- 120億のユニークなマルチカルチャルアバター
- 決定論的 — 同じ名前は常に同じアバターを生成する
- ピュアSVG出力 — ファイルサイズが小さく、無限にスケーラブル
- 外部API呼び出しは不要

## REST APIクイックリファレンス

すべてのエンドポイントはCORSをサポートし、長期キャッシュヘッダー付きで画像を返します。Base64 JSON出力は、小さなサムネイルで利用可能です。

### 画像エンドポイント

- `GET /{width}/{height}/{category}` — カテゴリからのランダム画像
- `GET /{width}/{height}` — すべてのカテゴリからのランダム画像
- `GET /id/{id}/{width}/{height}` — IDによる特定の画像
- `GET /ratio/{ratio}/{width}/{category}` — アスペクト比画像
- `GET /preset/{preset}/{category}` — ソーシャルメディアプリセット
- `GET /color/{hex}/{width}/{height}` — カラーマッチング画像
- `GET /gradient/{w}/{h}/{from}/{to}` — グラデーション画像
- `GET /svg/{width}/{height}` — SVGプレースホルダー
- `GET /avatar/{size}/{name}` — レターアバター（PNG/SVG）

### メタデータエンドポイント

- `GET /api/images` — カテゴリと合計を一覧表示
- `GET /api/info/id/{id}` — 画像メタデータ（寸法、カラー、形式）
- `GET /api/color/{hex}` — カラーに一致する画像

### ヘルスエンドポイント

- `GET /health` — ライブネスプローブ（Docker/K8s）
- `GET /ready` — レディネスプローブ（画像が読み込まれるまで503）

## 専門知識と資格

- 2008年以降、オープンソースエコシステムへの積極的な貢献者
- すべてのコードはMITライセンスの下でオープンソースであり、<a href="https://github.com/riadvice/placepix" target="_blank" class="text-accent hover:underline">GitHub</a>で監査可能

## よくある質問

### DockerでPlacePixをデプロイするには？

`docker run -d -p 3000:3000 -v ./images:/app/images riadvice/placepix:latest`を実行してください。画像フォルダをマウントすると、スマートスキャンが有効になった状態でサービスが即座に開始されます。

### 顔認識スマートクロッピングとは？

PlacePixはOpenCV Haarカスケードを使用して画像内の顔を検出します。任意のURLに`?fit=smart`を追加すると、幾何学的中心ではなく、検出された顔を中心にするようにクロップ領域が移動されます。顔が見つからない場合は、標準の中心クロップにフォールバックします。

### 写真をアップロードせずにグラデーションプレースホルダー画像を生成できますか？

はい。`/gradient/{width}/{height}/{from}/{to}`エンドポイントは、URLパラメータから完全にグラデーション画像を生成します。アップロードされた画像は必要ありません。`/svg/{width}/{height}`でSVGプレースホルダーも作成できます。

### API経由でInstagramストーリーサイズのプレースホルダー画像を生成するには？

プリセットエンドポイントを使用してください：`/preset/instagram-story/{category}`。これは1080x1920の画像を返します。最適化された配信には`?format=webp&quality=70`を、ポートレート安全クロップには`?fit=smart`を組み合わせてください。

### PlacePixはS3互換オブジェクトストレージをサポートしていますか？

はい。PlacePixはOVHcloud Object Storage、AWS S3、MinIO、およびS3互換プロバイダーと連携します。エンドポイント、バケット、アクセスキー、シークレットキーは環境変数で設定してください。

### サポートされている出力形式は何ですか？

WebP、AVIF、JPEG、PNG、SVG、およびBase64 JSONです。ファイル拡張子として`.webp`、`.avif`、または`.png`を使用するか、クエリパラメータとして`?format=webp`を追加してください。AVIFは最も小さいファイルを生成します。PNGはロスレスです。

### PlacePixは商用利用に無料ですか？

はい。PlacePixはMITライセンスの下でリリースされており、個人および商用利用の両方で無料です。セルフホストであるため、使用制限、APIキー、リクエストごとの課金はありません。