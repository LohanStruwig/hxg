import { createReadStream, existsSync, statSync } from "node:fs";
import { createServer } from "node:http";
import { extname, resolve, sep } from "node:path";

const host = "127.0.0.1";
const port = 4173;
const root = resolve(process.cwd(), "dist");
const prefix = "/hxg";
const contentTypes = {
  ".css": "text/css; charset=utf-8",
  ".graphml": "application/xml; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".ico": "image/x-icon",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".pdf": "application/pdf",
  ".svg": "image/svg+xml",
};

const server = createServer((request, response) => {
  const url = new URL(request.url || "/", `http://${host}:${port}`);
  if (url.pathname === prefix) {
    response.writeHead(308, { location: `${prefix}/` });
    response.end();
    return;
  }
  if (!url.pathname.startsWith(`${prefix}/`)) {
    response.writeHead(404).end("Not found");
    return;
  }
  const relative = decodeURIComponent(url.pathname.slice(prefix.length + 1));
  let target = resolve(root, relative || "index.html");
  if (existsSync(target) && statSync(target).isDirectory()) target = resolve(target, "index.html");
  if (!target.startsWith(`${root}${sep}`) && target !== root) {
    response.writeHead(403).end("Forbidden");
    return;
  }
  if (!existsSync(target) || !statSync(target).isFile()) {
    response.writeHead(404).end("Not found");
    return;
  }
  const type = contentTypes[extname(target)] || "application/octet-stream";
  response.writeHead(200, { "content-type": type, "cache-control": "no-store" });
  createReadStream(target).pipe(response);
});

server.listen(port, host, () => console.log(`HXG QA server: http://${host}:${port}${prefix}/`));
