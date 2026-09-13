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
