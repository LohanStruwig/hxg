import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.goto("./");
  await expect(page.locator("#graph-explorer")).toHaveAttribute("data-graph-ready", "true");
});

test("loads v0.3.0 without runtime errors or restricted release copy", async ({ page }) => {
  const errors: string[] = [];
  page.on("console", (message) => {
    if (["error", "warning"].includes(message.type())) errors.push(message.text());
  });
  await page.reload();
  await expect(page).toHaveTitle("Hospitality Experience Graph");
  await expect(page.getByRole("heading", { level: 1, name: /From screen to stay/i })).toBeVisible();
  await expect(page.getByText("Independent research · Release 0.3.0")).toBeVisible();
  await expect(page.locator("astro-dev-toolbar, vite-error-overlay, #webpack-dev-server-client-overlay")).toHaveCount(0);
  await expect(page.locator("#graph-explorer")).toHaveAttribute("data-total-nodes", "30");
  await expect(page.locator("#graph-explorer")).toHaveAttribute("data-total-relationships", "34");
  const body = await page.locator("body").innerText();
  for (const restricted of ["74%", "62%", "44,787", "$805", "$11.6T"]) expect(body).not.toContain(restricted);
  expect(errors).toEqual([]);
});

test("renders six bounded guided pathways and linked claims", async ({ page }) => {
  await expect(page.locator(".pathway-row")).toHaveCount(6);
  await expect(page.locator("#graph-explorer")).toHaveAttribute("data-visible-nodes", "12");
  await expect(page.locator("#graph-explorer")).toHaveAttribute("data-visible-edges", "6");
  await page.locator(".pathway-row").nth(4).click();
  await expect(page.locator("#drawer-title")).toHaveText("Protect sessions and data");
  await expect(page.locator("#drawer-path")).toContainText("can support");
  await expect(page.locator("#drawer-limitations")).toContainText("does not prove");
  await expect(page.locator("#graph-explorer")).toHaveAttribute("data-label-collisions", "0");
  await expect(page.locator("#graph-explorer")).toHaveAttribute("data-edge-crossings", "0");
});

test("keeps all nodes edge-free at rest and focuses one hop", async ({ page }) => {
  await page.getByRole("tab", { name: "Explore all nodes" }).click();
  await expect(page.locator(".node-group")).toHaveCount(5);
  await expect(page.locator(".node-button")).toHaveCount(30);
  await expect(page.locator("#graph-explorer")).toHaveAttribute("data-visible-edges", "0");
  await page.getByLabel("Find a node").fill("Data governance");
  await expect(page.locator("#focus-title")).toHaveText("Data governance");
  await expect(page.locator(".focus-relationship")).toHaveCount(1);
  await expect(page.locator("#graph-explorer")).toHaveAttribute("data-label-collisions", "0");
  await expect(page.locator("#graph-explorer")).toHaveAttribute("data-edge-crossings", "0");
  await page.getByRole("tab", { name: "Guided pathways" }).click();
  await expect(page.locator("#drawer-title")).toHaveText("Cast from your device");
});

test("retains all 34 searchable relationship records", async ({ page }) => {
  await page.getByRole("tab", { name: "Relationship list" }).click();
  await expect(page.locator(".relationship-row")).toHaveCount(34);
  await page.getByLabel("Search relationships").fill("REL-CASTING-HOME");
  await expect(page.locator("#relationship-count")).toHaveText("1 relationship");
  await page.locator(".relationship-row:visible").click();
  await expect(page.locator("#drawer-meta")).toContainText("REL-CASTING-HOME");
  await page.getByLabel("Search relationships").fill("");
  await page.locator("#relationship-status").selectOption("scenario");
  await expect(page.locator("#relationship-count")).not.toHaveText("0 relationships");
});

test("publishes metadata-only vendor links with the independence disclosure", async ({ page }) => {
  await expect(page.locator(".vendor-links a")).toHaveCount(4);
  await expect(page.locator(".vendor blockquote")).toContainText("not sponsored, endorsed, reviewed, or approved by Samsung");
  const hrefs = await page.locator(".vendor-links a").evaluateAll((links) => links.map((link) => (link as HTMLAnchorElement).href));
  expect(hrefs.every((href) => href.includes("samsung.com"))).toBeTruthy();
});

test("serves the rights-aware release artifacts and manifests", async ({ request }) => {
  const assets = [
    ["data/evidence/source-rights.json", /application\/json/],
    ["data/evidence/vendor-links.json", /application\/json/],
    ["data/evidence/run-manifest.json", /application\/json/],
    ["data/hospitality-experience-graph.json", /application\/json/],
    ["data/hospitality-experience-graph.graphml", /(application|text)\//],
    ["downloads/hxg-linkedin-carousel.pdf", /application\/pdf/],
    ["downloads/hxg-poster.pdf", /application\/pdf/],
  ] as const;
  for (const [path, contentType] of assets) {
    const response = await request.get(path);
    expect(response.ok(), path).toBeTruthy();
    expect(response.headers()["content-type"], path).toMatch(contentType);
  }
  const graph = await (await request.get("data/hospitality-experience-graph.json")).json();
  expect(graph.release).toBe("hxg-v0.3.0");
  expect(graph.elements.nodes).toHaveLength(30);
  expect(graph.elements.edges).toHaveLength(34);
  const manifest = await (await request.get("data/evidence/run-manifest.json")).json();
  expect(manifest.release_version).toBe("0.3.0");
  expect(manifest.generated_counts).toMatchObject({ sources: 10, claims: 19, entities: 30, relationships: 34, contradictions: 4, countries: 1 });
});

test("has no page overflow or serious accessibility findings", async ({ page }) => {
  expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(1);
  const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
  const blocking = results.violations.filter((item) => item.impact === "serious" || item.impact === "critical");
  expect(blocking).toEqual([]);
});

test("enforces the static-site security policy without inline-style exceptions", async ({ page }) => {
  const csp = await page.locator('meta[http-equiv="content-security-policy"]').getAttribute("content");
  expect(csp).toContain("object-src 'none'");
  expect(csp).toContain("base-uri 'self'");
  expect(csp).toContain("form-action 'none'");
  expect(csp).not.toContain("style-src-attr 'unsafe-inline'");
  await expect(page.locator('meta[name="referrer"]')).toHaveAttribute("content", "no-referrer");
  await expect(page.locator("[style]")).toHaveCount(0);
});

test("reflows at release widths with usable controls", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium", "One Chromium sweep covers explicit widths.");
  for (const width of [320, 390, 768, 1024, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    await page.waitForTimeout(160);
    expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth), `${width}px overflow`).toBeLessThanOrEqual(1);
    if (width <= 780) {
      const targets = page.locator(".mobile-nav summary, .repo-link, .mode-tabs button, .pathway-row, .node-button, #view-linked-evidence");
      for (const box of await targets.evaluateAll((items) => items.filter((item) => (item as HTMLElement).offsetParent !== null).map((item) => item.getBoundingClientRect().toJSON()))) {
        expect(box.height, `${width}px target height`).toBeGreaterThanOrEqual(44);
        expect(box.width, `${width}px target width`).toBeGreaterThanOrEqual(44);
      }
    }
  }
});
