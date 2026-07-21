"""日次メトリクス収集のエントリポイント。

毎朝launchdから実行される想定。手動実行も可:
  .venv/bin/python run_daily.py [--notify]

GSC/ASCそれぞれ独立して取得し、片方が失敗してももう片方は反映する。
結果は metrics/*.csv に蓄積し、metrics/DAILY.md にダイジェストを書く。
"""
import argparse
import datetime
import subprocess
import sys

from common import load_config, upsert_csv, read_csv, METRICS_DIR
import report

GSC_DAILY_CSV = METRICS_DIR / "gsc_daily.csv"
GSC_QUERIES_CSV = METRICS_DIR / "gsc_queries.csv"
GSC_PAGES_CSV = METRICS_DIR / "gsc_pages.csv"
ASC_DAILY_CSV = METRICS_DIR / "asc_daily.csv"
DIGEST_MD = METRICS_DIR / "DAILY.md"


def collect(today):
    config = load_config()
    errors = []
    gsc_queries, gsc_pages = [], []

    if "gsc" in config:
        try:
            import fetch_gsc
            data = fetch_gsc.fetch(config["gsc"], today)
            upsert_csv(GSC_DAILY_CSV, ["date", "clicks", "impressions"],
                       data["daily"])
            gsc_queries = sorted(data["queries"],
                                 key=lambda r: (-r["clicks"], -r["impressions"]))
            gsc_pages = sorted(data["pages"],
                               key=lambda r: (-r["clicks"], -r["impressions"]))
            # クエリ/ページはスナップショットとして取得日付きで履歴も残す
            upsert_csv(GSC_QUERIES_CSV,
                       ["date", "query", "clicks", "impressions"],
                       [{"date": f"{today.isoformat()}|{q['query']}", **q}
                        for q in gsc_queries])
            upsert_csv(GSC_PAGES_CSV,
                       ["date", "page", "clicks", "impressions"],
                       [{"date": f"{today.isoformat()}|{p['page']}", **p}
                        for p in gsc_pages])
        except Exception as e:  # noqa: BLE001 - 片系failでも他系は続行
            errors.append(f"GSC: {e}")
    else:
        errors.append("GSC: 未設定 (config.jsonにgscセクションがない)")

    if "asc" in config:
        try:
            import fetch_asc
            rows = fetch_asc.fetch(config["asc"], today)
            if rows:
                upsert_csv(ASC_DAILY_CSV,
                           ["date", "first_downloads", "redownloads", "updates"],
                           rows)
        except Exception as e:  # noqa: BLE001
            errors.append(f"ASC: {e}")
    else:
        errors.append("ASC: 未設定 (config.jsonにascセクションがない)")

    return gsc_queries, gsc_pages, errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--notify", action="store_true",
                        help="macOS通知を出す(launchd実行用)")
    args = parser.parse_args()

    today = datetime.date.today()
    gsc_queries, gsc_pages, errors = collect(today)

    gsc_daily = read_csv(GSC_DAILY_CSV)
    asc_daily = read_csv(ASC_DAILY_CSV)

    digest = report.build_digest(gsc_daily, gsc_queries, gsc_pages,
                                 asc_daily, today, errors=errors)
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    DIGEST_MD.write_text(digest)
    print(digest)

    if errors:
        print("errors:", errors, file=sys.stderr)

    if args.notify:
        summary = report.notification_summary(gsc_daily, asc_daily, today)
        if errors:
            summary += " ⚠️一部エラー"
        subprocess.run([
            "osascript", "-e",
            f'display notification "{summary}" with title "SHIRODO メトリクス"',
        ], check=False)

    return 1 if errors and not (gsc_daily or asc_daily) else 0


if __name__ == "__main__":
    sys.exit(main())
