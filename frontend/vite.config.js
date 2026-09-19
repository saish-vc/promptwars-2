import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: "0.0.0.0",
    proxy: {
      "/health": "http://localhost:8000",
      "/documents": "http://localhost:8000",
      "/analyze": "http://localhost:8000",
      "/compare": "http://localhost:8000",
      "/generate": "http://localhost:8000",
      "/chat": "http://localhost:8000",
      "/export": "http://localhost:8000",
      "/jobs": "http://localhost:8000",
    },
  },
});

