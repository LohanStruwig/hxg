import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const seriousAxeTags = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"];

test.beforeEach(async ({ page }) => {
  await page.goto("./");
  await expect(page.locator("#graph-explorer")).toHaveAttribute("data-graph-ready", "true");
});

test("loads v0.2.0 without runtime errors", async ({ page }) => {
  const errors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error" || message.type() === "warning") errors.push(message.text());
  });
  await page.reload();
  await expect(page).toHaveTitle("Hospitality Experience Graph");
  await expect(page.getByRole("heading", { level: 1, name: /From screen to stay/i })).toBeVisible();
  await expect(page.getByText("Independent research · Release 0.2.0")).toBeVisible();
  await expect(page.locator("astro-dev-toolbar, vite-error-overlay, #webpack-dev-server-client-overlay")).toHaveCount(0);
  await expect(page.locator("#graph-explorer")).toHaveAttribute("data-selected-view", "guided");
  await expect(page.locator("#graph-explorer")).toHaveAttribute("data-visible-nodes", "12");
  await expect(page.locator("#graph-explorer")).toHaveAttribute("data-visible-edges", "6");
  await expect(page.locator("#graph-explorer")).toHaveAttribute("data-label-collisions", "0");
  await expect(page.locator("#graph-explorer")).toHaveAttribute("data-edge-crossings", "0");
  await expect(page.locator('meta[name="referrer"]')).toHaveAttribute("content", "no-referrer");
  await expect(page.locator('meta[http-equiv="content-security-policy"]')).toHaveAttribute("content", /object-src 'none'/);
  expect(errors).toEqual([]);
});

test("keeps navigation sticky and anchors clear", async ({ page }, testInfo) => {
  const skipLink = page.getByRole("link", { name: "Skip to evidence" });
  if (testInfo.project.name === "desktop-webkit" || testInfo.project.name === "iphone-14") await skipLink.focus();
  else await page.keyboard.press("Tab");
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
    { link: "Map", heading: "#graph-title" },
    { link: "Evidence", heading: "#evidence-title" },
    { link: "Limitations", heading: "#limits-title" },
    { link: "Downloads", heading: "#downloads-title" },
  ]) {
    if (compactNavigation) {
      await menu.locator("summary").click();
      await menu.getByRole("link", { name: target.link, exact: true }).click();
      await expect(menu).not.toHaveAttribute("open", "");
    } else await page.locator(".primary-nav").getByRole("link", { name: target.link, exact: true }).click();
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

test("renders six one-to-one guided pathways and linked evidence", async ({ page }) => {
  await expect(page.locator(".pathway-row")).toHaveCount(6);
  const expected = [
    ["Cast from your device", "Feel at home"],
    ["Control room settings", "Feel in control"],
    ["Connect stay context", "Feel recognized"],
    ["Present content accessibly", "Feel included"],
    ["Protect sessions and data", "Feel secure"],
    ["Request services and help", "Feel supported"],
  ];
  for (let index = 0; index < expected.length; index += 1) {
    const row = page.locator(".pathway-row").nth(index);
    await expect(row.locator(".capability-node strong")).toHaveText(expected[index][0]);
    await expect(row.locator(".pathway-arrow")).toContainText("can support");
    await expect(row.locator(".outcome-node strong")).toHaveText(expected[index][1]);
  }
  await page.locator(".pathway-row").nth(4).click();
  await expect(page.locator("#drawer-title")).toHaveText("Protect sessions and data");
  await expect(page.locator("#drawer-path")).toContainText("can support");
  await expect(page.locator("#drawer-meta")).toContainText("Supported inference");
  await expect(page.locator("#graph-explorer")).toHaveAttribute("data-label-collisions", "0");
  await expect(page.locator("#graph-explorer")).toHaveAttribute("data-edge-crossings", "0");
});

test("keeps all nodes edge-free at rest and focuses only one hop", async ({ page }) => {
  await page.getByRole("tab", { name: "Explore all nodes" }).click();
  await expect(page.locator(".node-group")).toHaveCount(5);
  await expect(page.locator(".node-button")).toHaveCount(32);
  await expect(page.locator("#graph-explorer")).toHaveAttribute("data-selected-view", "explore");
  await expect(page.locator("#graph-explorer")).toHaveAttribute("data-visible-nodes", "32");
  await expect(page.locator("#graph-explorer")).toHaveAttribute("data-visible-edges", "0");
  await expect(page.locator(".focus-relationship")).toHaveCount(0);

  await page.getByLabel("Find a node").fill("Data governance");
  await expect(page.locator("#focus-title")).toHaveText("Data governance");
  await expect(page.locator(".focus-relationship")).toHaveCount(1);
  await expect(page.locator("#graph-explorer")).toHaveAttribute("data-selected-view", "focus");
  await expect(page.locator("#graph-explorer")).toHaveAttribute("data-visible-nodes", "2");
  await expect(page.locator("#graph-explorer")).toHaveAttribute("data-visible-edges", "1");
  await expect(page.locator("#graph-explorer")).toHaveAttribute("data-label-collisions", "0");
  await expect(page.locator("#graph-explorer")).toHaveAttribute("data-edge-crossings", "0");

  await page.getByRole("button", { name: "Clear focused map" }).click();
  await expect(page.locator("#graph-explorer")).toHaveAttribute("data-visible-edges", "0");
  await page.getByLabel("Find a node").fill("nothing-matches-this-query");
  await expect(page.locator("#node-empty")).toBeVisible();
  await expect(page.locator("#graph-explorer")).toHaveAttribute("data-visible-nodes", "0");
  await expect(page.locator("#graph-explorer")).not.toHaveAttribute("data-visible-edges", "42");
});

test("retains all 42 searchable relationship records", async ({ page }) => {
  await page.getByRole("tab", { name: "Relationship list" }).click();
  await expect(page.locator(".relationship-row")).toHaveCount(42);
  await page.getByLabel("Search relationships").fill("REL-OEM-ECOSYSTEM");
  await expect(page.locator("#relationship-count")).toHaveText("1 relationship");
  await page.locator(".relationship-row:visible").click();
  await expect(page.locator("#drawer-meta")).toContainText("REL-OEM-ECOSYSTEM");
  await page.getByLabel("Search relationships").fill("");
  await page.getByLabel("Evidence state").selectOption("scenario");
  await expect(page.locator("#relationship-count")).toHaveText("4 relationships");
  await page.getByLabel("Evidence state").selectOption("all");
  await page.getByLabel("Search relationships").fill("REL-CASTING-HOME");
  await page.locator(".relationship-row:visible").click();
  const linkedClaimCount = await page.locator("#drawer-claims article").count();
  await page.getByRole("button", { name: "View linked evidence" }).click();
  await expect(page.locator("#claim-count")).toHaveText(`${linkedClaimCount} claims`);
  await expect(page.getByLabel("Search claims")).toBeFocused();
});

test("filters the evidence register to five J.D. Power facts", async ({ page }) => {
  await page.getByLabel("Search claims").fill("JDP");
  await page.getByLabel("Filter by evidence class").selectOption("fact");
  await expect(page.locator("#claim-count")).toHaveText("5 claims");
  await expect(page.locator("#claim-rows tr:visible")).toHaveCount(5);
});

test("has no page overflow or serious and critical axe findings", async ({ page }) => {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(overflow).toBeLessThanOrEqual(1);
  const results = await new AxeBuilder({ page }).withTags(seriousAxeTags).analyze();
  const blocking = results.violations.filter((violation) => violation.impact === "serious" || violation.impact === "critical");
  expect(blocking).toEqual([]);
});

test("reflows at release widths with 44px controls", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium", "One Chromium viewport sweep covers the explicit release widths.");
  for (const width of [320, 390, 768, 1024, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    await page.waitForTimeout(160);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow, `${width}px viewport overflow`).toBeLessThanOrEqual(1);
    if (width <= 780) {
      const targets = page.locator(".mobile-nav summary, .repo-link, .mode-tabs button, .pathway-row, .node-button, #view-linked-evidence");
      for (const box of await targets.evaluateAll((elements) => elements.filter((element) => (element as HTMLElement).offsetParent !== null).map((element) => element.getBoundingClientRect().toJSON()))) {
        expect(box.height, `${width}px touch-target height`).toBeGreaterThanOrEqual(44);
        expect(box.width, `${width}px touch-target width`).toBeGreaterThanOrEqual(44);
      }
    }
  }
});

test("serves v0.2.0 downloads and deterministic presentation metadata", async ({ page, request }) => {
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
  expect(graph.release).toBe("hxg-v0.2.0");
  expect(graph.layout).toMatchObject({ name: "preset", algorithm: "semantic-groups", seed: 42 });
  expect(graph.guided_pathways).toHaveLength(6);
  expect(graph.elements.nodes).toHaveLength(32);
  expect(graph.elements.edges).toHaveLength(42);
  expect(graph.elements.nodes.every((node: any) => Number.isFinite(node.position.x) && Number.isFinite(node.position.y))).toBeTruthy();
  expect(graph.elements.nodes.every((node: any) => ["display_label", "reader_summary", "story_lane", "story_layer", "label_priority"].every((field) => field in node.data))).toBeTruthy();
  expect(graph.elements.edges.every((edge: any) => ["display_verb", "relationship_role", "story_lane", "primary_path"].every((field) => field in edge.data))).toBeTruthy();
  expect(graph.elements.edges.filter((edge: any) => edge.data.primary_path)).toHaveLength(6);
  const scriptSources = await page.locator("script[src]").evaluateAll((scripts) => scripts.map((script) => (script as HTMLScriptElement).src));
  for (const source of scriptSources) expect((await request.get(`${source}.map`)).status(), `${source}.map should not be deployed`).toBe(404);
});
