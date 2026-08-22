/*
  Playwright snippets used to capture Grafana screenshots for the performance report workflow.
  These snippets are intended for the run_playwright_code tool where `page` is already available.
*/

const fs = require('fs');
const path = require('path');

const REPOSITORY_ROOT = path.resolve(__dirname, '../..');
const OUTPUT_DIR = path.join(REPOSITORY_ROOT, 'docs');
const TEST_TIME_RANGE_CSV = path.join(REPOSITORY_ROOT, 'perf_test_scripts', 'results', 'parsed', 'test_time_range.csv');

function readParserTimeRange() {
  const csv = fs.readFileSync(TEST_TIME_RANGE_CSV, 'utf8').trim();
  const lines = csv.split(/\r?\n/).filter(Boolean);

  if (lines.length < 2) {
    throw new Error(`Missing parser time range row in ${TEST_TIME_RANGE_CSV}`);
  }

  const [windowName, fromMs, toMs] = lines[1].split(',');
  if (!windowName || !fromMs || !toMs) {
    throw new Error(`Invalid parser time range row in ${TEST_TIME_RANGE_CSV}: ${lines[1]}`);
  }

  return { fromMs, toMs };
}

const TIME_RANGE = readParserTimeRange();

const DASHBOARD_URLS = {
  resource: `http://localhost:3000/d/youtrack-resource-monitoring/youtrack-resource-monitoring?orgId=1&from=${TIME_RANGE.fromMs}&to=${TIME_RANGE.toMs}&timezone=browser`,
  jmx: `http://localhost:3000/d/1d99f121-2377-49a2-9275-003090d63b1e/youtrack-jvm-jmx-monitoring?orgId=1&from=${TIME_RANGE.fromMs}&to=${TIME_RANGE.toMs}&timezone=browser`,
};

const SOLO_PANEL_URLS = {
  resourceCpu: `http://localhost:3000/d-solo/youtrack-resource-monitoring/youtrack-resource-monitoring?orgId=1&panelId=20&from=${TIME_RANGE.fromMs}&to=${TIME_RANGE.toMs}&timezone=browser`,
  resourceMemory: `http://localhost:3000/d-solo/youtrack-resource-monitoring/youtrack-resource-monitoring?orgId=1&panelId=21&from=${TIME_RANGE.fromMs}&to=${TIME_RANGE.toMs}&timezone=browser`,
  jmxMemory: `http://localhost:3000/d-solo/1d99f121-2377-49a2-9275-003090d63b1e/youtrack-jvm-jmx-monitoring?orgId=1&panelId=1&from=${TIME_RANGE.fromMs}&to=${TIME_RANGE.toMs}&timezone=browser`,
  jmxThreads: `http://localhost:3000/d-solo/1d99f121-2377-49a2-9275-003090d63b1e/youtrack-jvm-jmx-monitoring?orgId=1&panelId=2&from=${TIME_RANGE.fromMs}&to=${TIME_RANGE.toMs}&timezone=browser`,
};

async function closeSideMenuIfOpen(page) {
  const closeMenuButton = page.getByRole('button', { name: 'Close menu' }).first();
  if (await closeMenuButton.count()) {
    await closeMenuButton.click();
  }
}

async function waitForDashboardReady(page) {
  await page.waitForLoadState('networkidle');
  await closeSideMenuIfOpen(page);
  await page.waitForTimeout(1200);
}

async function screenshotSoloPanel(page, panelUrl, outputPath) {
  await page.goto(panelUrl, { waitUntil: 'networkidle' });
  await page.setViewportSize({ width: 1600, height: 700 });
  await page.waitForTimeout(1200);

  const region = page.getByRole('region').first();
  if (await region.count()) {
    await region.scrollIntoViewIfNeeded();
    await region.screenshot({ path: outputPath });
    return;
  }

  const panelContainer = page
    .locator('[data-testid*="panel"], [class*="panel-container"], [class*="panel"]')
    .first();
  if (await panelContainer.count()) {
    await panelContainer.scrollIntoViewIfNeeded();
    await panelContainer.screenshot({ path: outputPath });
    return;
  }

  await page.screenshot({ path: outputPath });
}

// Optional login helper (used when Grafana prompts for auth).
async function loginGrafana(page, username = 'admin', password = 'admin') {
  await page.goto('http://localhost:3000/login', { waitUntil: 'networkidle' });
  await page.fill('input[placeholder="email or username"]', username);
  await page.fill('input[placeholder="password"]', password);
  await page.click('button:has-text("Log in")');

  // If the password-update page appears, skip it.
  const skipButton = page.locator('button:has-text("Skip")');
  if (await skipButton.count()) {
    await skipButton.first().click();
  }
}

// Capture CPU + memory panels and full dashboard from YouTrack Resource Monitoring.
async function captureResourceDashboard(page) {
  await page.goto(DASHBOARD_URLS.resource, { waitUntil: 'networkidle' });
  await page.setViewportSize({ width: 1600, height: 1200 });
  await waitForDashboardReady(page);

  await page.screenshot({
    path: `${OUTPUT_DIR}/youtrack_resource_dashboard_full.png`,
    fullPage: true,
  });

  await screenshotSoloPanel(page, SOLO_PANEL_URLS.resourceCpu, `${OUTPUT_DIR}/cpu_usage_panel.png`);
  await screenshotSoloPanel(page, SOLO_PANEL_URLS.resourceMemory, `${OUTPUT_DIR}/memory_usage_panel.png`);
}

// Capture full dashboard + JVM panels from YouTrack JVM JMX Monitoring.
async function captureJmxDashboard(page) {
  await page.goto(DASHBOARD_URLS.jmx, { waitUntil: 'networkidle' });
  await page.setViewportSize({ width: 1600, height: 1200 });
  await waitForDashboardReady(page);

  await page.screenshot({
    path: `${OUTPUT_DIR}/youtrack_jvm_jmx_dashboard_full.png`,
    fullPage: true,
  });

  await screenshotSoloPanel(page, SOLO_PANEL_URLS.jmxMemory, `${OUTPUT_DIR}/youtrack_jvm_memory_panel.png`);
  await screenshotSoloPanel(page, SOLO_PANEL_URLS.jmxThreads, `${OUTPUT_DIR}/youtrack_jvm_threads_panel.png`);
}

module.exports = {
  TIME_RANGE,
  DASHBOARD_URLS,
  SOLO_PANEL_URLS,
  loginGrafana,
  captureResourceDashboard,
  captureJmxDashboard,
};
