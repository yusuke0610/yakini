/**
 * Firebase Hosting Cookie strip 挙動をローカルで再現するプロキシサーバー。
 *
 * Firebase Hosting は __session という名前の Cookie のみ Cloud Run に転送し、
 * それ以外の Cookie を除去する。このスクリプトは同じ挙動をローカルで再現する。
 *
 * 使い方:
 *   make dev-proxy       # Vite + プロキシを同時起動
 *   make dev-proxy-only  # プロキシのみ起動
 *
 * ブラウザは http://localhost:3000 にアクセスすること。
 */

import express from "express";
import { createProxyMiddleware } from "http-proxy-middleware";

const PROXY_PORT = parseInt(process.env.PROXY_PORT ?? "3000", 10);
const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";
const FRONTEND_URL = process.env.FRONTEND_URL ?? "http://localhost:5173";

const app = express();

// __session 以外の Cookie を除去するミドルウェア
function stripCookies(req, _res, next) {
  const rawCookie = req.headers["cookie"];
  if (!rawCookie) {
    next();
    return;
  }

  const kept = [];
  const removed = [];

  for (const part of rawCookie.split(";")) {
    const name = part.trim().split("=")[0];
    if (name === "__session") {
      kept.push(part.trim());
    } else {
      removed.push(name);
    }
  }

  if (removed.length > 0) {
    for (const name of removed) {
      console.log(`[proxy] Cookie strip: ${name} → removed`);
    }
    if (kept.length > 0) {
      console.log(`[proxy] Forwarding __session only`);
      req.headers["cookie"] = kept.join("; ");
    } else {
      console.log(`[proxy] No __session found — Cookie header removed`);
      delete req.headers["cookie"];
    }
  }

  next();
}

/**
 * 3xx レスポンスから Set-Cookie を除去する。
 *
 * Firebase Hosting CDN は 303 等のリダイレクトレスポンスに付いた Set-Cookie を転送しない。
 * この挙動をローカルで再現することで、HTML リダイレクト方式の修正が正しく機能するか検証できる。
 */
function stripRedirectSetCookie(proxyRes) {
  if (proxyRes.statusCode >= 300 && proxyRes.statusCode < 400) {
    const cookies = proxyRes.headers["set-cookie"];
    if (cookies) {
      console.log(
        `[proxy] ${proxyRes.statusCode} response: Set-Cookie を除去 (${cookies.length} 件) — Firebase CDN 挙動の再現`
      );
      delete proxyRes.headers["set-cookie"];
    }
  }
}

// バックエンドへのプロキシ（Cookie strip あり）
const backendProxy = createProxyMiddleware({
  target: BACKEND_URL,
  changeOrigin: true,
  on: {
    proxyRes: stripRedirectSetCookie,
  },
});

const frontendProxy = createProxyMiddleware({
  target: FRONTEND_URL,
  changeOrigin: true,
  ws: true,
});

// app.use("/auth", ...) のような Express prefix matching は req.url から /auth を除去するため、
// バックエンドに /github/login-url のような不完全なパスが届く。
// catch-all で受けて req.url を自前でチェックし、パス全体を保持したままルーティングする。
const BACKEND_PREFIXES = ["/auth", "/api", "/health"];

app.use((req, res, next) => {
  if (BACKEND_PREFIXES.some((prefix) => req.url.startsWith(prefix))) {
    stripCookies(req, res, () => backendProxy(req, res, next));
  } else {
    frontendProxy(req, res, next);
  }
});

app.listen(PROXY_PORT, () => {
  console.log(`[proxy] Firebase Cookie 再現プロキシ起動`);
  console.log(`[proxy]   http://localhost:${PROXY_PORT}  → frontend: ${FRONTEND_URL}`);
  console.log(`[proxy]   /auth /api /health              → backend:  ${BACKEND_URL}`);
  console.log(`[proxy]   リクエスト: __session 以外の Cookie を除去して転送`);
  console.log(`[proxy]   レスポンス: 3xx リダイレクトの Set-Cookie を除去 (Firebase CDN 挙動の再現)`);
});
