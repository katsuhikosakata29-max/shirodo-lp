# -*- coding: utf-8 -*-
"""data/level.json から /guide/level/index.html を生成する

難易度レベルは one_way_min（片道分）と elevation_gain_m（標高差m）から機械判定する。
判定を上書きしたい城は data 側に "level_override" を持たせる。
城の基本情報（かな・県・分類）はアプリ本体の castles.json から引く。
"""
import json, html, os
from datetime import date

TODAY = date.today().isoformat()
TODAY_JA = f"{date.today().year}年{date.today().month}月{date.today().day}日"

CASTLES_SRC = "/Users/sakatakatsuhiko/Developer/shirodo/native/src/data/castles.json"
DATA_SRC = os.path.join(os.path.dirname(__file__), "..", "data", "level.json")
OUT = os.path.join(os.path.dirname(__file__), "..", "guide", "level", "index.html")

LEVELS = {
    1: {"label": "散策", "css": "lv-c1", "desc": "登りは20分未満の平地〜石段。普段の靴やスニーカーで問題なし（例：仙台城・松江城・姫路城）"},
    2: {"label": "登山", "css": "lv-c2", "desc": "登りが片道20分以上、または標高差100m以上の山道。ここからは登山。歩き慣れたスニーカーと飲み物を（例：鳥取城・備中松山城）"},
    3: {"label": "本格登山", "css": "lv-c3", "desc": "登りが片道45分超、または標高差300m超。軽登山のつもりで計画を（例：麓から歩く場合の高取城・岐阜城）"},
}

WARN_WORDS = ("クマ", "熊", "冬季閉鎖", "冬期閉鎖", "日没", "滑落")


def esc(s):
    return html.escape(str(s or ""), quote=True)


def calc_level(c):
    if c.get("level_override"):
        return int(c["level_override"])
    m = c.get("one_way_min")
    e = c.get("elevation_gain_m")
    if m is None and e is None:
        raise ValueError(f"{c['name']}: one_way_min / elevation_gain_m が両方 null（level_override が必要）")
    m = m or 0
    e = e or 0
    if m > 45 or e > 300:
        return 3
    if m >= 20 or e >= 100:
        return 2
    return 1


def mt_glyphs(level):
    one = ('<svg width="11" height="9" viewBox="0 0 11 9" fill="currentColor" aria-hidden="true">'
           '<path d="M5.5 0 11 9H0Z"/></svg>')
    return f'<span class="mt">{one * level}</span>'


def lv_txt(level):
    lv = LEVELS[level]
    return (f'<span class="lv-txt {lv["css"]}">{mt_glyphs(level)}'
            f'<b>Lv.{level}</b>{esc(lv["label"])}</span>')


def caution_html(text):
    warn = any(w in text for w in WARN_WORDS)
    return f'<span class="warn">{esc(text)}</span>' if warn else esc(text)


def warn_note(text):
    for w in WARN_WORDS:
        if w in text:
            return f'<span class="warn">{esc(text)}</span>'
    return esc(text)


# ---- データ読み込み ----
castles_master = {int(c["no"]): c for c in json.load(open(CASTLES_SRC)) if c.get("is_100meijo")}
data = json.load(open(DATA_SRC))
rows = data["castles"]
for c in rows:
    m = castles_master[int(c["no"])]
    c["kana"] = m["name_kana"]
    c["pref"] = m["prefecture"].replace("県", "").replace("府", "").replace("都", "").replace("道", "")
    c["pref_full"] = m["prefecture"]
    c["city"] = m.get("city", "")
    c["type"] = m.get("type", "")
    c["level"] = calc_level(c)

rows.sort(key=lambda c: (-c["level"], (c.get("one_way_min") or 0) * -1, int(c["no"])))
count_tozan = len([c for c in rows if c["level"] >= 2])
count_total = len(rows)

# ---- 詳細行（Lv.2以上＝登山の城のみ詳述。案C′: PCは表・スマホは積み重ね）----
def detail_rows_html(c):
    ow = f'約{c["one_way_min"]}分' if c.get("one_way_min") is not None else "—"
    el = f'約{c["elevation_gain_m"]}m' if c.get("elevation_gain_m") is not None else "—"
    shoes = esc(c.get("shoes") or "—")
    note = "・".join(caution_html(f) for f in (c.get("cautions") or [])[:4])
    detail = f'<p class="route">経路: {esc(c["easiest_route"])}'
    if c.get("on_foot_alt"):
        detail += f'（{esc(c["on_foot_alt"])}）'
    detail += "</p>"
    if c.get("memo"):
        visited = f'<span class="visited">{esc(c["visited"])} 実登</span>' if c.get("visited") else ""
        detail += f'<p class="exp">{esc(c["memo"])}{visited}</p>'
    if c.get("sources"):
        srcs = c["sources"]
        if len(srcs) == 1:
            links = f'<a href="{esc(srcs[0])}" target="_blank" rel="noopener">出典を見る</a>'
        else:
            links = "出典を見る: " + "・".join(
                f'<a href="{esc(u)}" target="_blank" rel="noopener">{i}</a>'
                for i, u in enumerate(srcs, 1))
        detail += f'<p class="src">{links}</p>'
    return f'''          <tr class="main" id="c{c["no"]}">
            <td class="cname">{esc(c["name"])}<small class="kana">{esc(c["kana"])}</small><small class="pref">{esc(c["pref_full"])}{esc(c["city"])} · No.{c["no"]} · 分類は「{esc(c["type"])}」</small></td>
            <td class="stat" data-k="登り">{ow}</td>
            <td class="stat" data-k="標高差">{el}</td>
            <td class="stat" data-k="靴">{shoes}</td>
            <td class="note-cell">{note}</td>
          </tr>
          <tr class="detail">
            <td colspan="5">{detail}</td>
          </tr>'''


cards_by_level = {}
for lv in (3, 2):
    items = [c for c in rows if c["level"] == lv]
    if items:
        cards_by_level[lv] = "\n".join(detail_rows_html(c) for c in items)

card_sections = []
for lv in (3, 2):
    if lv not in cards_by_level:
        continue
    sub = "— ここを知らずに行くと困る" if lv == 2 else "— 軽登山のつもりで計画を"
    card_sections.append(f'''  <section id="lv{lv}">
    <h2>Lv.{lv}「{LEVELS[lv]["label"]}」の城 <span class="h2-sub">{sub}</span></h2>
    <div class="tbl-wrap">
      <table class="ctable">
        <thead>
          <tr><th>城名</th><th>登り</th><th>標高差</th><th>靴</th><th>注意</th></tr>
        </thead>
        <tbody>
{cards_by_level[lv]}
        </tbody>
      </table>
    </div>
    <a class="back-to-toc" href="#toc">▲ 目次へ戻る</a>
  </section>''')
card_sections_html = "\n\n".join(card_sections)

# ---- 一覧表 ----
def table_row(c):
    ow = f'約{c["one_way_min"]}分' if c.get("one_way_min") is not None else "—"
    el = f'約{c["elevation_gain_m"]}m' if c.get("elevation_gain_m") is not None else "—"
    note_items = [warn_note(x) for x in (c.get("cautions") or [])[:2]]
    if c.get("on_foot_alt"):
        note_items.append(f'<span class="alt">徒歩のみの場合：{esc(c["on_foot_alt"])}</span>')
    notes = "・".join(note_items) or "—"
    return f'''            <tr>
              <td><a class="tname" href="#c{c["no"]}">{esc(c["name"])}</a><span class="tkana">{esc(c["kana"])} · {esc(c["pref"])}</span></td>
              <td class="lv-cell">{lv_txt(c["level"])}</td>
              <td class="stat" data-k="登り">{ow}</td>
              <td class="stat" data-k="標高差">{el}</td>
              <td class="stat" data-k="靴">{esc(c.get("shoes") or "—")}</td>
              <td class="tnote">{notes}</td>
            </tr>''' if c["level"] >= 2 else f'''            <tr>
              <td><span class="tname">{esc(c["name"])}</span><span class="tkana">{esc(c["kana"])} · {esc(c["pref"])}</span></td>
              <td class="lv-cell">{lv_txt(c["level"])}</td>
              <td class="stat" data-k="登り">{ow}</td>
              <td class="stat" data-k="標高差">{el}</td>
              <td class="stat" data-k="靴">{esc(c.get("shoes") or "—")}</td>
              <td class="tnote">{notes}</td>
            </tr>'''


table_rows_html = "\n".join(table_row(c) for c in rows)

# ---- FAQ ----
faqs = [
    ("100名城のうち「登山」になる城はいくつありますか？",
     f"当ガイドの調査済みの城では、登りが片道20分以上の山道になるLv.2以上が{count_tozan}城あります。ただしロープウェー・リフト・シャトルバスで上部まで行ける城も多く、アクセス手段しだいで難易度は大きく変わります。本ページの難易度は「最も楽な一般的経路」を基準にしています。"),
    ("鳥取城の登山はきついですか？",
     "山上ノ丸（久松山山頂・標高263m）までは登り30〜40分・標高差約240mの登山道で、リフトや車道はありません。歩き慣れたスニーカーで登れますが、飲み物は必須で、夏の暑い日は汗だくになる本格的な登りです。登山道入口にはクマ注意の掲示があります。山麓部（天球丸・仁風閣周辺）だけの見学なら登山は不要です。"),
    ("山城にはどんな持ち物が必要ですか？",
     "歩き慣れたスニーカーで登れる城がほとんどですが、雨のあとは滑りやすいので底のしっかりした靴が安心です。飲み物・タオル・虫除け（夏）・軍手・熊鈴などを基本の持ち物に足してください。詳しくは「城巡りの持ち物リスト」のガイドで山城編としてまとめています。"),
    ("クマが心配です。対策はありますか？",
     "登城前に自治体・観光協会サイトで出没情報を確認し、熊鈴を着け、できるだけ複数人で、早朝・夕方の時間帯を避けて登るのが基本です。掲示や立入規制が出ている場合は従ってください。"),
]
faq_jsonld = ",\n  ".join(
    '{"@type": "Question", "name": %s,\n   "acceptedAnswer": {"@type": "Answer", "text": %s}}'
    % (json.dumps(q, ensure_ascii=False), json.dumps(a, ensure_ascii=False))
    for q, a in faqs)
faq_html = "\n".join(f'''    <details class="faq-item">
      <summary>{esc(q)}</summary>
      <div class="faq-body">{esc(a)}</div>
    </details>''' for q, a in faqs)

# ---- 目次（カードのある難易度だけ載せる） ----
toc_card_items = "\n".join(
    f'      <li><a href="#lv{lv}">Lv.{lv}「{LEVELS[lv]["label"]}」の城</a></li>'
    for lv in (3, 2) if lv in cards_by_level)

# ---- 凡例 ----
legend_html = "\n".join(f'''        <div class="legend-row">
          {lv_txt(lv)}
          <span>{esc(LEVELS[lv]["desc"])}</span>
        </div>''' for lv in (1, 2, 3))

published = data.get("published", TODAY)
published_ja = f"{int(published[:4])}年{int(published[5:7])}月{int(published[8:10])}日"

page = f'''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>100名城の登城難易度一覧｜「実は登山」の城はどこ？ | 城道（SHIRODO）</title>
<meta name="description" content="100名城を「現代の登城のきつさ」でLv.1〜3に分類。登りの時間・標高差・クマ注意など現地の注意を一覧で解説。鳥取城・月山富田城の実登経験に基づく、登城記録アプリ城道（SHIRODO）のガイド。">
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://shirodo.com/guide/level/">
<meta property="og:title" content="100名城の登城難易度一覧｜「実は登山」の城はどこ？">
<meta property="og:description" content="100名城を登城のきつさでLv.1〜3に分類。登りの時間・標高差・現地の注意を一覧で解説。">
<meta property="og:image" content="https://shirodo.com/assets/kumamoto-castle.jpg">
<meta property="og:url" content="https://shirodo.com/guide/level/">
<meta property="og:type" content="article">
<meta property="og:site_name" content="城道（SHIRODO）">
<meta property="og:locale" content="ja_JP">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="100名城の登城難易度一覧｜「実は登山」の城はどこ？">
<meta name="twitter:description" content="100名城を登城のきつさでLv.1〜3に分類。登りの時間・標高差・現地の注意を一覧で解説。">
<meta name="twitter:image" content="https://shirodo.com/assets/kumamoto-castle.jpg">
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🏯</text></svg>">
<script type="application/ld+json">
{{
 "@context": "https://schema.org",
 "@type": "BreadcrumbList",
 "itemListElement": [
  {{"@type": "ListItem", "position": 1, "name": "城道（SHIRODO）", "item": "https://shirodo.com/"}},
  {{"@type": "ListItem", "position": 2, "name": "100名城の登城難易度一覧", "item": "https://shirodo.com/guide/level/"}}
 ]
}}
</script>
<script type="application/ld+json">
{{
 "@context": "https://schema.org",
 "@type": "Article",
 "headline": "100名城の登城難易度一覧｜「実は登山」の城はどこ？",
 "description": "100名城を現代の登城のきつさでLv.1〜3に分類。登りの時間・標高差・現地の注意を一覧で解説。",
 "inLanguage": "ja-JP",
 "datePublished": "{published}",
 "dateModified": "{TODAY}",
 "author": {{"@type": "Person", "@id": "https://shirodo.com/#author", "name": "城道（SHIRODO）開発者", "url": "https://shirodo.com/"}},
 "publisher": {{"@type": "Organization", "name": "城道（SHIRODO）", "url": "https://shirodo.com/"}},
 "mainEntityOfPage": "https://shirodo.com/guide/level/",
 "image": "https://shirodo.com/assets/kumamoto-castle.jpg"
}}
</script>
<script type="application/ld+json">
{{
 "@context": "https://schema.org",
 "@type": "FAQPage",
 "inLanguage": "ja-JP",
 "mainEntity": [
  {faq_jsonld}
 ]
}}
</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&family=Shippori+Mincho:wght@500;700&display=swap">
<style>
  :root {{
    --gold: #c9a961;
    --gold-bright: #e5c67d;
    --ochre: #c97b3f;
    --vermilion: #a33a2a;
    --vermilion-text: #d85c45;
    --warn: #d98a77;
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

  main {{ max-width: 720px; margin: 0 auto; padding: 110px 20px 60px; }}
  .breadcrumb {{ font-size: 0.75rem; color: var(--washi-dim); margin-bottom: 28px; }}
  .breadcrumb a {{ color: var(--washi-dim); text-decoration: underline; text-underline-offset: 3px; text-decoration-color: var(--line); }}

  h1 {{ font-family: var(--f-serif); font-size: 1.75rem; line-height: 1.5; margin-bottom: 10px; }}
  .article-meta {{ font-size: 0.75rem; color: var(--washi-dim); margin-bottom: 26px; }}
  .lead-answer {{
    padding: 20px 22px; margin-bottom: 36px;
    background: var(--sumi-2); border-left: 3px solid var(--gold); border-radius: 0 10px 10px 0;
    font-size: 0.95rem;
  }}
  .lead-answer strong {{ color: var(--washi); font-weight: 700; }}

  .toc {{
    background: var(--sumi-2); border: 1px solid var(--line); border-radius: 12px;
    padding: 20px 24px; margin-bottom: 48px;
    scroll-margin-top: 76px;
  }}
  .toc-title {{
    font-family: var(--f-serif); font-size: 0.9rem; color: var(--gold);
    letter-spacing: 0.2em; margin-bottom: 10px;
  }}
  .toc ol {{ list-style: none; }}
  .toc li {{ border-bottom: 1px solid rgba(201,169,97,0.12); }}
  .toc li:last-child {{ border-bottom: none; }}
  .toc a {{ display: block; padding: 9px 2px; font-size: 0.9rem; color: var(--washi); }}
  .toc a:hover {{ color: var(--gold-bright); }}

  section {{ margin-bottom: 52px; scroll-margin-top: 76px; }}
  h2 {{ font-family: var(--f-serif); font-size: 1.35rem; margin-bottom: 16px; padding-bottom: 10px; border-bottom: 1px solid var(--line); }}
  .h2-sub {{ font-size: 0.72rem; color: var(--washi-dim); font-family: var(--f-sans); font-weight: 400; }}
  h3 {{ font-family: var(--f-serif); font-size: 1.05rem; color: var(--gold-bright); margin: 24px 0 10px; }}
  p {{ font-size: 0.92rem; color: var(--washi-dim); margin-bottom: 14px; }}
  p strong, li strong {{ color: var(--washi); font-weight: 500; }}
  .src-note {{ font-size: 0.75rem; }}
  .src-note a {{ color: var(--washi-dim); text-decoration: underline; text-underline-offset: 3px; text-decoration-color: var(--line); }}
  .back-to-toc {{
    display: inline-block; margin-top: 18px; font-size: 0.78rem;
    color: var(--washi-dim); text-decoration: underline;
    text-underline-offset: 3px; text-decoration-color: var(--line);
  }}
  .back-to-toc:hover {{ color: var(--gold-bright); }}

  /* 難易度の視覚言語 */
  .mt {{ display: inline-flex; gap: 2px; align-items: flex-end; }}
  .mt svg {{ display: block; }}
  .lv-c1 {{ color: var(--gold); }}
  .lv-c2 {{ color: var(--ochre); }}
  .lv-c3 {{ color: var(--vermilion-text); }}
  .lv-txt {{
    display: inline-flex; align-items: center; gap: 7px;
    font-size: 0.72rem; letter-spacing: 0.08em;
    white-space: nowrap;
  }}
  .lv-txt b {{ font-family: var(--f-serif); font-weight: 500; font-size: 0.8rem; }}

  .legend {{ display: grid; gap: 10px; margin: 18px 0 8px; }}
  .legend-row {{
    display: grid; grid-template-columns: max-content 1fr; gap: 14px; align-items: baseline;
    padding: 10px 2px; border-bottom: 1px solid rgba(201,169,97,0.1);
    font-size: 0.85rem; color: var(--washi-dim);
  }}
  .legend-row b {{ color: var(--washi); font-weight: 500; }}

  .visited {{
    font-size: 0.7rem; color: var(--gold-bright); letter-spacing: 0.1em;
    border-bottom: 1px solid var(--line); padding-bottom: 1px; margin-left: 6px;
  }}

  .tbl-wrap {{ overflow-x: auto; margin: 20px 0 8px; }}
  .ctable {{ border-collapse: collapse; width: 100%; font-size: 0.82rem; }}
  .ctable thead th {{
    font-family: var(--f-serif); font-weight: 500; font-size: 0.75rem; letter-spacing: 0.1em;
    color: var(--gold); text-align: left; padding: 8px 14px 8px 2px;
    border-bottom: 1px solid var(--line);
    white-space: nowrap;
  }}
  .ctable tbody td {{
    padding: 13px 14px 13px 2px; border-bottom: 1px solid rgba(201,169,97,0.1);
    color: var(--washi-dim); vertical-align: top;
    font-variant-numeric: tabular-nums;
  }}
  .ctable tbody tr:last-child td {{ border-bottom: none; }}
  .ctable tr.main {{ scroll-margin-top: 76px; }}
  .ctable tr.main td {{ border-bottom: none; padding-bottom: 4px; }}
  .ctable tr.detail td {{ padding-top: 0; font-size: 0.76rem; }}
  .ctable p {{ margin-bottom: 0; }}
  .ctable td .tname {{ font-family: var(--f-serif); color: var(--washi); font-size: 0.95rem; white-space: nowrap; }}
  .ctable td a.tname {{ text-decoration: underline; text-underline-offset: 3px; text-decoration-color: var(--line); }}
  .ctable td .tkana {{ display: block; font-size: 0.65rem; letter-spacing: 0.1em; color: var(--washi-dim); }}
  .ctable td.cname {{ font-family: var(--f-serif); color: var(--washi); font-size: 0.95rem; min-width: 165px; }}
  .ctable td.cname .kana {{ font-size: 0.65rem; letter-spacing: 0.1em; color: var(--washi-dim); font-family: var(--f-sans); margin-left: 6px; }}
  .ctable td.cname .pref {{ display: block; font-size: 0.65rem; color: var(--washi-dim); font-family: var(--f-sans); }}
  .ctable td.stat {{ white-space: nowrap; color: var(--washi); }}
  .ctable td.tnote, .ctable td.note-cell {{ font-size: 0.76rem; }}
  .ctable .warn {{ color: var(--warn); }}
  .ctable td .alt {{ color: var(--washi-dim); opacity: 0.85; }}
  .ctable .route {{ font-size: inherit; }}
  .ctable .exp {{ font-size: 0.8rem; margin-top: 8px; }}
  .ctable .exp::before {{ content: "登城メモ　"; font-size: 0.68rem; letter-spacing: 0.18em; color: var(--gold); }}
  .ctable .src {{ font-size: 0.7rem; margin-top: 6px; }}
  .ctable .src a {{ color: var(--washi-dim); text-decoration: underline; text-underline-offset: 3px; text-decoration-color: var(--line); }}
  .tbl-cap {{ font-size: 0.72rem; color: var(--washi-dim); margin-top: 10px; }}
  @media (max-width: 619px) {{
    .ctable, .ctable tbody, .ctable tr, .ctable td {{ display: block; }}
    .ctable thead {{ display: none; }}
    .ctable tbody tr {{ padding: 16px 0; border-bottom: 1px solid rgba(201,169,97,0.1); }}
    .ctable tbody td {{ padding: 0; border-bottom: none; }}
    .ctable tbody tr:last-child {{ border-bottom: none; }}
    .ctable tr.main {{ border-bottom: none; padding-bottom: 0; }}
    .ctable tr.main td {{ padding-bottom: 0; }}
    .ctable tr.detail {{ padding-top: 6px; }}
    .ctable td.cname {{ font-size: 1.05rem; }}
    .ctable td .tname {{ font-size: 1.05rem; }}
    .ctable td .tkana {{ display: inline; margin-left: 6px; }}
    .ctable td.lv-cell {{ margin-top: 2px; }}
    .ctable td.stat {{ display: inline-block; margin: 4px 16px 0 0; }}
    .ctable td.stat::before {{ content: attr(data-k); font-size: 0.68rem; letter-spacing: 0.12em; color: var(--gold); margin-right: 6px; }}
    .ctable td.tnote, .ctable td.note-cell {{ margin-top: 6px; }}
    .ctable td.note-cell::before, .ctable td.tnote::before {{ content: "注意 — "; color: var(--warn); font-size: 0.72rem; letter-spacing: 0.1em; }}
  }}

  .faq-item {{ border-bottom: 1px solid rgba(201,169,97,0.12); }}
  .faq-item summary {{
    cursor: pointer; padding: 16px 4px; font-size: 0.95rem; font-weight: 500;
    list-style: none; position: relative; padding-right: 28px; color: var(--washi);
  }}
  .faq-item summary::-webkit-details-marker {{ display: none; }}
  .faq-item summary::after {{
    content: "＋"; position: absolute; right: 4px; top: 16px; color: var(--gold);
  }}
  .faq-item[open] summary::after {{ content: "－"; }}
  .faq-body {{ padding: 0 4px 18px; font-size: 0.88rem; color: var(--washi-dim); }}

  .bridge-slot {{ margin: 36px 0 48px; }}
  .bridge-line {{ padding: 14px 2px; border-top: 1px solid var(--line); font-size: 0.9rem; }}
  .bridge-line span {{ color: var(--washi-dim); }}
  .bridge-line a {{ color: var(--gold-bright); text-decoration: underline; text-underline-offset: 3px; }}
  .bridge-chip {{
    display: flex; align-items: center; gap: 14px;
    padding: 14px 16px 14px 14px;
    background: var(--sumi-3); border: 1px solid var(--line); border-radius: 10px;
  }}
  .bridge-chip .badge {{
    width: 30px; height: 30px; flex-shrink: 0; border-radius: 50%;
    border: 1px solid var(--gold); display: flex; align-items: center; justify-content: center;
    font-family: var(--f-serif); font-size: 0.8rem; color: var(--gold-bright);
  }}
  .bridge-chip .text {{ font-size: 0.86rem; color: var(--washi-dim); flex: 1; }}
  .bridge-chip .text b {{ color: var(--washi); font-weight: 500; }}
  .bridge-chip a.arrow {{ color: var(--gold-bright); font-size: 0.83rem; flex-shrink: 0; text-decoration: none; white-space: nowrap; }}
  .bridge-box {{
    padding: 16px 18px;
    background: var(--sumi-2); border-left: 3px solid var(--gold); border-radius: 0 10px 10px 0;
  }}
  .bridge-box .q {{ font-size: 0.9rem; color: var(--washi); margin-bottom: 8px; font-weight: 500; }}
  .bridge-box .link-row {{ font-size: 0.84rem; margin-bottom: 0; }}
  .bridge-box .link-row span {{ color: var(--washi-dim); }}
  .bridge-box .link-row a {{ color: var(--gold-bright); text-decoration: underline; text-underline-offset: 3px; font-weight: 500; }}

  .author-box {{
    display: flex; gap: 4px; flex-direction: column;
    padding: 18px 20px; margin-bottom: 48px;
    background: var(--sumi-2); border: 1px solid var(--line); border-radius: 12px;
    font-size: 0.8rem; color: var(--washi-dim);
  }}
  .author-box strong {{ color: var(--washi); font-weight: 500; }}

  footer {{
    text-align: center; padding: 44px 20px 60px; font-size: 0.75rem;
    color: rgba(255,255,255,0.45); border-top: 1px solid var(--line);
  }}
  footer a {{ color: rgba(255,255,255,0.55); text-decoration: underline; text-underline-offset: 3px; text-decoration-color: rgba(201,169,97,0.4); }}
  .footer-brand {{ font-family: var(--f-serif); color: var(--washi-dim); display: block; margin-bottom: 12px; font-size: 0.95rem; }}

  @media (min-width: 720px) {{
    h1 {{ font-size: 2.1rem; }}
  }}
</style>
<script defer src="/assets/analytics.js"></script>
</head>
<body>

<nav class="nav">
  <div class="nav-brand"><a href="/" style="color:inherit">城道</a><small>SHIRODO</small></div>
  <a class="nav-cta" href="https://apps.apple.com/app/id6781983836">入手</a>
</nav>

<main>
  <p class="breadcrumb"><a href="/">城道（SHIRODO）</a> › 100名城の登城難易度一覧</p>

  <h1>100名城の登城難易度一覧<br>「実は登山」の城はどこ？</h1>
  <p class="article-meta">更新日: {TODAY_JA} · 執筆: 城道（SHIRODO）開発者</p>

  <div class="lead-answer">
    <p style="margin-bottom:0">100名城には、<strong>登りが片道20分以上の山道になる「登山」の城が{count_tozan}城以上</strong>あります。しかも城の分類ではそれが分かりません。姫路城と鳥取城は同じ「平山城」ですが、姫路城では登りを意識することがないのに、鳥取城の山上ノ丸はリフトも車道もなく<strong>登り30〜40分・標高差約240m</strong>の登山道です。このページでは山城を中心とした{count_total}城を「現代の登城のきつさ」でLv.1〜3に分け、登りの時間・標高差・現地の注意を一覧にしました。</p>
  </div>

  <nav class="toc" id="toc" aria-label="目次">
    <p class="toc-title">目 次</p>
    <ol>
      <li><a href="#story">その城、実は登山です</a></li>
      <li><a href="#legend">難易度の見かた（判定基準）</a></li>
{toc_card_items}
      <li><a href="#table">難易度データ一覧表</a></li>
      <li><a href="#about-data">データについて</a></li>
      <li><a href="#faq">よくある質問</a></li>
    </ol>
  </nav>

  <section id="story">
    <h2>その城、実は登山です</h2>
    <p>鳥取城跡の登山道入口には「熊に注意」の掲示があります。引き返そうかと思ったとき、熊鈴を着けた地元の方が「大丈夫だよ、たまに猪がいるくらい」と登っていきました。その言葉に背中を押されて登った片道30分は、観光ではなく、はっきりと登山でした。</p>
    <p>それでも鳥取城の分類は、姫路城と同じ「平山城」です。<strong>山城・平山城・平城という分類は築城時の地形の話であって、いまの登城のきつさを教えてくれません</strong>。同じ旅でめぐった松江城や姫路城では「登り」を意識することすらなかったのに、月山富田城は登城者のいない虫だらけの山道でした。だから、実際に登った経験と各城の公式情報から、「現代の登城のきつさ」で独自に3段階に分けました。</p>
  </section>

  <section id="legend">
    <h2>難易度の見かた（判定基準）</h2>
    <p>難易度は、<strong>一般観光客が本丸・天守に至る最も楽な経路</strong>（ロープウェー・リフト・シャトルバス・車の利用を含む）を基準に、その経路の<strong>「登り」の時間と標高差</strong>で判定しています。時間は登りだけの目安で、<strong>城内の見学時間は含みません</strong>（姫路城のように、登りは短くても見学に1時間半〜2時間かかる城もあります）。麓から歩く場合に難易度が上がる城は、各城の欄に補足しています。</p>
    <div class="legend">
{legend_html}
    </div>
    <p class="src-note">判定基準: Lv.3＝登り片道45分超または標高差300m超 / Lv.2＝登り片道20分以上または標高差100m以上 / Lv.1＝それ未満。</p>
    <a class="back-to-toc" href="#toc">▲ 目次へ戻る</a>
  </section>

{card_sections_html}

  <section id="table">
    <h2>難易度データ一覧表</h2>
    <p>調査済みの{count_total}城を難易度が高い順に並べています。城名をタップすると各城の詳細に移動します（Lv.2以上）。</p>
    <div class="tbl-wrap">
      <table class="ctable">
        <thead>
          <tr><th>城</th><th>難易度</th><th>登り</th><th>標高差</th><th>靴</th><th>注意</th></tr>
        </thead>
        <tbody>
{table_rows_html}
        </tbody>
      </table>
    </div>
    <p class="tbl-cap">「登り」は最も楽な一般的経路での登り徒歩時間の目安で、城内の見学時間は含みません。体力・天候・季節で大きく変わります。残りの城（多くは平城・平山城でLv.1相当）も順次追加していきます。</p>
    <a class="back-to-toc" href="#toc">▲ 目次へ戻る</a>
  </section>

  <section id="about-data">
    <h2>データについて</h2>
    <p>所要時間・標高差は、各城の自治体・観光協会・公式サイトの公開情報をもとにし、幅がある場合は代表値を採用しています。鳥取城・月山富田城・松江城・姫路城は2026年8月に実際に登城して確認しました（「実登」表示）。現地の状況（クマ出没・通行止め・リフト運休など）は変わるため、<strong>登城前に必ず公式の最新情報を確認してください</strong>。</p>
    <p class="src-note">各城の出典は詳細欄の「出典を見る」から確認できます。誤りを見つけた場合は<a href="/support/">サポート</a>からお知らせください。山城の装備は<a href="/guide/mochimono/">城巡りの持ち物リスト</a>、訪ねたあとの記録は<a href="/guide/kiroku/">登城記録のつけ方</a>、全100城の一覧は<a href="/100meijo/">日本100名城 一覧</a>へ。</p>
    <a class="back-to-toc" href="#toc">▲ 目次へ戻る</a>
  </section>

  <div id="bridge-slot" class="bridge-slot"></div>
  <script>
  (function () {{
    var APP_URL = 'https://apps.apple.com/app/id6781983836';
    var variants = {{
      C1: '<p class="bridge-line"><span>登った城の記録は、山頂でその場で残せます。</span> <a href="' + APP_URL + '" class="bridge-link bridge-link--c1">城道（しろどう）を見る ›</a></p>',
      C2: '<div class="bridge-chip"><span class="badge">城</span><span class="text">登城の記録とメモは、<b>城道（しろどう）</b>という無料アプリでも残せます。</span><a href="' + APP_URL + '" class="arrow bridge-link bridge-link--c2">見てみる ›</a></div>',
      C3: '<div class="bridge-box"><p class="q">登山になる城ほど、登った記録を残したくなります。</p><p class="link-row"><span>城道（しろどう）は、その場で登城の記録とメモを残せる無料アプリです。</span> <a href="' + APP_URL + '" class="bridge-link bridge-link--c3">App Storeで見る ›</a></p></div>'
    }};
    var keys = Object.keys(variants);
    var STORAGE_KEY = 'level_bridge_variant';
    var variant = null;
    try {{ variant = localStorage.getItem(STORAGE_KEY); }} catch (e) {{}}
    if (!variant || !variants[variant]) {{
      variant = keys[Math.floor(Math.random() * keys.length)];
      try {{ localStorage.setItem(STORAGE_KEY, variant); }} catch (e) {{}}
    }}
    document.getElementById('bridge-slot').innerHTML = variants[variant];
    document.addEventListener('DOMContentLoaded', function () {{
      if (window.posthog) {{
        posthog.capture('bridge_variant_view', {{ variant: variant, page_path: location.pathname }});
      }}
    }});
  }})();
  </script>

  <section id="faq">
    <h2>よくある質問</h2>
{faq_html}
    <a class="back-to-toc" href="#toc">▲ 目次へ戻る</a>
  </section>

  <div class="author-box">
    <span><strong>この記事について</strong></span>
    <span>執筆: 城道（SHIRODO）開発者。日本100名城の登城記録アプリを開発しながら、自身も城をめぐっています。2026年8月に松江城・月山富田城・鳥取城・姫路城を登城し、「観光のつもりが登山だった」経験からこのページを作りました。</span>
    <span>公開: {published_ja} / 最終更新: {TODAY_JA}</span>
  </div>

</main>

<footer>
  <span class="footer-brand">城道 SHIRODO</span>
  <p><a href="/">トップページ</a> &nbsp;·&nbsp; <a href="/shindan/">城めぐりタイプ診断</a> &nbsp;·&nbsp; <a href="/100meijo/">日本100名城 一覧</a> &nbsp;·&nbsp; <a href="/guide/mochimono/">城巡りの持ち物ガイド</a> &nbsp;·&nbsp; <a href="/guide/kiroku/">登城記録のつけ方</a> &nbsp;·&nbsp; <a href="/support/">サポート</a> &nbsp;·&nbsp; <a href="/privacy/">プライバシーポリシー</a> &nbsp;·&nbsp; © 2026 城道（SHIRODO）</p>
</footer>

</body>
</html>
'''

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w") as f:
    f.write(page)
print(f"OK: {len(rows)}城（登山レベルLv.2以上 {count_tozan}城）→ {os.path.relpath(OUT)}")
