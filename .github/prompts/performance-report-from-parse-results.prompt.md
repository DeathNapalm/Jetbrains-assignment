# Reusable Prompt: Build YouTrack Performance Report Package

Use this prompt when all 3 performance scripts were run successfully and you need a complete, portable report package with parser outputs and Grafana evidence.

## Prompt text

You are working in this repository.

Goal:
Create a complete performance test report package using parse_results.py outputs and Grafana screenshots. The final deliverable must be a standalone folder `docs/report_<time>/` containing the report, all referenced images, and text artifacts.

Requirements:
1. Ensure list/read scenarios measure `GET /api/sortedIssues` for list calls (not `GET /api/issues`) in:
   - `perf_test_scripts/src/test/scala/youtrack/UC01_createOrUpdate.scala`
   - `perf_test_scripts/src/test/scala/youtrack/UC03_viewIssue.scala`
2. Use `parse_results.py` as the single source for request graph/table artifacts.
3. If parser time-window files are missing, update `parse_results.py` to produce:
   - `perf_test_scripts/results/parsed/simulation_time_windows.csv`
   - `perf_test_scripts/results/parsed/test_time_range.csv`
4. Run `python3 parse_results.py`.
5. Use `test_time_range.csv` (`from_ms`, `to_ms`) as the exact Grafana time window for all screenshots.
6. Reuse Playwright snippets from `.github/playwright/grafana-screenshot-snippets.js`:
   - `loginGrafana(page, username, password)`
   - `captureResourceDashboard(page)`
   - `captureJmxDashboard(page)`
7. Capture screenshots from Grafana:
   - YouTrack Resource Monitoring: CPU panel, Memory panel, full dashboard
   - YouTrack JVM JMX Monitoring: full dashboard, JVM memory panel, JVM threads/classes panel
8. Build or update working report content to match the final structure:
   - Test Analysis paragraph with workload profile link
   - Test Details (combined UTC window + duration)
   - Bundled test artifacts section with clickable links
   - Request graph section
   - Response-time table with columns: `Usecase`, `Transaction`, `Total`, `Success`, `Failed`, `Error rate %`, `Avg ms`, `P50 ms`, `P90 ms`, `Min ms`, `Max ms`
   - Transaction names in column 2 must be action names only (no `Script: ...` prefix)
   - SLO compliance paragraph immediately after response-time table:
     - `GET /api/issue/{id}?fields=... <= 500 ms`
     - `POST /api/issuesGetter?fields=... <= 1000 ms`
     - `GET /api/sortedIssues <= 500 ms`
     - Mark each as PASS/FAIL using measured p90 values
   - Aggregated-by-script table
   - Grafana evidence section with embedded images
   - Do not mention in the report that results, tables, graphs, or time windows are parser-generated or produced by `parse_results.py`
9. Package final deliverable into `docs/report_<time>/`:
   - Copy `report.md`
   - Copy every image referenced by the report into the same folder
   - Copy text artifacts (`latency_summary.csv`, `requests_over_time.csv`, `simulation_time_windows.csv`, `test_time_range.csv`) into the same folder
   - Ensure report links are self-contained and resolvable from `docs/report_<time>/report.md`
10. Verify `parse_results.py` syntax with `python3 -m py_compile parse_results.py`.

Output and paths:
- Parser outputs:
  - `perf_test_scripts/results/parsed/latency_summary.csv`
  - `perf_test_scripts/results/parsed/requests_over_time.svg`
  - `perf_test_scripts/results/parsed/requests_over_time.csv`
  - `perf_test_scripts/results/parsed/simulation_time_windows.csv`
  - `perf_test_scripts/results/parsed/test_time_range.csv`
- Playwright helper:
  - `.github/playwright/grafana-screenshot-snippets.js`
- Screenshot assets (initially generated under `docs/`, then copied into package):
  - `cpu_usage_panel.png`
  - `memory_usage_panel.png`
  - `youtrack_resource_dashboard_full.png`
  - `youtrack_jvm_jmx_dashboard_full.png`
  - `youtrack_jvm_memory_panel.png`
  - `youtrack_jvm_threads_panel.png`
- Final packaged report:
  - `docs/report_<time>/report.md`

Execution notes:
- Do not manually guess time windows. Always use parser-generated `test_time_range.csv`.
- Keep all reported numbers aligned with parser CSV files.
- For panel screenshots, prefer deterministic solo-panel capture (panelId-based) to avoid wrong panel crops.
- Keep report language concise and professional.
- Keep implementation details out of the report narrative; do not call out `parse_results.py` or say that the results are parser-generated.

Success criteria:
- A standalone package `docs/report_<time>/` exists.
- `report.md` in that folder renders correctly with working links and images.
- SLO compliance section is present after the response-time table and reflects measured p90 values.
- `parse_results.py` runs and compiles successfully.
