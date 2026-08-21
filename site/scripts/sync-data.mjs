import { mkdir, rm } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const siteRoot = resolve(here, "..");
const target = resolve(siteRoot, "public", "data");
const downloads = resolve(siteRoot, "public", "downloads");
const dist = resolve(siteRoot, "dist");

await rm(target, { recursive: true, force: true });
await rm(downloads, { recursive: true, force: true });
await rm(dist, { recursive: true, force: true });
await mkdir(target, { recursive: true });
await mkdir(downloads, { recursive: true });

// Emergency takedown: public research artifacts remain withheld until the
// rights-aware v0.3.0 release passes its release gates.
