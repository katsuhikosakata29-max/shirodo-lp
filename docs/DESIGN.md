# 城道 LP デザイン言語（DESIGN.md）

このファイルは shirodo-lp の**唯一の**デザイン参照元。新ページ・生成スクリプト・既存ページの改修は、ここに書かれた値と規則に従う。値の実体は各ページの `:root` にインラインで複製されているため、変更するときは **このファイルを先に直し、全ページと `scripts/gen_*.py` に反映する**。

コンセプト名は「静謐な巻物」（index.html 冒頭コメント）。黒×金の武家的世界観に朱を差し色として足し、モバイルファースト（375px 基準）で組む。

---

## 1. 北極星（North Star）

- **静かで、重く、余白で語る。** 明るい SaaS 的 UI（白背景・Inter・角丸 8px の並列カード）は城道ではない。
- **文字が主役。** 装飾は 1px の金線と薄いノイズテクスチャまで。イラスト・アイコン・絵文字は使わない。
- **金は「印」、朱は「注意」。** どちらも面で塗らず、線・点・縁として使う。
- **見出しは明朝、本文はゴシック。** 書体はこの 2 種類しか使わない。
- **モバイルで完成させてから PC に広げる。** PC 版は左右余白を広げるだけで、レイアウトの構造は変えない。

---

## 2. 色トークン

背景 3 段（sumi）と文字 2 段（washi）、金 2 段、朱 1 段。これ以外の色を新規に足すときは、このファイルに追記してから使う。

| トークン | 値 | 役割 |
|---|---|---|
| `--sumi` | `#0a0908` | ページ背景。基準となる黒 |
| `--sumi-2` | `#14120e` | セクション背景の段差、カードの地、目次・称号・問いセクション |
| `--sumi-3` | `#1e1a14` | 表ヘッダ、注記ボックス、さらに一段浮かせた面 |
| `--washi` | `#f2ede2` | 本文・見出しの文字色。生成りの白 |
| `--washi-dim` | `#b5ad9b` | 補足文・キャプション・メタ情報。本文の 2 段目 |
| `--gold` | `#c9a961` | 印・線・番号・eyebrow・主 CTA の地色 |
| `--gold-bright` | `#e5c67d` | リンク・強調語（`.accent`）・ホバー時の文字色 |
| `--vermilion` | `#a33a2a` | 朱。**線と印のみ**（例：注意ボックスの左罫線 2px）。文字色には使わない（暗背景で 3:1 未満） |
| `--vermilion-text` | `#d85c45` | 朱を**文字**として出す必要があるときの代替（`--sumi-2` 上で 4.9:1）。登城難易度ページの「本格登山」ラベルなど |
| `--line` | `rgba(201,169,97,0.22)` | 区切り線・枠線の標準。金の 22% |

登城難易度ページ（`/guide/level/`）限定の追加トークン：

| トークン | 値 | 役割 |
|---|---|---|
| `--ochre` | `#c97b3f` | 難易度 2「登山」の文字色（金と朱の中間段） |
| `--warn` | `#d98a77` | 表内の注意書き（「注意 —」プレフィックス、`.warn`） |

補助的な半透明値（トークン化していないが、慣例として固定）：

- 金の薄い罫線：`rgba(201,169,97,0.12)`（表の行区切り、目次の点線）、`0.15`〜`0.18`（破線）、`0.35`〜`0.4`（下線・破線枠）
- 金の面：`rgba(201,169,97,0.05)`（引用ボックスの地）、`0.12`（最上位称号のグラデーション）
- カードの地：`rgba(30,26,20,0.4)`〜`0.5`（`--sumi-3` の半透明版）
- フッターの文字：`rgba(255,255,255,0.4)`、リンク `0.55`
- 写真の上の暗幕：`rgba(10,9,8,0.35)` → `0.92` の縦グラデーション

### 色の規則

- 背景は必ず `--sumi` 系。白背景のセクションは作らない（例外：QR コードの白箱 `#fff` のみ）。
- 金は塗り面として使うのは **主 CTA だけ**。他は線・点・文字。
- `--vermilion` は 1 ページに 1 用途まで。乱用すると「注意」の意味が薄れる。
- 文字色は `--washi` / `--washi-dim` / `--gold` / `--gold-bright` の 4 つに限る。コントラストは最低でも 4.5:1（`--washi-dim` on `--sumi` で 8.9:1）。

---

## 3. 書体

| トークン | 値 | 用途 |
|---|---|---|
| `--f-serif` | `"Shippori Mincho", "Noto Serif JP", "Hiragino Mincho ProN", "Yu Mincho", serif` | 見出し（h1〜h4）、リード文、問い本文、称号名、ブランド名、FAQ の質問 |
| `--f-sans` | `"Noto Sans JP", -apple-system, BlinkMacSystemFont, "Hiragino Sans", "Yu Gothic", sans-serif` | 本文、補足、番号、英字ラベル、CTA |

読み込みは Google Fonts。ウェイトは **Noto Sans JP 400/500/700、Shippori Mincho 500/700** のみ。

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&family=Shippori+Mincho:wght@500;700&display=swap">
```

### 基本設定

```css
body { font-family: var(--f-sans); font-weight: 400; line-height: 1.85;
       font-feature-settings: "palt"; -webkit-font-smoothing: antialiased; }
h1, h2, h3, h4 { font-family: var(--f-serif); font-weight: 500; line-height: 1.4; letter-spacing: 0.02em; }
```

### サイズの階層（モバイル基準）

| 役割 | サイズ | 書体 | 備考 |
|---|---|---|---|
| ヒーロー h1 | `clamp(3rem, 14vw, 4.6rem)`、PC 5.2rem | serif | `letter-spacing: 0.15em` |
| セクション h2 | `clamp(1.6rem, 6.5vw, 2.2rem)` | serif | `line-height: 1.55`、`text-wrap: balance` |
| 記事ページ h1 | `1.75rem` | serif | ガイド記事 |
| 記事ページ h2 | `1.35rem` | serif | 下に `1px solid var(--line)` |
| 記事ページ h3 | `1.05rem` | serif | 色は `--gold-bright` |
| リード文 | `clamp(1rem, 3.8vw, 1.12rem)` | serif | `line-height: 2` |
| 本文 | `0.9`〜`0.95rem` | sans | 色は `--washi-dim`、強調語だけ `--washi` |
| 補足・キャプション | `0.75`〜`0.85rem` | sans | `--washi-dim` |
| eyebrow・英字ラベル | `0.7`〜`0.72rem` | sans | `letter-spacing: 0.24〜0.42em`、大文字英字 |
| フッター | `0.78rem` | sans | |

### 書体の規則

- 英字のブランド表記は **字間を極端に空ける**（`S H I R O D O`、`letter-spacing: 0.42em`）。これがロゴの代わり。
- 見出しは `text-wrap: balance`、段落は `text-wrap: pretty` を付ける。
- 太字は `font-weight: 500` まで。700 は CTA のみ。
- 漢数字（壱・弐・参、一〜十）を番号に使う。アラビア数字の丸囲みは使わない。

---

## 4. 余白とレイアウト

| 項目 | 値 |
|---|---|
| コンテンツ幅 | LP セクション `780px`、開発者の想い `720px`、ガイド記事 `720px`、100 名城一覧 `760px` |
| セクション縦余白 | `88px`（標準）、`100px`（想い・最終 CTA）、PC の最終 CTA `120px` |
| 左右余白 | モバイル `24px`（記事は `20px`）、PC（768px〜）`40px` |
| 記事ページ上余白 | `110px`（固定ナビ分） |
| セクション間の段差 | 背景を `--sumi` ↔ `--sumi-2` で交互に切り替え、`border-top/bottom: 1px solid var(--line)` |
| カード内余白 | `24px 22px`（問いカード）、`20px 24px`（目次）、`14px 18px`（称号行） |
| カード間隔 | `20px`（問い）、`24px`（ステップ）、`2px`（称号ラダー） |
| アンカー余白 | `scroll-margin-top: 76〜80px` |

ブレークポイントは **768px と 1024px の 2 つ**だけ。表は 619px 以下でカード型に崩す。

### 角丸

| 値 | 用途 |
|---|---|
| `999px` | ボタン、バッジ、ピル |
| `12px` | カード、目次、表の外枠 |
| `10px` | 注記ボックス、`0 10px 10px 0`（左罫線つきの引用） |
| `8px` | 小さな注記 |
| `4px` | 問いカード（意図的に角を立てる） |
| `50%` | 番号の丸、点 |

新規要素はこの中から選ぶ。中間値（6px、16px など）は増やさない。

---

## 5. コンポーネント

### 固定ナビ `.nav`
- 上端固定、`padding: 14px 20px`（PC `18px 40px`）、背景は黒→透明の縦グラデーション + `backdrop-filter: blur(8px)`。
- 左：`城道` + `<small>SHIRODO</small>`（金、字間 0.28em）。右：ピル型 CTA「入手」。
- LP は金の塗りピル（`background: var(--gold); color: var(--sumi)`）、下層ページは金の線ピル（`border: 1px solid var(--gold); color: var(--gold-bright)`）。

### 主 CTA `.cta-primary`
- 金の塗り、`color: var(--sumi)`、`font-weight: 700`、`padding: 16px 34px`、`border-radius: 999px`、`min-height: 52px`。
- 影：`0 8px 30px rgba(201,169,97,0.35)` + 内側 1px の明るい縁。ホバーで 2px 浮く。
- 末尾に `›` の矢印（ホバーで 4px 右へ）。
- **1 画面に 1 つ**。並べるなら App Store バッジ（黒）か下線リンクにする。

### 副 CTA（下線リンク） `.hero-shindan`
- 文字 `--washi-dim`、`border-bottom: 1px solid rgba(201,169,97,0.4)`。ホバーで文字 `--gold-bright`。
- ボタンを増やしたくなったら、まずこの形で足す。

### eyebrow `.section-eyebrow`
- セクション見出しの上に置く小ラベル。`0.7rem`、`--gold`、`letter-spacing: 0.35em`、左に 20px の金線。
- 全セクション共通。h2 の前に必ず置く。

### バッジ `.hero-badge`
- ピル、`border: 1px solid var(--line)`、左に 5px の金点（`box-shadow: 0 0 8px var(--gold)`）。`0.72rem`、`--gold-bright`。

### カード `.q-card`（問い）
- 地 `rgba(30,26,20,0.5)`、`border: 1px solid var(--line)`、`border-radius: 4px`。左端に 3px の金→透明の縦グラデーション。
- 構造：メタ行（`Q.01 · 城名 — 年`、`0.72rem` 金） → 本文（serif `1.08rem`） → ヒント（`0.8rem` dim、上に破線）。

### 引用・回答ボックス `.story-quote` / `.lead-answer`
- `border-left: 3px solid var(--gold)`、地は `rgba(201,169,97,0.05)` か `--sumi-2`。文字は `--gold-bright` または `--washi`。

### 注意ボックス `.permission`
- 地 `--sumi-3`、`border-left: 2px solid var(--vermilion)`、`border-radius: 10px`。朱の唯一の標準用途。

### ステップ `.step`
- 2 カラム grid（`44px 1fr`、PC `56px 1fr`）。左に漢数字の丸（金の 1px 線、serif）、丸と丸を 1px の金線でつなぐ。
- 本文 h3 は `1.1rem` `--washi`、説明は `0.9rem` `--washi-dim`。

### 称号ラダー `.ladder-item`
- 3 カラム grid（番号・名前・石高）。左罫線 3px の金の不透明度を 0.18 → 1.0 まで段階的に上げる。最上位のみ金のグラデーション地。

### 目次 `.toc` / `.toc-nav`
- LP：左 1px の金線に沿って並べ、各行を点線で区切る。番号は `01` 形式で金。
- 記事：`--sumi-2` の角丸 12px 箱、タイトルは serif `0.9rem` 金、字間 0.2em。

### FAQ `.faq-item`
- `<details>` を使う。`summary` は serif `1rem`、右端に `＋`／`－`（金）。区切りは `--line`。

### 表 `.table-wrap > table`
- 外枠 `1px solid var(--line)`、角丸 12px、横スクロール可。`thead th` は `--sumi-3` 地に金の文字。行区切りは金 12%。

### スマホ枠 `.phone-frame`
- `aspect-ratio: 9/19.5`、角丸 36px、内側 28px。ノッチは黒のピル。横スクロール + `scroll-snap` で並べ、PC では中央寄せで全部見せる。

### 出現アニメーション `.reveal`
- `opacity: 0; translateY(24px)` → `.in` で `0.8s ease-out`。`prefers-reduced-motion` では全て無効化する。

### フッター
- 中央寄せ、`--sumi`、上に `--line`。ブランド名は serif 金、字間 0.16em。リンクは白 55% + 金 40% の下線。

---

## 6. 写真とテクスチャ

- ヒーローと最終 CTA だけ実写（松本城・熊本城）。上から `rgba(10,9,8,0.35→0.92)` の暗幕をかけ、文字を必ず読めるようにする。
- 写真の上に SVG ノイズ（`feTurbulence baseFrequency 0.9`、金味の `feColorMatrix`、`opacity 0.5`、`mix-blend-mode: overlay`）を重ねて紙の質感を出す。
- 写真クレジットは右下 `0.62rem` 白 35%。
- 装飾文字（`.philosophy::before` の巨大な「文」）は `rgba(201,169,97,0.04)` まで薄くする。

---

## 7. やること／やらないこと

**やる**
- 新ページは index.html の `:root` をそのまま複製し、このファイルにない値を足さない。
- セクションの背景は `--sumi` と `--sumi-2` を交互にし、境界を `--line` で切る。
- 見出し前に eyebrow、末尾に主 CTA を 1 つ。
- `prefers-reduced-motion` に対応する。
- 生成ページ（`/100meijo/`、`/guide/level/`）はスクリプト側のトークンをこのファイルに揃える。

**やらない**
- 白・明るいグレーの背景。ライトモード。
- 3 書体目、Inter や system-ui を主書体にすること。
- 金の塗り面を CTA 以外に使うこと。ゴールドのグラデーション文字。
- 朱を文字色に使うこと（`--vermilion-text` を使う）。朱の塗り面。
- 影付きの浮いた白カード、`box-shadow` を影として使うこと（影は主 CTA とスマホ枠のみ）。
- アイコンフォント、絵文字、イラスト。
- 角丸 6px や 16px などトークン外の値。
- 1 画面に主 CTA を 2 つ。
- 新規の色トークンをページ内に直書きすること。

---

## 8. 実装の作法

- CSS はページ内 `<style>` にインライン（外部 CSS なし、ビルドなし）。
- クラス命名はセクション名をプレフィックスにしたケバブケース（`.hero-badge`、`.q-card`、`.ladder-item`）。BEM の `__` `--` は使わない。
- 新ページを作るときは既存ページ（LP なら index.html、記事なら guide/kiroku/index.html）をコピーして削る。ゼロから書かない。
- 変更後は `python3 scripts/update_sitemap.py` を実行する（CLAUDE.md 参照）。
