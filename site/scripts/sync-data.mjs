import { cp, mkdir } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const siteRoot = resolve(here, "..");
const repoRoot = resolve(siteRoot, "..");
const target = resolve(siteRoot, "public", "data");
const downloads = resolve(siteRoot, "public", "downloads");

await mkdir(target, { recursive: true });
await mkdir(downloads, { recursive: true });
await cp(resolve(repoRoot, "data", "public"), resolve(target, "evidence"), { recursive: true });
await cp(
  resolve(repoRoot, "graphs", "hospitality-experience-graph.json"),
  resolve(target, "hospitality-experience-graph.json")
);
await cp(
  resolve(repoRoot, "graphs", "hospitality-experience-graph.graphml"),
  resolve(target, "hospitality-experience-graph.graphml")
);
await cp(resolve(repoRoot, "reports", "hxg-poster.pdf"), resolve(downloads, "hxg-poster.pdf"));
await cp(
  resolve(repoRoot, "reports", "linkedin-carousel.pdf"),
  resolve(downloads, "hxg-linkedin-carousel.pdf")
);
