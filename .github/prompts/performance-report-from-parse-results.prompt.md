# Reusable Prompt: Build Performance Test Report From parse_results.py

Use this prompt when all 3 performance scripts were run successfully and you need a complete report with parser outputs and Grafana evidence.

## Prompt text

You are working in this repository.

Goal:
Create a complete performance test result report using the existing parser script and Grafana dashboards.

Requirements:
1. Use parse_results.py as the single source for request graph/table artifacts.
2. If the parser does not export a combined test time range yet, update parse_results.py to produce:
   - perf_test_scripts/results/parsed/simulation_time_windows.csv
   - perf_test_scripts/results/parsed/test_time_range.csv
3. Run parse_results.py.
4. Use test_time_range.csv (from_ms, to_ms) as the exact Grafana time window for all screenshots.
5. Capture screenshots from dashboard "YouTrack Resource Monitoring":
   - CPU panel
   - Memory panel
   - Full dashboard view
6. Capture screenshots from dashboard "YouTrack JVM JMX Monitoring":
   - Full dashboard view
   - JVM memory panel
   - JVM threads/classes panel
7. Reuse the Playwright snippets in `.github/playwright/grafana-screenshot-snippets.js`:
   - `loginGrafana(page, username, password)`
   - `captureResourceDashboard(page)`
   - `captureJmxDashboard(page)`
7. Create or update docs/report.md with:
   - Test window (UTC, duration) from parser output
   - Request graph image from parse_results.py (requests_over_time.svg)
   - Transaction-level request table from latency_summary.csv
   - Aggregated-by-script table (total/success/failed/error rate/weighted avg,p50,p90,max)
   - Embedded screenshots for both dashboards
8. Verify parse_results.py is syntactically valid (py_compile).

Output and paths:
- Parser outputs:
  - perf_test_scripts/results/parsed/latency_summary.csv
  - perf_test_scripts/results/parsed/requests_over_time.svg
  - perf_test_scripts/results/parsed/simulation_time_windows.csv
  - perf_test_scripts/results/parsed/test_time_range.csv
- Playwright screenshot helper/snippets:
   - .github/playwright/grafana-screenshot-snippets.js
   - Functions to use: loginGrafana, captureResourceDashboard, captureJmxDashboard
- Screenshots (store under docs/):
  - docs/cpu_usage_panel.png
  - docs/memory_usage_panel.png
  - docs/youtrack_resource_dashboard_full.png
  - docs/youtrack_jvm_jmx_dashboard_full.png
  - docs/youtrack_jvm_memory_panel.png
  - docs/youtrack_jvm_threads_panel.png
- Report:
  - docs/report.md

Execution notes:
- Do not manually guess time windows. Always use test_time_range.csv from parse_results.py.
- Keep report numbers aligned with latency_summary.csv.
- If Grafana login is required, authenticate first, then navigate dashboards with the same from/to window.
- Prefer calling the snippet functions from `.github/playwright/grafana-screenshot-snippets.js` instead of duplicating ad-hoc Playwright code.
- If a requested panel is not uniquely detectable by title, capture at least the full dashboard and clearly label that in report.md.

Success criteria:
- docs/report.md exists and includes request graph, transaction table, aggregated table, and all available screenshot evidence.
- Time window in report matches test_time_range.csv exactly.
- parse_results.py runs successfully and compiles.
