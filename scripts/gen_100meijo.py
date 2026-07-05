# -*- coding: utf-8 -*-
"""castles.json から /100meijo/index.html を生成する"""
import json, html

SRC = "/Users/sakatakatsuhiko/Developer/shirodo/native/src/data/castles.json"
OUT = "/Users/sakatakatsuhiko/Developer/shirodo-lp/100meijo/index.html"

REGIONS = [
    ("北海道・東北", "hokkaido-tohoku", ["北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県"]),
    ("関東・甲信越", "kanto-koshinetsu", ["茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県", "山梨県", "長野県", "新潟県"]),
    ("北陸・東海", "hokuriku-tokai", ["富山県", "石川県", "福井県", "岐阜県", "静岡県", "愛知県", "三重県"]),
    ("近畿", "kinki", ["滋賀県", "京都府", "大阪府", "兵庫県", "奈良県", "和歌山県"]),
    ("中国・四国", "chugoku-shikoku", ["鳥取県", "島根県", "岡山県", "広島県", "山口県", "徳島県", "香川県", "愛媛県", "高知県"]),
    ("九州・沖縄", "kyushu-okinawa", ["福岡県", "佐賀県", "長崎県", "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県"]),
]

castles = [c for c in json.load(open(SRC)) if c.get("is_100meijo")]
assert len(castles) == 100, f"expected 100, got {len(castles)}"
castles.sort(key=lambda c: int(c["no"]))

def esc(s):
    return html.escape(str(s or ""), quote=True)

# ---- 地方別リストHTML + 目次 ----
region_sections = []
toc_items = []
for region, slug, prefs in REGIONS:
    items = [c for c in castles if c["prefecture"] in prefs]
    rows = []
    for c in items:
        meta_parts = [c["prefecture"], c.get("type", "")]
        if c.get("is_genzon"):
            meta_parts.append("現存天守")
        if c.get("is_kokuho"):
            meta_parts.append("国宝")
        meta = "・".join(p for p in meta_parts if p)
        hook = c.get("hook", "")
        hook_html = f'\n        <p class="hook">{esc(hook)}</p>' if hook else ""
        rows.append(f'''      <li class="castle" id="c{esc(c["no"])}">
        <span class="no">{esc(c["no"])}</span>
        <div class="castle-body">
          <span class="cname">{esc(c["name"])}<small>{esc(c["name_kana"])}</small></span>
          <span class="cmeta">{esc(meta)}</span>{hook_html}
        </div>
      </li>''')
    count = len(items)
    toc_items.append(
        f'      <li><a href="#{slug}"><span class="toc-label">{esc(region)}</span>'
        f'<span class="toc-count">{items[0]["no"]}–{items[-1]["no"]}</span></a></li>')
    region_sections.append(f'''  <section class="region" id="{slug}">
    <h3 class="serif">{esc(region)}<span class="rcount">{count}城</span></h3>
    <ol class="castle-list">
{chr(10).join(rows)}
    </ol>
    <a class="back-to-toc" href="#toc">▲ 目次へ戻る</a>
  </section>''')
region_html = "\n".join(region_sections)

toc_items.append('      <li><a href="#about"><span class="toc-label">スタンプラリーとは・やり方</span></a></li>')
toc_items.append('      <li><a href="#faq"><span class="toc-label">よくある質問</span></a></li>')
toc_html = f'''  <nav class="toc" id="toc" aria-label="目次">
    <p class="toc-title">目 次</p>
    <ol>
{chr(10).join(toc_items)}
    </ol>
  </nav>'''

# ---- ItemList JSON-LD（軽量: 名前のみ） ----
itemlist = {
    "@context": "https://schema.org",
    "@type": "ItemList",
    "name": "日本100名城 一覧",
    "description": "公益財団法人日本城郭協会が選定した日本100名城の全一覧（公式番号順）。",
    "numberOfItems": 100,
    "itemListOrder": "https://schema.org/ItemListOrderAscending",
    "itemListElement": [
        {"@type": "ListItem", "position": int(c["no"]), "name": c["name"]}
        for c in castles
    ],
}

faq = [
    ("日本100名城とは何ですか？",
     "日本100名城とは、公益財団法人日本城郭協会が2006年に選定した、日本を代表する100の城です。江戸城・大阪城・姫路城などの有名な城から、根室半島チャシ跡群のような史跡まで、全都道府県から選ばれています。"),
    ("100名城スタンプ帳はどこで買えますか？",
     "公式スタンプ帳は単体では販売されておらず、公式ガイドブック『日本100名城に行こう 公式スタンプ帳つき』（770円・税込）の巻末に付属しています。全国の書店やAmazon・楽天などの通販で購入できます。続日本100名城と一体になった『日本100名城と続日本100名城に行こう』（1,300円・税込）もあります。"),
    ("100名城スタンプは24時間いつでも押せますか？",
     "いいえ。100名城スタンプの多くは管理事務所・休憩所・資料館などの屋内に設置されており、押せるのは開館時間内だけです。冬期は設置場所が休業・移動する城もあるため、遠方の城へ行く前に日本城郭協会サイトの「スタンプ設置場所などの変更一覧」で確認するのが確実です。"),
    ("100名城を全部まわると何年かかりますか？",
     "決まった期限はなく、押印に有効期間もありません。集中してまわる人は数か月〜1年、週末や連休を使う人は3年前後、10年かけてゆっくり達成する人もいます。離島や山城を含むため、自分のペースで計画するのがおすすめです。"),
    ("スタンプを押し間違えたらどうなりますか？",
     "押し間違えても登城認定が受けられなくなるわけではありません。日本城郭協会が公式サイトのよくある質問で対処法を案内しているので、慌てて別の用紙に押し直す前に確認してください。なお、別の紙に押したスタンプを切り貼りしたものは原則無効とされています。"),
    ("100名城のスタンプラリーとどう違いますか？",
     "公式スタンプラリーは各城に設置されたスタンプを専用スタンプ帳に集める仕組みです。城道（SHIRODO）はスタンプの代わりに、登城の記録・メモ・写真を端末とiCloudに残せるアプリです。スタンプラリーと併用することもできます。"),
    ("スタンプ帳を忘れても記録できますか？",
     "はい。城道（SHIRODO）はスマートフォンだけで登城記録を残せるので、スタンプ帳を忘れた日や、スタンプ設置場所が閉まっていた日でも、その場で記録できます。"),
    ("続日本100名城には対応していますか？",
     "現在は日本100名城のみ収録しています。続日本100名城への対応は順次検討中です。"),
    ("アプリは無料ですか？",
     "城道（SHIRODO）は無料でお使いいただけます。アプリ内広告もありません。アカウント登録も不要です。"),
]
faqpage = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "inLanguage": "ja-JP",
    "mainEntity": [
        {"@type": "Question", "name": q,
         "acceptedAnswer": {"@type": "Answer", "text": a}}
        for q, a in faq
    ],
}

breadcrumb = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "城道（SHIRODO）", "item": "https://shirodo.com/"},
        {"@type": "ListItem", "position": 2, "name": "日本100名城 一覧", "item": "https://shirodo.com/100meijo/"},
    ],
}

faq_html = "\n".join(
    f'''    <details class="faq-item">
      <summary>{esc(q)}</summary>
      <div class="faq-body">{esc(a)}</div>
    </details>''' for q, a in faq)

jld = lambda d: json.dumps(d, ensure_ascii=False, indent=1)

page = f'''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>日本100名城 一覧（全100城・地方別）と記録アプリ | 城道（SHIRODO）</title>
<meta name="description" content="日本100名城の全一覧を地方別・公式番号順に掲載。各城には「なぜ？」から入る問い付き。スタンプ帳の代わりにスマホで登城記録を残せる無料アプリ、城道（SHIRODO）。">
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://shirodo.com/100meijo/">
<meta property="og:title" content="日本100名城 一覧（全100城・地方別）| 城道（SHIRODO）">
<meta property="og:description" content="日本100名城の全一覧を地方別・公式番号順に掲載。各城に「なぜ？」から入る問い付き。登城記録アプリ城道（SHIRODO）。">
<meta property="og:image" content="https://shirodo.com/assets/matsumoto-castle.jpg">
<meta property="og:url" content="https://shirodo.com/100meijo/">
<meta property="og:type" content="website">
<meta property="og:site_name" content="城道（SHIRODO）">
<meta property="og:locale" content="ja_JP">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="日本100名城 一覧（全100城・地方別）| 城道（SHIRODO）">
<meta name="twitter:description" content="日本100名城の全一覧を地方別・公式番号順に掲載。各城に「なぜ？」から入る問い付き。">
<meta name="twitter:image" content="https://shirodo.com/assets/matsumoto-castle.jpg">
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🏯</text></svg>">
<script type="application/ld+json">
{jld(breadcrumb)}
</script>
<script type="application/ld+json">
{jld(itemlist)}
</script>
<script type="application/ld+json">
{jld(faqpage)}
</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&family=Shippori+Mincho:wght@500;700&display=swap">
<style>
  :root {{
    --gold: #c9a961;
    --gold-bright: #e5c67d;
    --vermilion: #a33a2a;
    --sumi: #0a0908;
    --sumi-2: #14120e;
    --sumi-3: #1e1a14;
    --washi: #f2ede2;
    --washi-dim: #b5ad9b;
    --line: rgba(201, 169, 97, 0.22);
    --f-serif: "Shippori Mincho", "Noto Serif JP", "Hiragino Mincho ProN", "Yu Mincho", serif;
    --f-sans: "Noto Sans JP", -apple-system, BlinkMacSystemFont, "Hiragino Sans", "Yu Gothic", sans-serif;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html {{ scroll-behavior: smooth; -webkit-text-size-adjust: 100%; }}
  body {{
    background: var(--sumi);
    color: var(--washi);
    font-family: var(--f-sans);
    line-height: 1.85;
    font-feature-settings: "palt";
    -webkit-font-smoothing: antialiased;
  }}
  .serif {{ font-family: var(--f-serif); font-weight: 500; letter-spacing: 0.02em; }}
  .visually-hidden {{
    position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px;
    overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0;
  }}
  a {{ color: var(--gold-bright); text-decoration: none; }}

  .nav {{
    position: fixed; top: 0; left: 0; right: 0; z-index: 50;
    display: flex; justify-content: space-between; align-items: center;
    padding: 14px 20px;
    background: linear-gradient(to bottom, rgba(10,9,8,0.95), rgba(10,9,8,0.6) 80%, transparent);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
  }}
  .nav-brand {{ font-family: var(--f-serif); font-size: 1.15rem; color: var(--washi); }}
  .nav-brand small {{ font-size: 0.6rem; letter-spacing: 0.25em; color: var(--gold); margin-left: 8px; }}
  .nav-cta {{
    font-size: 0.8rem; padding: 7px 18px; border: 1px solid var(--gold);
    border-radius: 999px; color: var(--gold-bright);
  }}

  main {{ max-width: 760px; margin: 0 auto; padding: 110px 20px 60px; }}
  .breadcrumb {{ font-size: 0.75rem; color: var(--washi-dim); margin-bottom: 28px; }}
  .breadcrumb a {{ color: var(--washi-dim); text-decoration: underline; text-underline-offset: 3px; text-decoration-color: var(--line); }}

  h1 {{ font-family: var(--f-serif); font-size: 1.9rem; line-height: 1.5; margin-bottom: 6px; }}
  .h1-sub {{ font-size: 0.85rem; color: var(--gold); letter-spacing: 0.1em; margin-bottom: 24px; }}
  .lead {{ color: var(--washi-dim); font-size: 0.95rem; margin-bottom: 16px; }}
  .lead strong {{ color: var(--washi); font-weight: 500; }}

  .app-callout {{
    margin: 36px 0 48px; padding: 22px 22px;
    background: var(--sumi-2); border: 1px solid var(--line); border-radius: 12px;
  }}
  .app-callout h2 {{ font-family: var(--f-serif); font-size: 1.15rem; margin-bottom: 10px; }}
  .app-callout p {{ font-size: 0.9rem; color: var(--washi-dim); margin-bottom: 14px; }}
  .cta-primary {{
    display: inline-block; padding: 11px 26px; border-radius: 999px;
    background: linear-gradient(135deg, var(--gold), var(--gold-bright));
    color: var(--sumi); font-weight: 700; font-size: 0.9rem;
  }}
  .cta-note {{ font-size: 0.72rem; color: var(--washi-dim); margin-top: 10px; }}

  .toc {{
    background: var(--sumi-2); border: 1px solid var(--line); border-radius: 12px;
    padding: 24px 26px; margin-bottom: 52px;
    scroll-margin-top: 76px;
  }}
  .toc-title {{
    font-family: var(--f-serif); font-size: 0.95rem; color: var(--gold);
    letter-spacing: 0.2em; margin-bottom: 16px;
  }}
  .toc ol {{ list-style: none; }}
  .toc li {{ border-bottom: 1px solid rgba(201,169,97,0.12); }}
  .toc li:last-child {{ border-bottom: none; }}
  .toc a {{
    display: flex; align-items: baseline; justify-content: space-between;
    padding: 11px 2px; font-size: 0.92rem; color: var(--washi);
  }}
  .toc a:hover .toc-label {{ color: var(--gold-bright); }}
  .toc-count {{ font-size: 0.72rem; color: var(--gold); letter-spacing: 0.1em; margin-left: 12px; white-space: nowrap; }}
  @media (min-width: 720px) {{
    .toc ol {{ display: grid; grid-template-columns: 1fr 1fr; column-gap: 32px; }}
    .toc li:nth-last-child(2) {{ border-bottom: none; }}
  }}

  .region, .about, .faq {{ scroll-margin-top: 76px; }}
  .back-to-toc {{
    display: inline-block; margin-top: 18px; font-size: 0.78rem;
    color: var(--washi-dim); text-decoration: underline;
    text-underline-offset: 3px; text-decoration-color: var(--line);
  }}
  .back-to-toc:hover {{ color: var(--gold-bright); }}

  .region {{ margin-bottom: 52px; }}
  .region h3 {{
    font-size: 1.3rem; padding-bottom: 10px; margin-bottom: 18px;
    border-bottom: 1px solid var(--line);
  }}
  .rcount {{ font-size: 0.75rem; color: var(--gold); margin-left: 12px; letter-spacing: 0.1em; }}
  .castle-list {{ list-style: none; }}
  .castle {{
    display: flex; gap: 14px; padding: 14px 4px;
    border-bottom: 1px solid rgba(201, 169, 97, 0.1);
  }}
  .no {{
    flex: 0 0 34px; height: 34px; display: flex; align-items: center; justify-content: center;
    font-family: var(--f-serif); font-size: 0.85rem; color: var(--gold);
    border: 1px solid var(--line); border-radius: 50%;
    margin-top: 2px;
  }}
  .castle-body {{ flex: 1; }}
  .cname {{ font-family: var(--f-serif); font-size: 1.05rem; display: block; }}
  .cname small {{ font-size: 0.7rem; color: var(--washi-dim); margin-left: 10px; font-family: var(--f-sans); }}
  .cmeta {{ font-size: 0.72rem; color: var(--washi-dim); display: block; margin-top: 2px; }}
  .hook {{
    font-size: 0.82rem; color: var(--gold-bright); margin-top: 8px;
    padding-left: 12px; border-left: 2px solid var(--line); line-height: 1.7;
  }}
  .hook::before {{ content: "問い　"; color: var(--washi-dim); font-size: 0.7rem; letter-spacing: 0.15em; }}

  .about, .faq {{ margin-bottom: 56px; }}
  .about h2, .faq h2 {{ font-family: var(--f-serif); font-size: 1.4rem; margin-bottom: 18px; padding-bottom: 10px; border-bottom: 1px solid var(--line); }}
  .about h2 + h2, .about h2:not(:first-child) {{ margin-top: 40px; }}
  .about p {{ font-size: 0.92rem; color: var(--washi-dim); margin-bottom: 14px; }}
  .about p strong {{ color: var(--washi); font-weight: 500; }}
  .about .steps {{ margin: 0 0 14px 1.4em; font-size: 0.92rem; color: var(--washi-dim); }}
  .about .steps li {{ margin-bottom: 8px; }}
  .src-note {{ font-size: 0.75rem !important; }}
  .src-note a {{ color: var(--washi-dim); text-decoration: underline; text-underline-offset: 3px; text-decoration-color: var(--line); }}

  .faq-item {{ border-bottom: 1px solid rgba(201,169,97,0.12); }}
  .faq-item summary {{
    cursor: pointer; padding: 16px 4px; font-size: 0.95rem; font-weight: 500;
    list-style: none; position: relative; padding-right: 28px;
  }}
  .faq-item summary::-webkit-details-marker {{ display: none; }}
  .faq-item summary::after {{
    content: "＋"; position: absolute; right: 4px; top: 16px; color: var(--gold);
  }}
  .faq-item[open] summary::after {{ content: "－"; }}
  .faq-body {{ padding: 0 4px 18px; font-size: 0.88rem; color: var(--washi-dim); }}

  footer {{
    text-align: center; padding: 44px 20px 60px; font-size: 0.75rem;
    color: rgba(255,255,255,0.45); border-top: 1px solid var(--line);
  }}
  footer a {{ color: rgba(255,255,255,0.55); text-decoration: underline; text-underline-offset: 3px; text-decoration-color: rgba(201,169,97,0.4); }}
  .footer-brand {{ font-family: var(--f-serif); color: var(--washi-dim); display: block; margin-bottom: 12px; font-size: 0.95rem; }}

  @media (min-width: 720px) {{
    h1 {{ font-size: 2.3rem; }}
  }}
</style>
</head>
<body>

<nav class="nav">
  <div class="nav-brand"><a href="/" style="color:inherit">城道</a><small>SHIRODO</small></div>
  <a class="nav-cta" href="https://apps.apple.com/app/id6781983836">入手</a>
</nav>

<main>
  <p class="breadcrumb"><a href="/">城道（SHIRODO）</a> › 日本100名城 一覧</p>

  <h1>日本100名城 一覧<span class="visually-hidden">（全100城・地方別・公式番号順）</span></h1>
  <p class="h1-sub">全100城 · 地方別 · 公式番号順</p>

  <p class="lead"><strong>日本100名城</strong>は、公益財団法人日本城郭協会が選定した、日本を代表する100の城です。このページでは全100城を地方別に、公式スタンプラリーの番号順で掲載しています。</p>
  <p class="lead">各城には、登城記録アプリ<strong>城道（SHIRODO）</strong>に収録されている「問い」を添えました。答えを知ってから訪ねると、同じ石垣がちがって見えます。</p>

  <div class="app-callout">
    <h2 class="serif">スタンプ帳の代わりに、スマホで登城記録を。</h2>
    <p>城道（SHIRODO）は、日本100名城の登城記録・メモ・写真を残せる無料iOSアプリ。毎朝ひとつ届く「問い」で、城の文脈を学びながらめぐれます。広告なし・アカウント登録不要。</p>
    <a class="cta-primary" href="https://apps.apple.com/app/id6781983836">App Storeで入手する ›</a>
    <p class="cta-note">無料 · 広告なし · iOS 16以上</p>
  </div>

{toc_html}

{region_html}

  <section class="about" id="about">
    <h2>日本100名城スタンプラリーとは？</h2>
    <p>日本100名城スタンプラリーとは、公益財団法人日本城郭協会が2007年に始めた公式企画で、100名城それぞれに設置された専用スタンプを公式スタンプ帳に集めるものです。全100城を押印すると協会に登城完了の認定を申請でき、達成者として登録されます。押印に有効期間はないため、何年かけてめぐっても構いません。</p>

    <h2>スタンプラリーのやり方は？</h2>
    <p>やり方は3ステップです。公式スタンプ帳を入手し、各城のスタンプ設置場所で押印し、全城達成後に登城認定を申請します。まわる順番は決まっていないので、行きやすい城から始められます。</p>
    <ol class="steps">
      <li>公式ガイドブック『日本100名城に行こう 公式スタンプ帳つき』（770円・税込）を書店・通販で入手する</li>
      <li>各城のスタンプ設置場所（管理事務所・休憩所・資料館など）で、スタンプ帳に直接押印する（別紙に押した切り貼りは原則無効）</li>
      <li>全100城達成後、日本城郭協会へスタンプ帳を郵送して登城認定を申請する</li>
    </ol>
    <p class="src-note">出典: <a href="https://jokaku.jp/" target="_blank" rel="noopener">公益財団法人日本城郭協会</a>（日本100名城の選定は2006年、スタンプラリー開始は2007年）</p>

    <h2>スタンプの代わりにスマホで記録するには？</h2>
    <p><strong>城道（SHIRODO）</strong>は、その旅にもうひとつの楽しみ方を足すアプリです。スタンプの代わりに登城記録・メモ・写真をスマホに残せるので、スタンプ帳を忘れた日も記録が途切れません。そして何より、各城の「なぜ？」から入る問いと物語で、<strong>文脈を知ってから城を訪ねる</strong>体験ができます。</p>
    <p>記録はあなたの端末とiCloudにのみ保存され、開発者のサーバーには送信されません。</p>
    <a class="back-to-toc" href="#toc">▲ 目次へ戻る</a>
  </section>

  <section class="faq" id="faq">
    <h2>よくある質問</h2>
{faq_html}
    <a class="back-to-toc" href="#toc">▲ 目次へ戻る</a>
  </section>

</main>

<footer>
  <span class="footer-brand">城道 SHIRODO</span>
  <p><a href="/">トップページ</a> &nbsp;·&nbsp; <a href="https://katsuhikosakata29-max.github.io/shirodo-privacy/">プライバシーポリシー</a> &nbsp;·&nbsp; © 2026 Katsuhiko Sakata</p>
</footer>

</body>
</html>
'''

import os
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w").write(page)
print(f"OK: {OUT} ({len(page)} bytes, {len(castles)} castles)")
