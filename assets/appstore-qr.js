/**
 * SHIRODO LP: PCで見ている訪問者向けのApp Store QRダイアログ
 * - マウス操作・幅900px以上の端末でApp Storeリンクを押すと、遷移の代わりにQRを出す
 *   (PCでApp Storeへ飛んでもiPhoneアプリは入れられず、行き止まりになるため)
 * - スマホ・タブレット、JSが動かない環境、修飾キー付きクリックは今まで通りリンクとして動く
 * - QRの中身は App Store Connect のキャンペーンリンク(ct=LP-QR)。生成は scripts/gen_appstore_qr.py
 * - ダイアログを開いたら appstore_qr_open を PostHog に送る(読み取り自体は PostHog に映らない)
 */
(function () {
  var DESKTOP = '(hover: hover) and (pointer: fine) and (min-width: 900px)';
  var QR_SRC = '/assets/appstore-qr.svg';
  var dialog = null;
  var lastTrigger = null;

  if (!window.matchMedia || typeof HTMLDialogElement !== 'function') return;

  var CSS = [
    // サイト側の * { margin: 0 } リセットで中央寄せが外れるため margin:auto を明示
    '.sd-qr{margin:auto;border:1px solid rgba(201,169,97,.28);border-radius:16px;padding:30px 30px 24px;width:min(340px,calc(100vw - 32px));',
    'background:#1e1a14;color:#f2ede2;text-align:center;box-shadow:0 24px 70px rgba(0,0,0,.6);',
    'font-family:"Noto Sans JP",-apple-system,BlinkMacSystemFont,"Hiragino Sans","Yu Gothic",sans-serif}',
    '.sd-qr[open]{animation:sd-qr-in .18s ease-out}',
    '.sd-qr::backdrop{background:rgba(10,9,8,.72)}',
    '@keyframes sd-qr-in{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}',
    '@media (prefers-reduced-motion:reduce){.sd-qr[open]{animation:none}}',
    '.sd-qr__inner{display:grid;gap:14px;justify-items:center}',
    '.sd-qr__title{margin:0;font-family:"Shippori Mincho","Noto Serif JP","Hiragino Mincho ProN","Yu Mincho",serif;',
    'font-weight:600;font-size:1.15rem;line-height:1.5;color:#f2ede2}',
    '.sd-qr__img{display:block;width:188px;height:188px;border-radius:10px}',
    '.sd-qr__note{margin:0;font-size:.82rem;line-height:1.7;color:#b5ad9b}',
    '.sd-qr__link{font-size:.78rem;color:#b5ad9b;text-underline-offset:3px}',
    '.sd-qr__link:hover{color:#e5c67d}',
    '.sd-qr__close{position:absolute;top:8px;right:10px;background:none;border:0;color:#b5ad9b;',
    'font-size:1.4rem;line-height:1;padding:6px 8px;cursor:pointer;border-radius:6px}',
    '.sd-qr__close:hover{color:#f2ede2}',
    '.sd-qr :focus-visible{outline:2px solid #e5c67d;outline-offset:3px}'
  ].join('');

  function build() {
    var style = document.createElement('style');
    style.textContent = CSS;
    document.head.appendChild(style);

    dialog = document.createElement('dialog');
    dialog.className = 'sd-qr';
    dialog.setAttribute('aria-labelledby', 'sd-qr-title');
    dialog.innerHTML =
      '<button type="button" class="sd-qr__close" aria-label="閉じる">×</button>' +
      '<div class="sd-qr__inner">' +
        '<p class="sd-qr__title" id="sd-qr-title">iPhoneで読み取ってください</p>' +
        '<img class="sd-qr__img" src="' + QR_SRC + '" width="188" height="188" alt="城道のApp StoreページのQRコード">' +
        '<p class="sd-qr__note">城道はiPhone専用アプリです。<br>カメラを向けるとApp Storeが開きます。</p>' +
        '<a class="sd-qr__link" href="#">このままApp Storeのページを開く ›</a>' +
      '</div>';
    document.body.appendChild(dialog);

    dialog.querySelector('.sd-qr__close').addEventListener('click', function () { dialog.close(); });
    // 枠の外(背景)をクリックしたら閉じる
    dialog.addEventListener('click', function (ev) { if (ev.target === dialog) dialog.close(); });
    dialog.addEventListener('close', function () { if (lastTrigger) lastTrigger.focus(); });
  }

  function open(link) {
    if (!dialog) build();
    lastTrigger = link;
    dialog.querySelector('.sd-qr__link').href = link.href;
    dialog.showModal();
    if (window.posthog) {
      posthog.capture('appstore_qr_open', {
        cta_class: link.className || '(none)',
        page_path: location.pathname
      });
    }
  }

  document.addEventListener('click', function (ev) {
    if (ev.defaultPrevented || ev.button !== 0 || ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.altKey) return;
    var link = ev.target && ev.target.closest && ev.target.closest('a[href*="apps.apple.com"]');
    if (!link || link.closest('.sd-qr')) return;
    if (!window.matchMedia(DESKTOP).matches) return;
    ev.preventDefault();
    open(link);
  });
})();
