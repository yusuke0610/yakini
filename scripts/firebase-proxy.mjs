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

// バックエンドへのプロキシ（Cookie strip あり）
const backendProxy = createProxyMiddleware({
  target: BACKEND_URL,
  changeOrigin: true,
});

app.use("/auth", stripCookies, backendProxy);
app.use("/api", stripCookies, backendProxy);
app.use("/health", stripCookies, backendProxy);

// フロントエンドへのプロキシ（Cookie strip なし）
app.use(
  "/",
  createProxyMiddleware({
    target: FRONTEND_URL,
    changeOrigin: true,
    ws: true,
  })
);

app.listen(PROXY_PORT, () => {
  console.log(`[proxy] Firebase Cookie 再現プロキシ起動`);
  console.log(`[proxy]   http://localhost:${PROXY_PORT}  → frontend: ${FRONTEND_URL}`);
  console.log(`[proxy]   /auth /api /health              → backend:  ${BACKEND_URL}`);
  console.log(`[proxy]   __session 以外の Cookie を除去して転送`);
});
