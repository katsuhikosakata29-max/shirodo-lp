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


def _trend_mark(cur, prev):
    if cur > prev:
        return f"↑ (前週 {prev})"
    if cur < prev:
        return f"↓ (前週 {prev})"
    return f"→ (前週 {prev})"


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
        lines += [
            f"- 直近7日クリック数: **{clicks_cur}** {_trend_mark(clicks_cur, clicks_prev)}",
            f"- 直近7日表示回数: **{imp_cur}** {_trend_mark(imp_cur, imp_prev)}",
        ]
        latest = max(gsc_daily, key=lambda r: r["date"])
        lines.append(
            f"- 最新日 {latest['date']}: クリック {latest['clicks']} / 表示 {latest['impressions']}")
    else:
        lines.append("- データ未取得")

    if gsc_queries:
        lines += ["", "### 上位クエリ (直近10日)",
                  "| クエリ | クリック | 表示 |", "|---|---|---|"]
        for q in gsc_queries[:10]:
            lines.append(f"| {q['query']} | {q['clicks']} | {q['impressions']} |")

    if gsc_pages:
        lines += ["", "### 上位ページ (直近10日)",
                  "| ページ | クリック | 表示 |", "|---|---|---|"]
        for p in gsc_pages[:10]:
            lines.append(f"| {p['page']} | {p['clicks']} | {p['impressions']} |")

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
        f"*生成: {today.isoformat()} (scripts/metrics/run_daily.py)*",
    ]
    return "\n".join(lines) + "\n"


def notification_summary(gsc_daily, asc_daily, today):
    """macOS通知用の1行サマリー。"""
    parts = []
    if gsc_daily:
        c, _ = week_over_week(gsc_daily, "clicks", today)
        i, _ = week_over_week(gsc_daily, "impressions", today)
        parts.append(f"GSC 7日: クリック{c}/表示{i}")
    if asc_daily:
        d, _ = week_over_week(asc_daily, "first_downloads", today)
        parts.append(f"App 7日: DL{d}")
    return " | ".join(parts) if parts else "データ未取得"
