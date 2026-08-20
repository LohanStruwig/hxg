import { defineConfig } from "astro/config";

export default defineConfig({
  site: "https://lohanstruwig.github.io",
  base: "/hxg",
  output: "static",
  build: {
    format: "directory"
  },
  vite: {
    build: {
      sourcemap: true
    }
  }
});
