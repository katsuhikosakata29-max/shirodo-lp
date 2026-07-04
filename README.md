# shirodo-lp

城道（SHIRODO）— iOSアプリのランディングページ。
公開URL: **https://shirodo.com/**

## 構成

| 項目 | 内容 |
|---|---|
| ホスティング | GitHub Pages（カスタムドメイン `shirodo.com`） |
| デプロイ | `.github/workflows/deploy-pages.yml`（mainへのpushで自動実行、約20秒） |
| DNS | ムームーDNS（ムームードメインで管理） |
| サイト本体 | `index.html` 1枚 + `assets/`（純粋な静的サイト、ビルド不要） |

## デプロイの仕組み（2026-07-04に構造変更済み）

**経緯**: 当初はGitHub Pages標準の「Deploy from a branch」方式だったが、
GitHub内部のレガシーワークフロー（pages-build-deployment）が頻繁にキュー詰まりを起こし、
再実行(re-run)すると宙ぶらりんになって二度と動かない問題が多発した。

**現在**: 自前のActionsワークフロー（`deploy-pages.yml`）でデプロイする方式に切替済み。

- mainにpushすると自動でデプロイされる（Jekyllビルドなし）
- **公開されるのはワークフロー内の許可リストに載せたファイルだけ**
  （`index.html`・`assets/`・`100meijo/`・`robots.txt`・`sitemap.xml`・GSC確認用HTML）。
  README等はリポジトリ上では見えるが `shirodo.com` では配信されない。
  新しく公開したいファイルは `deploy-pages.yml` の「Build publish directory」に追加する
- Pages側の一時的エラー（"Deployment failed, try again later"）には自動リトライを内蔵
- 手動で再デプロイしたい場合: Actionsタブ →「Deploy to GitHub Pages」→「Run workflow」
- Actions履歴に残っている古い「pages build and deployment」のqueued表示はGitHub側のゾンビで実害なし

## 消してはいけないもの

| ファイル / レコード | 理由 |
|---|---|
| `CNAME` | カスタムドメインの紐付け。消えるとshirodo.comで表示されなくなる |
| `googlef6d63fab54b72de2.html` | Google Search Console所有権確認（HTMLファイル方式） |
| ムームーDNSのAレコード4行（185.199.108〜111.153） | GitHub Pagesへの接続。消えるとサイトが落ちる |
| ムームーDNSのTXTレコード（google-site-verification=...） | Search Consoleドメインプロパティの所有権確認 |
| ムームーDNSのCNAMEレコード（www → katsuhikosakata29-max.github.io） | www.shirodo.com からのリダイレクト用 |

## SEO対応の記録

### 実施済み（2026-07-02〜04）

- **on-page**: title / meta description / canonical / OGP / Twitterカード / h1副題（visually-hidden）
- **構造化データ (JSON-LD)**: MobileApplication・FAQPage・WebSite
- **sitemap.xml**: 画像sitemap込み（hero + スクリーンショット6枚）
- **robots.txt**: 全許可 + sitemap参照
- **Google Search Console**:
  - URLプレフィックスプロパティ `https://shirodo.com`（HTMLファイルで確認済み）
  - ドメインプロパティ `shirodo.com`（DNS TXTレコードで確認済み・2026-07-04）
  - sitemap.xml送信済み（成功・2026-07-04）
  - インデックス登録リクエスト済み（2026-07-04）

### 検索での状態（2026-07-04時点）

- Googleインデックス登録済み。「城道 shirodo」で**1位表示**、AIによる概要でも公式サイトとして引用される
- 「城道 アプリ」「shirodo アプリ」単独ではまだ上位に出ない（城ドラ系サイトが強い）。
  ドメインが新しく被リンクがほぼないため。時間と実績で解消する領域

### 今後のアクション

- [x] App Store Connectの「マーケティングURL」を `https://shirodo.com` に設定（2026-07-04完了）
- [ ] X等のSNSでLP URL付きの告知
- [ ] 1週間後（7/11頃）にSearch Console「検索パフォーマンス」を確認し、
      表示されているクエリに合わせてLP文言を調整する
- [ ] 「城道 アプリ」での順位を定期観測（目安: 1〜2週間で浮上）
