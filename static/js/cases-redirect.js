/**
 * cases-redirect.js
 * 仅在 cases.html 作为独立页面访问时（非 embedded/standalone 模式）重定向到 verify.html
 * 提取自原 cases.html 内联脚本以符合 CSP script-src 'self'
 */
(function () {
  var params = new URLSearchParams(location.search);
  var embedded = params.get('embedded') === '1';
  var standalone = params.get('standalone') === '1';
  if (!embedded && !standalone) {
    location.replace('/static/verify.html?tab=cases');
  }
})();
