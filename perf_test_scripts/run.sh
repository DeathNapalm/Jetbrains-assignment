#!/usr/bin/env bash
# Run the BrowseIssues Gatling simulation via Docker.
# All config via env vars; defaults work against the local docker-compose stack.
set -euo pipefail

YOUTRACK_URL="${YOUTRACK_URL:-http://youtrack:8080}"
YOUTRACK_TOKEN="${YOUTRACK_TOKEN:-}"
YOUTRACK_PROJECT="${YOUTRACK_PROJECT:-DEMO}"
PERF_USERS="${PERF_USERS:-10}"
PERF_DURATION="${PERF_DURATION:-120}"
SIMULATION_CLASS="${SIMULATION_CLASS:-youtrack.BrowseIssuesSimulation}"
PERF_CREATE_RATIO="${PERF_CREATE_RATIO:-30}"
YOUTRACK_LIST_QUERY="${YOUTRACK_LIST_QUERY:-}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Load token from .env if not set
if [ -z "$YOUTRACK_TOKEN" ] && [ -f "$SCRIPT_DIR/../scripts/test_data_generation/.env" ]; then
  YOUTRACK_TOKEN=$(grep '^YOUTRACK_TOKEN=' "$SCRIPT_DIR/../scripts/test_data_generation/.env" | cut -d= -f2- | tr -d '\r')
fi

if [ -z "$YOUTRACK_TOKEN" ]; then
  echo "ERROR: YOUTRACK_TOKEN is empty. Export it in the shell or set it in scripts/test_data_generation/.env." >&2
  exit 1
fi

echo "=== Gatling Simulation ==="
echo "  Target  : $YOUTRACK_URL  project=$YOUTRACK_PROJECT"
echo "  Users   : $PERF_USERS   duration=${PERF_DURATION}s"
echo "  Class   : $SIMULATION_CLASS"
echo "  Create% : $PERF_CREATE_RATIO"
echo "  Query   : ${YOUTRACK_LIST_QUERY:-<empty>}"
echo ""

docker run --rm \
  --network jb-try1_default \
  -e YOUTRACK_URL="$YOUTRACK_URL" \
  -e YOUTRACK_TOKEN="$YOUTRACK_TOKEN" \
  -e YOUTRACK_PROJECT="$YOUTRACK_PROJECT" \
  -e PERF_USERS="$PERF_USERS" \
  -e PERF_DURATION="$PERF_DURATION" \
  -e PERF_CREATE_RATIO="$PERF_CREATE_RATIO" \
  -e YOUTRACK_LIST_QUERY="$YOUTRACK_LIST_QUERY" \
  -e JAVA_OPTS="-Dgatling.charting.maxPlotPerSeries=1000" \
  -v "$SCRIPT_DIR/src/test/scala:/opt/gatling/user-files/simulations" \
  -v "$SCRIPT_DIR/data:/opt/gatling/user-files/resources" \
  -v "$SCRIPT_DIR/results:/opt/gatling/results" \
  denvazh/gatling:3.9.5 \
  -s "$SIMULATION_CLASS"

echo ""
echo "Results saved to: $SCRIPT_DIR/results"
