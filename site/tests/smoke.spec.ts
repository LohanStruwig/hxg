import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const seriousAxeTags = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"];

test.beforeEach(async ({ page }) => {
  await page.goto("./");
  await expect(page.locator("#cy")).toHaveAttribute("data-ready", "true");
});

test("loads the frozen release without runtime errors", async ({ page }) => {
  const errors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error" || message.type() === "warning") errors.push(message.text());
  });
  await page.reload();
  await expect(page).toHaveTitle("Hospitality Experience Graph");
  await expect(page.getByRole("heading", { level: 1, name: /From screen to stay/i })).toBeVisible();
  await expect(page.locator("astro-dev-toolbar, vite-error-overlay, #webpack-dev-server-client-overlay")).toHaveCount(0);
  await expect(page.locator("#cy")).toHaveAttribute("data-node-count", "32");
  await expect(page.locator("#cy")).toHaveAttribute("data-relationship-count", "42");
  expect(errors).toEqual([]);
});

test("keeps navigation sticky and anchors clear", async ({ page }, testInfo) => {
  const skipLink = page.getByRole("link", { name: "Skip to evidence" });
  if (testInfo.project.name === "desktop-webkit" || testInfo.project.name === "iphone-14") {
    await skipLink.focus();
  } else {
    await page.keyboard.press("Tab");
  }
  await expect(skipLink).toBeFocused();
  await expect(skipLink).toBeVisible();
  const compactNavigation = (page.viewportSize()?.width || 1440) <= 980;
  const menu = page.locator(".mobile-nav");
  if (compactNavigation) {
    await menu.locator("summary").focus();
    await page.keyboard.press("Enter");
    await expect(menu).toHaveAttribute("open", "");
    await page.keyboard.press("Escape");
    await expect(menu).not.toHaveAttribute("open", "");
  }
  for (const target of [
    { link: "Graph", heading: "#graph-title" },
    { link: "Evidence", heading: "#evidence-title" },
    { link: "Limitations", heading: "#limits-title" },
    { link: "Downloads", heading: "#downloads-title" },
  ]) {
    if (compactNavigation) {
      await menu.locator("summary").click();
      await menu.getByRole("link", { name: target.link, exact: true }).click();
      await expect(menu).not.toHaveAttribute("open", "");
    } else {
      await page.locator(".primary-nav").getByRole("link", { name: target.link, exact: true }).click();
    }
    await expect(page.locator(target.heading)).toBeInViewport();
    const geometry = await page.evaluate((headingSelector) => {
      const header = document.querySelector(".site-header")!.getBoundingClientRect();
      const heading = document.querySelector(headingSelector)!.getBoundingClientRect();
      return { headerTop: header.top, headerBottom: header.bottom, headingTop: heading.top };
    }, target.heading);
    expect(Math.abs(geometry.headerTop)).toBeLessThanOrEqual(1);
    expect(geometry.headingTop).toBeGreaterThan(geometry.headerBottom + 8);
  }
});

test("searches, filters, zooms, resets, and exposes list parity", async ({ page }) => {
  if ((page.viewportSize()?.width || 1440) <= 760) {
    await page.locator("#graph-filters summary").click();
    await expect(page.locator("#graph-filters")).toHaveAttribute("open", "");
  }
  const search = page.getByLabel("Find a node");
  await search.fill("privacy");
  await expect(page.locator("#graph-status")).toContainText("Search “privacy”");
  await expect(page.locator("#graph-status")).not.toContainText("0 nodes");
  await search.fill("nothing-matches-this-query");
  await expect(page.locator("#graph-status")).toContainText("No results");
  await expect(page.locator("#graph-status")).toContainText("0 nodes · 0 relationships");
  await page.getByRole("button", { name: "Reset graph" }).click();
  await expect(page.locator("#cy")).toHaveAttribute("data-relationship-count", "42");
  await page.getByRole("checkbox", { name: "Modeled scenario" }).uncheck();
  const filteredCount = Number(await page.locator("#cy").getAttribute("data-relationship-count"));
  expect(filteredCount).toBeLessThan(42);
  await page.getByRole("button", { name: "Zoom in" }).click();
  await expect(page.locator("#graph-status")).toContainText("Zoomed in");
  await page.getByRole("button", { name: "Fit graph" }).click();
  await expect(page.locator("#graph-status")).toContainText("fitted");
  await page.getByRole("button", { name: "Relationship list" }).click();
  await expect(page.locator("#relationship-list article")).toHaveCount(42);
  await page.getByLabel("Search relationships").fill("privacy");
  await expect(page.locator("#relationship-count")).not.toHaveText("0 relationships");
  await page.locator("#relationship-list article:visible").first().getByRole("button", { name: "Inspect linked evidence" }).click();
  await expect(page.getByRole("button", { name: "Interactive graph" })).toHaveAttribute("aria-pressed", "true");
  await expect(page.locator("#drawer-title")).not.toHaveText("Human experience");
  if ((page.viewportSize()?.width || 1440) > 760) {
    const inspectionGeometry = await page.evaluate(() => {
      const header = document.querySelector(".site-header")!.getBoundingClientRect();
      const heading = document.querySelector("#graph-title")!.getBoundingClientRect();
      return { headerBottom: header.bottom, headingTop: heading.top };
    });
    expect(inspectionGeometry.headingTop).toBeGreaterThan(inspectionGeometry.headerBottom + 8);
  }
  const metadataAlignment = await page.locator("#drawer-meta > div").first().evaluate((row) => {
    const term = row.querySelector("dt")!.getBoundingClientRect();
    const detail = row.querySelector("dd")!.getBoundingClientRect();
    return Math.abs(term.left - detail.left);
  });
  expect(metadataAlignment).toBeLessThanOrEqual(1);
  const linkedClaimCount = await page.locator("#drawer-claims .drawer-claim").count();
  await page.getByRole("button", { name: "View linked evidence" }).click();
  await expect(page.locator("#claim-count")).toHaveText(`${linkedClaimCount} claim${linkedClaimCount === 1 ? "" : "s"}`);
  await expect(page.getByLabel("Search claims")).toBeFocused();
});

test("filters the evidence register to five J.D. Power facts", async ({ page }) => {
  await page.getByLabel("Search claims").fill("JDP");
  await page.getByLabel("Filter by evidence class").selectOption("fact");
  await expect(page.locator("#claim-count")).toHaveText("5 claims");
  await expect(page.locator("#claim-rows tr:visible")).toHaveCount(5);
});

test("has no page-level overflow and no serious or critical axe findings", async ({ page }) => {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(overflow).toBeLessThanOrEqual(1);
  const results = await new AxeBuilder({ page }).withTags(seriousAxeTags).analyze();
  const blocking = results.violations.filter((violation) => violation.impact === "serious" || violation.impact === "critical");
  expect(blocking).toEqual([]);
});

test("reflows at release widths with 44px primary touch targets", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium", "One Chromium viewport sweep covers the explicit release widths.");
  for (const width of [320, 390, 768, 1024, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    await page.waitForTimeout(180);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow, `${width}px viewport overflow`).toBeLessThanOrEqual(1);
    if (width <= 760) {
      const targets = page.locator(".mobile-nav summary, .repo-link, .view-switch button, .graph-controls button, #graph-filters summary");
      for (const box of await targets.evaluateAll((elements) => elements.filter((element) => (element as HTMLElement).offsetParent !== null).map((element) => element.getBoundingClientRect().toJSON()))) {
        expect(box.height, `${width}px touch-target height`).toBeGreaterThanOrEqual(44);
        expect(box.width, `${width}px touch-target width`).toBeGreaterThanOrEqual(44);
      }
    }
  }
});

test("serves release downloads and stable graph coordinates", async ({ request }) => {
  const assets = [
    ["data/hospitality-experience-graph.json", /application\/json/],
    ["data/hospitality-experience-graph.graphml", /(application|text)\//],
    ["downloads/hxg-linkedin-carousel.pdf", /application\/pdf/],
    ["downloads/hxg-poster.pdf", /application\/pdf/],
  ] as const;
  for (const [path, type] of assets) {
    const response = await request.get(path);
    expect(response.ok(), path).toBeTruthy();
    expect(response.headers()["content-type"], path).toMatch(type);
  }
  const graph = await (await request.get("data/hospitality-experience-graph.json")).json();
  expect(graph.layout).toMatchObject({ name: "preset", seed: 42 });
  expect(graph.elements.nodes).toHaveLength(32);
  expect(graph.elements.nodes.every((node: any) => Number.isFinite(node.position.x) && Number.isFinite(node.position.y))).toBeTruthy();
});
