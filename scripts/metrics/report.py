"""日次ダイジェスト(metrics/DAILY.md)の生成ロジック。純粋関数のみ。"""
import datetime


def _sum_window(rows, key, start, end):
    """rows(date列を持つdictのlist)のうち start <= date < end の key 列合計。"""
    total = 0
    for r in rows:
        d = datetime.date.fromisoformat(r["date"])
        if start <= d < end:
            total += int(r[key])
    return total


def week_over_week(rows, key, today):
    """直近7日間の合計と、その前7日間の合計を返す。"""
    this_start = today - datetime.timedelta(days=7)
    prev_start = today - datetime.timedelta(days=14)
    return (_sum_window(rows, key, this_start, today),
            _sum_window(rows, key, prev_start, this_start))


def _num(row, key):
    """CSV由来の文字列も含めて数値化する。欠損・空文字・不正値はNone。"""
    v = row.get(key)
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def weighted_position(rows, today):
    """直近7日と前7日の、表示回数で加重した平均掲載順位を返す。

    順位は合計できないので加重平均する(GSCの日次positionは当日の加重平均)。
    position列を持たない古い行は無視し、データがない期間はNoneを返す。
    """
    def avg(start, end):
        num = den = 0.0
        for r in rows:
            d = datetime.date.fromisoformat(r["date"])
            if not (start <= d < end):
                continue
            pos, imp = _num(r, "position"), _num(r, "impressions") or 0
            if pos is None or imp <= 0:
                continue
            num += pos * imp
            den += imp
        return round(num / den, 1) if den else None

    this_start = today - datetime.timedelta(days=7)
    prev_start = today - datetime.timedelta(days=14)
    return avg(this_start, today), avg(prev_start, this_start)


def top10_share(rows):
    """表示回数のうち掲載順位10位以内で得たものの割合(%)。母数がなければNone。

    ページ別スナップショットを渡す想定。11位以降=検索結果2ページ目以降は
    ほぼクリックされないため、「表示が増えた」を good と誤読しないための指標。
    """
    top = total = 0.0
    for r in rows:
        pos, imp = _num(r, "position"), _num(r, "impressions") or 0
        if pos is None or imp <= 0:
            continue
        total += imp
        if pos <= 10:
            top += imp
    return round(top / total * 100, 1) if total else None


def _trend_mark(cur, prev):
    if cur > prev:
        return f"↑ (前週 {prev})"
    if cur < prev:
        return f"↓ (前週 {prev})"
    return f"→ (前週 {prev})"


def _position_mark(prev):
    """順位は小さいほど良いので、上下の意味を明示する。"""
    if prev is None:
        return "(前週 データなし)"
    return f"(前週 {prev} / 小さいほど上位)"


def _pos_cell(row):
    pos = _num(row, "position")
    return "-" if pos is None else f"{pos:.1f}"


def build_digest(gsc_daily, gsc_queries, gsc_pages, asc_daily, today,
                 errors=None):
    """Markdownダイジェストを組み立てる。データ欠損は「未取得」と明示する。"""
    lines = [f"# SHIRODO デイリーメトリクス — {today.isoformat()}", ""]
    if errors:
        lines.append("> ⚠️ 取得エラー: " + " / ".join(errors))
        lines.append("")

    # --- Search Console ---
    lines.append("## Search Console (shirodo.com)")
    if gsc_daily:
        clicks_cur, clicks_prev = week_over_week(gsc_daily, "clicks", today)
        imp_cur, imp_prev = week_over_week(gsc_daily, "impressions", today)
        pos_cur, pos_prev = weighted_position(gsc_daily, today)
        lines += [
            f"- 直近7日クリック数: **{clicks_cur}** {_trend_mark(clicks_cur, clicks_prev)}",
            f"- 直近7日表示回数: **{imp_cur}** {_trend_mark(imp_cur, imp_prev)}",
            f"- 直近7日 平均掲載順位: **{pos_cur if pos_cur is not None else '不明'}** "
            f"{_position_mark(pos_prev)}",
        ]
        share = top10_share(gsc_pages)
        if share is not None:
            lines.append(
                f"- うち順位10位以内の表示: **{share}%** "
                "(11位以降はほぼクリックされない)")
        latest = max(gsc_daily, key=lambda r: r["date"])
        lines.append(
            f"- 最新日 {latest['date']}: クリック {latest['clicks']}"
            f" / 表示 {latest['impressions']} / 順位 {_pos_cell(latest)}")
    else:
        lines.append("- データ未取得")

    if gsc_queries:
        lines += ["", "### 上位クエリ (直近10日)",
                  "| クエリ | クリック | 表示 | 順位 |", "|---|---|---|---|"]
        for q in gsc_queries[:10]:
            lines.append(f"| {q['query']} | {q['clicks']} | {q['impressions']}"
                         f" | {_pos_cell(q)} |")

    if gsc_pages:
        lines += ["", "### 上位ページ (直近10日)",
                  "| ページ | クリック | 表示 | 順位 |", "|---|---|---|---|"]
        for p in gsc_pages[:10]:
            lines.append(f"| {p['page']} | {p['clicks']} | {p['impressions']}"
                         f" | {_pos_cell(p)} |")

    # --- App Store ---
    lines += ["", "## App Store (城道)"]
    if asc_daily:
        dl_cur, dl_prev = week_over_week(asc_daily, "first_downloads", today)
        re_cur, re_prev = week_over_week(asc_daily, "redownloads", today)
        lines += [
            f"- 直近7日初回DL: **{dl_cur}** {_trend_mark(dl_cur, dl_prev)}",
            f"- 直近7日再DL: **{re_cur}** {_trend_mark(re_cur, re_prev)}",
        ]
        latest = max(asc_daily, key=lambda r: r["date"])
        lines.append(
            f"- 最新日 {latest['date']}: 初回DL {latest['first_downloads']}"
            f" / 再DL {latest['redownloads']} / 更新 {latest['updates']}")
    else:
        lines.append("- データ未取得")

    lines += [
        "",
        "---",
        "*自分のアクセス/DLも含む数値。絶対数ではなく前週比の傾きを見ること。*",
        "*表示回数の増加は順位とセットで読むこと。"
        "順位50位前後の表示が増えても流入には結びつかない。*",
        f"*生成: {today.isoformat()} (scripts/metrics/run_daily.py)*",
    ]
    return "\n".join(lines) + "\n"


def notification_summary(gsc_daily, asc_daily, today):
    """macOS通知用の1行サマリー。"""
    parts = []
    if gsc_daily:
        c, _ = week_over_week(gsc_daily, "clicks", today)
        i, _ = week_over_week(gsc_daily, "impressions", today)
        p, _ = weighted_position(gsc_daily, today)
        pos = f"/順位{p}" if p is not None else ""
        parts.append(f"GSC 7日: クリック{c}/表示{i}{pos}")
    if asc_daily:
        d, _ = week_over_week(asc_daily, "first_downloads", today)
        parts.append(f"App 7日: DL{d}")
    return " | ".join(parts) if parts else "データ未取得"
