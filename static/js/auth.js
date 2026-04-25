/**
 * auth.js — 全局 token 管理工具
 * 统一 key "access_token"，localStorage + sessionStorage 双同步。
 * 在所有页面的首个 <script> 前引入，供 bazi/main.js、ziwei/main.js、
 * ziwei/vue-panels.js、admin/main.js 共同使用。
 */
"use strict";

(function () {
  const KEY = "access_token";

  /** 读取 token（localStorage 优先，sessionStorage 备） */
  function getToken() {
    return localStorage.getItem(KEY) || sessionStorage.getItem(KEY) || "";
  }

  /** 写入 token（localStorage + sessionStorage 双写） */
  function setToken(tok) {
    if (tok) {
      localStorage.setItem(KEY, tok);
      sessionStorage.setItem(KEY, tok);
    }
  }

  /** 清除 token（两处同时删除） */
  function clearToken() {
    localStorage.removeItem(KEY);
    sessionStorage.removeItem(KEY);
  }

  window.getToken   = getToken;
  window.setToken   = setToken;
  window.clearToken = clearToken;
})();
