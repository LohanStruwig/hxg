import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const withheldPaths = [
  "data/evidence/run-manifest.json",
  "data/evidence/claims.json",
  "data/hospitality-experience-graph.json",
  "data/hospitality-experience-graph.graphml",
  "downloads/hxg-linkedin-carousel.pdf",
  "downloads/hxg-poster.pdf",
];

test("serves the neutral source-rights review page", async ({ page }) => {
  const errors: string[] = [];
  page.on("console", (message) => {
    if (["error", "warning"].includes(message.type())) errors.push(message.text());
  });
  await page.goto("./");
  await expect(page).toHaveTitle("HXG - Source-rights review");
  await expect(page.getByRole("heading", { level: 1, name: /source-rights review/i })).toBeVisible();
  await expect(page.getByRole("status")).toContainText("Review in progress");
  await expect(page.getByRole("link", { name: "View the public repository" })).toHaveAttribute("href", "https://github.com/LohanStruwig/hxg");
  await expect(page.locator("astro-dev-toolbar, vite-error-overlay, #webpack-dev-server-client-overlay")).toHaveCount(0);
  expect(errors).toEqual([]);
});

test("withholds old evidence, graph, and publication URLs", async ({ request }) => {
  for (const path of withheldPaths) {
    const response = await request.get(path);
    expect(response.status(), path).toBe(404);
  }
});

test("has no page overflow or serious accessibility findings", async ({ page }) => {
  await page.goto("./");
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(1);
  const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
  const blocking = results.violations.filter((item) => item.impact === "serious" || item.impact === "critical");
  expect(blocking).toEqual([]);
});

test("keeps maintenance controls usable at release widths", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium", "One Chromium sweep covers explicit widths.");
  await page.goto("./");
  for (const width of [320, 390, 768, 1024, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    await page.waitForTimeout(160);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow, `${width}px viewport overflow`).toBeLessThanOrEqual(1);
    const links = page.locator("a:visible");
    for (const box of await links.evaluateAll((items) => items.map((item) => item.getBoundingClientRect().toJSON()))) {
      expect(box.height, `${width}px link height`).toBeGreaterThanOrEqual(44);
      expect(box.width, `${width}px link width`).toBeGreaterThanOrEqual(44);
    }
  }
});
