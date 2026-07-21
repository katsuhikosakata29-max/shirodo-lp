"""共通ユーティリティ: 設定読み込みとCSVの日付キーupsert。"""
import csv
import json
import os
from pathlib import Path

CONFIG_PATH = Path(os.environ.get(
    "SHIRODO_METRICS_CONFIG",
    Path.home() / ".config" / "shirodo-metrics" / "config.json",
))

REPO_ROOT = Path(__file__).resolve().parents[2]
METRICS_DIR = REPO_ROOT / "metrics"


def load_config():
    """設定ファイルを読む。存在しなければ空dict(各ソースはスキップされる)。"""
    if not CONFIG_PATH.exists():
        return {}
    with open(CONFIG_PATH) as f:
        return json.load(f)


def upsert_csv(path, fieldnames, rows, key="date"):
    """CSVにrowsをkey列でupsertし、key昇順で書き戻す。

    再実行しても行が重複しない(同じ日付は上書き)。
    """
    path = Path(path)
    existing = {}
    if path.exists():
        with open(path, newline="") as f:
            for row in csv.DictReader(f):
                existing[row[key]] = row
    for row in rows:
        existing[str(row[key])] = {k: str(v) for k, v in row.items()}
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for k in sorted(existing):
            writer.writerow(existing[k])


def read_csv(path):
    path = Path(path)
    if not path.exists():
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f))
