"""App Store Connect APIから日次ダウンロード数を取得する。

必要な設定 (config.json の "asc" セクション):
  issuer_id: App Store Connect API の Issuer ID
  key_id: APIキーのKey ID
  private_key_path: AuthKey_XXXX.p8 のパス
  vendor_number: Sales and Trends のベンダー番号

Sales Reports (DAILY/SALES/SUMMARY) を使う。レポートは翌日以降に
生成されるため、直近の取得可能な日から遡って取得する。
"""
import csv
import datetime
import gzip
import io
import time

import jwt
import requests

API_URL = "https://api.appstoreconnect.apple.com/v1/salesReports"

# Product Type Identifier の分類
# 1系=初回ダウンロード, 3系=再ダウンロード, 7系=アップデート
FIRST_DOWNLOAD_PREFIXES = ("1",)
REDOWNLOAD_PREFIXES = ("3",)
UPDATE_PREFIXES = ("7",)


def _make_token(config):
    with open(config["private_key_path"]) as f:
        private_key = f.read()
    now = int(time.time())
    payload = {
        "iss": config["issuer_id"],
        "iat": now,
        "exp": now + 600,
        "aud": "appstoreconnect-v1",
    }
    return jwt.encode(payload, private_key, algorithm="ES256",
                      headers={"kid": config["key_id"]})


def parse_sales_tsv(text):
    """Sales Report のTSVを集計して {first_downloads, redownloads, updates} を返す。"""
    totals = {"first_downloads": 0, "redownloads": 0, "updates": 0}
    reader = csv.DictReader(io.StringIO(text), delimiter="\t")
    for row in reader:
        ptype = (row.get("Product Type Identifier") or "").strip()
        try:
            units = int(float(row.get("Units") or 0))
        except ValueError:
            continue
        if ptype.startswith(FIRST_DOWNLOAD_PREFIXES):
            totals["first_downloads"] += units
        elif ptype.startswith(REDOWNLOAD_PREFIXES):
            totals["redownloads"] += units
        elif ptype.startswith(UPDATE_PREFIXES):
            totals["updates"] += units
    return totals


def _fetch_one_day(token, vendor_number, date):
    resp = requests.get(API_URL, headers={"Authorization": f"Bearer {token}"},
                        params={
                            "filter[frequency]": "DAILY",
                            "filter[reportDate]": date.isoformat(),
                            "filter[reportType]": "SALES",
                            "filter[reportSubType]": "SUMMARY",
                            "filter[vendorNumber]": vendor_number,
                        }, timeout=30)
    if resp.status_code == 404:
        return None  # レポート未生成 or その日の実績ゼロ
    resp.raise_for_status()
    text = gzip.decompress(resp.content).decode("utf-8")
    return parse_sales_tsv(text)


def fetch(config, today=None, backfill_days=7):
    """直近backfill_days日分の日次DL数を返す。

    返り値: [{date, first_downloads, redownloads, updates}, ...]
    404(レポート未生成/実績ゼロ)の日は0埋めせずスキップする。
    """
    today = today or datetime.date.today()
    token = _make_token(config)
    rows = []
    for delta in range(1, backfill_days + 1):
        date = today - datetime.timedelta(days=delta)
        totals = _fetch_one_day(token, config["vendor_number"], date)
        if totals is not None:
            rows.append({"date": date.isoformat(), **totals})
    return rows
