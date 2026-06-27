// Note: this JS config is intentionally not `// @ts-check`'d — astro check would
// otherwise flag a known type-version skew between @tailwindcss/vite's plugin
// signature and the Vite types Astro bundles. The build itself is unaffected.
import { defineConfig } from "astro/config";
import mdx from "@astrojs/mdx";
import sitemap from "@astrojs/sitemap";
import tailwindcss from "@tailwindcss/vite";

// Static output for Cloudflare Pages (no @astrojs/cloudflare adapter needed for
// a purely static portfolio; deploy the built `dist/`).
export default defineConfig({
  site: "https://labs.example.com",
  output: "static",
  integrations: [mdx(), sitemap()],
  vite: { plugins: [tailwindcss()] },
  markdown: {
    syntaxHighlight: "shiki",
    shikiConfig: { theme: "github-dark-dimmed", wrap: true },
  },
});
