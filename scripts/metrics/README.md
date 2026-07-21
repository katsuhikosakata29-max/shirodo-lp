# SHIRODO デイリーメトリクス

Search Console と App Store Connect の数値を毎朝8時に自動取得し、
`metrics/` にCSV蓄積 + `metrics/DAILY.md` にダイジェストを生成する。

## 構成

- `fetch_gsc.py` — Search Console API (クリック/表示回数、クエリ、ページ)
- `fetch_asc.py` — App Store Connect Sales Reports (初回DL/再DL/更新)
- `report.py` — ダイジェスト生成(純粋関数)
- `run_daily.py` — エントリポイント。片方の取得が失敗しても他方は反映する
- `com.shirodo.metrics.plist` — launchd定義(毎朝8:00、macOS通知つき)

## 初期セットアップ

### 0. 依存インストール

```sh
cd scripts/metrics
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### 1. 認証情報の置き場所

リポジトリ外の `~/.config/shirodo-metrics/config.json` に置く(コミット禁止):

```json
{
  "gsc": {
    "service_account_json": "/Users/sakatakatsuhiko/.config/shirodo-metrics/gsc-sa.json",
    "site_url": "sc-domain:shirodo.com"
  },
  "asc": {
    "issuer_id": "<Issuer ID>",
    "key_id": "<Key ID>",
    "private_key_path": "/Users/sakatakatsuhiko/.config/shirodo-metrics/AuthKey_XXXX.p8",
    "vendor_number": "<ベンダー番号>"
  }
}
```

セクションがない・鍵が無効な場合、そのソースは「未取得」としてダイジェストに明示される。

### 2. GSC サービスアカウント発行

1. [Google Cloud Console](https://console.cloud.google.com/) → プロジェクト作成(例: shirodo-metrics)
2. 「APIとサービス」→「ライブラリ」→ **Search Console API** を有効化
3. 「認証情報」→「サービスアカウントを作成」→ 鍵(JSON)を作成しダウンロード
   → `~/.config/shirodo-metrics/gsc-sa.json` に置く
4. [Search Console](https://search.google.com/search-console) → 設定 → ユーザーと権限
   → サービスアカウントのメールアドレスを「制限付き(閲覧)」で追加

### 3. App Store Connect APIキー発行

1. [App Store Connect](https://appstoreconnect.apple.com/) → ユーザとアクセス → 統合 → App Store Connect API
2. 「チームキー」でキーを生成。ロールは **販売・財務(Sales and Finance)**
3. `.p8` をダウンロード(一度しかDLできない)→ `~/.config/shirodo-metrics/` に置く
4. Issuer ID・Key ID を config.json に転記
5. ベンダー番号: App Store Connect → 「支払いと財務レポート」の左上に表示される数字

### 4. 動作確認と launchd 登録

```sh
.venv/bin/python run_daily.py          # 手動実行してDAILY.mdを確認
cp com.shirodo.metrics.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.shirodo.metrics.plist
launchctl start com.shirodo.metrics    # 即時テスト実行
```

ログ: `/tmp/shirodo-metrics.log` / `/tmp/shirodo-metrics.err`

## 運用メモ

- GSCデータは2〜3日遅れ。直近10日を毎回取り直して上書きする(欠損自動補完)
- App Storeの日次レポートは翌日以降に生成。未生成の日はスキップし翌朝拾う
- 自分のアクセス/DLも数値に含まれる。**絶対数でなく前週比の傾き**を見ること
- `metrics/*.csv` はコミットして履歴を残す運用(公開許可リスト外なのでサイトには出ない)

## テスト

```sh
.venv/bin/python -m unittest discover tests
```
