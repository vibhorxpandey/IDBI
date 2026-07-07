import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// LendLens dashboard dev server. The API base is configurable via VITE_API_URL
// (defaults to http://127.0.0.1:8000 — see src/api.js).
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, open: false },
});
