import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import { fileURLToPath } from "node:url";
import { readFile, readdir } from "node:fs/promises";
import { join } from "node:path";
import { compile } from "tailwindcss";

const components = fileURLToPath(new URL("./src/components", import.meta.url));

// Compile this library's literal utility classes with the installed Tailwind
// compiler. No extra package or application stylesheet changes are required.
function componentStyles() {
  return {
    name: "component-tailwind",
    enforce: "pre",
    async transform(source, id) {
      if (
        id.split("?")[0].replaceAll("\\", "/") !==
        `${components.replaceAll("\\", "/")}/styles.css`
      )
        return;
      const candidates = new Set();
      const scan = async (directory) => {
        for (const entry of await readdir(directory, { withFileTypes: true })) {
          const path = join(directory, entry.name);
          if (entry.isDirectory()) await scan(path);
          else if (/\.(jsx|js)$/.test(entry.name)) {
            this.addWatchFile(path);
            const text = await readFile(path, "utf8");
            for (const token of text.match(/[^\s"'`<>]+/g) ?? [])
              candidates.add(token);
          }
        }
      };
      await scan(components);
      const theme = await readFile(
        fileURLToPath(
          new URL("./node_modules/tailwindcss/theme.css", import.meta.url),
        ),
        "utf8",
      );
      const compiler = await compile(`${theme}\n${source}`);
      return { code: compiler.build([...candidates]), map: null };
    },
    handleHotUpdate({ file, server }) {
      if (
        file.replaceAll("\\", "/").startsWith(components.replaceAll("\\", "/"))
      ) {
        const modules = server.moduleGraph.getModulesByFile(
          join(components, "styles.css"),
        );
        for (const module of modules ?? [])
          server.moduleGraph.invalidateModule(module);
        server.ws.send({ type: "full-reload" });
      }
    },
  };
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), componentStyles()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
      "@components": components,
    },
  },
});
