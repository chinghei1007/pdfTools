import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import { fileURLToPath } from "node:url";

const components = fileURLToPath(new URL("./src/components", import.meta.url));

// A local development URL for the standalone component preview.
function previewRoute() {
  return {
    name: "component-preview-route",
    configureServer(server) {
      server.middlewares.use((req, _res, next) => {
        const url = new URL(req.url || "/", "http://localhost");
        const previewPath = url.pathname
          .toLowerCase()
          .replace(/\/$/, "")
          .replace(/\.html$/, "");
        if (
          ["/previewv1", "/previewpypdf_v1", "/preview_pypdf_v1"].includes(
            previewPath,
          )
        ) {
          req.url = `/pypdf/render${url.search}`;
        }
        if (
          ["/preview_pymupdf_v1", "/preview_pymypdf_v1"].includes(previewPath)
        ) {
          req.url = `/pymupdf/render${url.search}`;
        }
        next();
      });
    },
  };
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), previewRoute()],
  server: {
    proxy: { "/api/v1": "http://127.0.0.1:8001" },
  },
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
      "@components": components,
    },
  },
});
