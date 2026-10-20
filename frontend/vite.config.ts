import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const backend = process.env.ALICE_API ?? "http://127.0.0.1:8471";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    port: 8472,
    strictPort: true,
    proxy: {
      "/api": { target: backend, changeOrigin: true },
      "/artifacts": { target: backend, changeOrigin: true },
    },
  },
});
