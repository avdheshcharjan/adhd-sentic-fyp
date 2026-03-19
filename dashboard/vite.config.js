import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/insights": "http://localhost:8420",
      "/whoop": "http://localhost:8420",
      "/interventions": "http://localhost:8420",
    },
  },
});
