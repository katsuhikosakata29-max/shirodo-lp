"""Google Search Console APIから日次データを取得する。

必要な設定 (config.json の "gsc" セクション):
  service_account_json: サービスアカウント鍵JSONのパス
  site_url: プロパティ名 (例 "sc-domain:shirodo.com")

サービスアカウントはGSCのプロパティに「閲覧者」として追加しておくこと。
"""
import datetime

import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request

API_BASE = "https://searchconsole.googleapis.com/webmasters/v3/sites"
SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"

# GSCのデータ反映は2〜3日遅れるため、直近数日は取り直して上書きする
BACKFILL_DAYS = 10


def _get_token(sa_json_path):
    creds = service_account.Credentials.from_service_account_file(
        sa_json_path, scopes=[SCOPE])
    creds.refresh(Request())
    return creds.token


def _query(token, site_url, body):
    url = f"{API_BASE}/{requests.utils.quote(site_url, safe='')}/searchAnalytics/query"
    resp = requests.post(url, json=body,
                         headers={"Authorization": f"Bearer {token}"},
                         timeout=30)
    resp.raise_for_status()
    return resp.json().get("rows", [])


def fetch(config, today=None):
    """日別・クエリ別・ページ別のデータを取得して返す。

    返り値: {"daily": [...], "queries": [...], "pages": [...]}
    """
    today = today or datetime.date.today()
    start = (today - datetime.timedelta(days=BACKFILL_DAYS)).isoformat()
    end = today.isoformat()
    token = _get_token(config["service_account_json"])
    site = config["site_url"]

    def rows_for(dimension, limit):
        rows = _query(token, site, {
            "startDate": start, "endDate": end,
            "dimensions": [dimension], "rowLimit": limit,
        })
        return [
            {dimension: r["keys"][0],
             "clicks": int(r["clicks"]),
             "impressions": int(r["impressions"])}
            for r in rows
        ]

    return {
        "daily": rows_for("date", 25),
        "queries": rows_for("query", 20),
        "pages": rows_for("page", 20),
    }
