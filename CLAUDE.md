# shirodo-lp

城道（Shirodo）iOSアプリのランディングページ。静的HTML/CSS/JSのみで、ビルド工程はない。`npx serve -l 5500 .` でローカル確認できる（`.claude/launch.json` 参照）。

## ページを追加・更新したら

1. `python3 scripts/update_sitemap.py` を実行して `sitemap.xml` の `lastmod` を同期する（コミット前に実行する。未コミットの変更があるファイルは今日の日付になる）
   - 新ページを作った場合、sitemap への `<url>` 追記は手動。未掲載は同スクリプトが警告する
   - `--check` を付けるとズレを検出するだけで書き換えない（終了コード1）
2. 新しいディレクトリを公開する場合は `.github/workflows/deploy-pages.yml` の許可リストに `cp -r <dir> _site/<dir>` を追記する（許可リスト方式のため、追記しないと本番に出ない）
3. `/100meijo/` は `scripts/gen_100meijo.py`、`/guide/level/` は `scripts/gen_level.py`（データは `data/level.json`）の生成物。**HTMLを直接編集せず、スクリプトを直して再生成する**
   - **タイトル・リード文・FAQなどの文章もスクリプトの中にある**。文章だけの修正でもHTMLではなくスクリプトを直す（2026-09-12に「百名城」の修正をHTMLへ直接入れ、再生成で消える状態を作った事故がある）
   - 生成物の2行目には「自動生成ファイル」の目印コメントが入っている。HTMLを開いてこれがあれば編集しない
   - `python3 scripts/gen_100meijo.py --check`（`gen_level.py` も同様）で、公開中のHTMLとスクリプト出力のズレを検出する（書き換えない。ズレがあれば終了コード1）。アプリ本体の `castles.json` が変わった場合もズレとして出る
   - 内容を変えない再生成（計測タグの追加など）は `GEN_DATE=YYYY-MM-DD` を付けて、ページ上の更新日を据え置く
4. コミット前に `python3 -m unittest discover scripts/tests` を実行する（生成ページのズレ検出もここに含まれる）
5. **コミット前フックで、生成ページの直接編集を機械的に止めている**
   - `.githooks/pre-commit` が、生成ページ・生成スクリプト・`data/` を含むコミットのときだけ `--check` を実行し、ズレがあればコミットを止める
   - クローンしたら一度だけ `git config core.hooksPath .githooks` を実行して有効にする
   - フックが失敗したら、**飛ばさずに原因を直す**。`--no-verify` / `-n` や `core.hooksPath` の変更は、Claude Code 側のフック（`.claude/hooks/block_hook_bypass.py`）が止める

### 全ページ共通の部品（ヘッダー・フッター・head内の共通タグ・共通スクリプト）

- 正本は `scripts/shared_parts.py`。各ページの `<!-- shared:head -->`、`shared:nav`、`shared:footer`、`shared:scripts` の目印の間はここから書き込まれる。**目印の間を直接編集しない**
- 変更したら `python3 scripts/sync_shared.py` で手書きページに反映し、生成ページ（100meijo・level）は生成スクリプトを再生成する（`GEN_DATE` で更新日を据え置く）
- **新しいページを作るとき**: 4つの目印を置き、`FOOTER_LINKS` にページを追加して `sync_shared.py` を実行する。フッターは各ページで自分自身へのリンクを自動で外す
- ズレはコミット前フックで止まる（`sync_shared.py --check`）。テストでも、全ページに目印があること・全ページがフッターに載っていることを確認している
- ページ固有のCSS（見た目）はまだ各ページのインラインCSSにある。共通CSSへの切り出しは未実施（2段階目）

### ヘッダーの入手ボタン

- 文言は全ページ「アプリ入手」で統一する（検索から読み物ページに来た人は、城道がアプリだと知らないため。2026-09-13決定）。テストで一致を確認している
- **トップだけ金色の塗り、他のページは枠線**なのは意図的。トップは申し込みが主目的のページなので強く、読み物ページは控えめにする

### アプリの機能に言及するとき

LPでアプリの機能を書くときは、必ず `~/Developer/shirodo`（アプリ本体のリポジトリ）のソースか `docs/BACKLOG.md` で裏を取る。このリポジトリにはアプリのコードがないため思い込みが入りやすく、実際に「写真を残せる」と8箇所に誤記載した事故がある（2026-07-27修正）。実装済みなのは登城記録・メモ・iCloud自動復元で、**写真保存と登城日の変更は未実装**。

## 開発の進め方（未知の共同発見）

以下で参照する `/unknowns` スキルは、共通プラグイン [katsuhikosakata29-max/claude-skills](https://github.com/katsuhikosakata29-max/claude-skills) が提供する（このリポジトリには置かない）。未インストールの環境では一度だけ `/plugin marketplace add katsuhikosakata29-max/claude-skills` → `/plugin install katsu-workflow@claude-skills` を実行する。

このリポジトリの開発者は個人開発者（本業PM）で、レビュアーがいない。Claude への依頼を「作業指示→結果の受け取り」にせず、「未知の共同発見」として進めること。

### 実装前

- 新しい機能・デザイン変更・不慣れな領域の作業を始めるとき、いきなり実装せず `/unknowns` スキルの利用を提案する。特に「見れば分かるが言語化されていない」デザイン・UX 判断が絡む場合は、実装前に HTML モックを複数案出して反応をもらう。
- スコープが曖昧なままの依頼には、設計が変わる質問を優先して確認してから着手する。

### 実装中

- 計画や指示から逸脱せざるを得ないエッジケースに遭遇したら、保守的な選択肢を取り、`implementation-notes.md` の「Deviations」セクションに記録して続行する（作業のたびに新規作成してよい。コミットには含めない）。
- 質問で作業を止めるのは、破壊的操作か本質的なスコープ変更のときだけ。
