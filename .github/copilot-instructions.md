# Project Guidelines

## Project Context

- This repository provisions YouTrack Server, generates a production-scale test data set, runs Gatling performance workloads, monitors the system with Prometheus and Grafana, and produces performance reports.
- Treat `README.md` as the entry point for operations and `docs/performance-testing-methodology.md` as the source of truth for workload assumptions, SLOs, test phases, and result interpretation. Update those documents when behavior or methodology changes.

## Architecture

- `docker-compose.yml` owns the YouTrack service and optional test-data generator. Monitoring configuration belongs in `monitoring/` and is launched with `monitoring/docker-compose-monitoring.yml`.
- `perf_test_scripts/src/test/scala/youtrack/` contains Gatling simulations. Keep simulation resources in `perf_test_scripts/data/` and run simulations through `perf_test_scripts/run.sh` rather than introducing a separate local Gatling setup.
- `scripts/test_data_generation/` contains the Python REST client, configuration, data generator, and backup helpers. Keep environment parsing and defaults in `config.py`; keep YouTrack HTTP behavior in `youtrack_api.py`.
- `scripts/performance_reporting/parse_results.py` parses Gatling logs and writes generated artifacts beneath `perf_test_scripts/results/parsed/`.

## Configuration And Security

- Configure service URLs, tokens, workload size, concurrency, duration, and ratios through the existing environment variables. Preserve useful local defaults where the code already provides them.
- Never hard-code, commit, print, or include a real `YOUTRACK_TOKEN` in examples. Use placeholders such as `<token>` or `perm:<your-token>`. Local `.env` files are ignored and must remain untracked.
- Preserve the distinction between host URLs such as `http://localhost:8080` and container-network URLs such as `http://youtrack:8080`.
- Do not run full data generation, long performance scenarios, volume deletion (`docker compose down -v`), or backup cleanup unless the user explicitly requests the operation. Full generation targets 100 users and 100,000 issues and can take hours.

## Code Conventions

- Follow the style of the touched language and neighboring files; avoid unrelated refactors in benchmark and infrastructure changes.
- For Gatling scenarios, read configuration from `sys.env`, use CSV feeders for variable test inputs, group script-level and action-level transactions, assert expected HTTP statuses, and guard flows that depend on optional saved session values.
- Keep workload controls in `perf_test_scripts/run.sh` aligned with the Scala environment-variable names. Preserve the `youtrack.<ClassName>` simulation naming used by the runner and reporting parser.
- For Python API calls, reuse the shared `requests.Session`, explicit timeouts, retry policy, `raise_for_status()`, and structured logging. Propagate request failures unless the caller intentionally implements recovery.
- Use `pathlib.Path` for repository file paths and the standard `csv` and `json` modules for structured data. Keep type hints and docstrings consistent with neighboring Python code.
- Treat `perf_test_scripts/results/`, test-data logs, generated backups, and timestamped report artifacts as generated output. Do not hand-edit or commit them unless the task specifically concerns captured results.

## Build And Validation

- Start YouTrack with `docker compose up -d youtrack` and check readiness with `docker compose ps` before running operations against it.
- Start the monitoring stack with `docker compose -f monitoring/docker-compose-monitoring.yml up -d` and verify it with `docker compose -f monitoring/docker-compose-monitoring.yml ps`. Grafana, Prometheus, cAdvisor, and the JMX exporter must be available while collecting load-test metrics.
- Stop monitoring with `docker compose -f monitoring/docker-compose-monitoring.yml down`. Do not add `-v` unless the user explicitly requests deletion of persisted monitoring data.
- Install Python dependencies with `python3 -m pip install -r scripts/test_data_generation/requirements.txt`.
- Run a Gatling workload with `SIMULATION_CLASS=youtrack.<ClassName> PERF_USERS=<users> PERF_DURATION=<seconds> ./perf_test_scripts/run.sh`; it requires a running YouTrack instance, Docker, and `YOUTRACK_TOKEN`.
- Generate report artifacts with `python3 scripts/performance_reporting/parse_results.py` after Gatling results exist.
- For Python-only changes, run `python3 -m compileall -q scripts` at minimum. For shell changes, run `bash -n` on each touched script. For Compose changes, run `docker compose config --quiet` and include the monitoring Compose file when it is affected.
- There is no standalone unit-test suite for the Gatling simulations. Validate scenario changes with the shortest practical smoke run and report when Docker, a token, or a live YouTrack instance prevents that validation.