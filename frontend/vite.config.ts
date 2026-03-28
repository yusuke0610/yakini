/// <reference types="vitest" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  base: "./",
  server: {
    host: "0.0.0.0",
    port: 5173,
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test-setup.ts"],
    /** vitestが拾うテストファイルを src 配下の .test.ts に限定する */
    include: ["src/**/*.test.ts", "src/**/*.test.tsx"],
  },
});
