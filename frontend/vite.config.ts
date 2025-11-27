import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Use backend:8000 in Docker, localhost:8000 for local development
const backendTarget = process.env.VITE_BACKEND_URL || "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      "/api": {
        target: backendTarget,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
      "/uploads": {
        target: backendTarget,
        changeOrigin: true,
      },
    },
  },
});
