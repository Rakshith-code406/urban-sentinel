import path from "node:path";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },

  server: {
    host: true, // 🔥 IMPORTANT
    allowedHosts: [
      "churn-squishy-bless.ngrok-free.dev" // 👈 your ngrok link
    ],
    proxy: [
      '/api',
      '/auth',
      '/admin',
      '/worker',
      '/user',
      '/issues',
      '/reports',
      '/iot',
      '/panel',
      '/uploads',
      '/receipt',
      '/qr',
      '/send-otp',
      '/verify-otp',
      '/reset-password',
    ].reduce<Record<string, { target: string; changeOrigin: boolean; secure: boolean; ws?: boolean }>>((proxy, route) => {
      proxy[route] = {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
        ws: route === '/panel',
      };
      return proxy;
    }, {})
  }
});
