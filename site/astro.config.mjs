import { defineConfig } from "astro/config";

export default defineConfig({
  site: "https://lohanstruwig.github.io",
  base: "/hxg",
  output: "static",
  markdown: {
    syntaxHighlight: false
  },
  security: {
    csp: {
      algorithm: "SHA-256",
      directives: [
        "default-src 'self'",
        "connect-src 'self'",
        "font-src 'self'",
        "img-src 'self' data:",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'none'"
      ],
      scriptDirective: {
        resources: ["'self'"]
      },
      styleDirective: {
        hashes: [
          { hash: "sha256-pgvDUBa4IjFA2yuSJ2cqcyxmNYJMborsd0ORcRv9vw8=", kind: "element" }
        ],
        resources: [
          { resource: "'self'", kind: "element" }
        ]
      }
    }
  },
  build: {
    format: "directory"
  },
  vite: {
    build: {
      sourcemap: false
    }
  }
});
