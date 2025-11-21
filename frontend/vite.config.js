import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 4173,
    proxy: {
      "/auth": "http://localhost:8000",
      "/status": "http://localhost:8000",
      "/timeline": "http://localhost:8000",
      "/incidents": "http://localhost:8000",
      "/rules": "http://localhost:8000",
      "/ws": {
        target: "ws://localhost:8000",
        ws: true
      }
    }
  }
});
