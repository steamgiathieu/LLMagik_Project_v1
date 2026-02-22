import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// https://vitejs.dev/config/
export default defineConfig({
  base: process.env.VITE_BASE_URL || "/", // Use "/" for local dev, "/LLMagik/" for GitHub Pages
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      // Optional: proxy API calls during development
      // "/api": "http://localhost:8000",
    },
  },
  build: {
    outDir: "dist",
    sourcemap: false,
    minify: "terser",
  },
});
