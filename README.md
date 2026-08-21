Jetbrains 
# Performance testing methodology
[docs/performance-testing-methodology.md](docs/performance-testing-methodology.md)

# Performance testing result
[docs/report.md](docs/report.md)

# How to deploy service 

## YouTrack Service Deployment

### Start YouTrack Container
```bash
# Start YouTrack service only (wait for health check to pass)
docker compose up -d youtrack

# Watch startup logs
docker compose logs -f youtrack
```

YouTrack will be available at `http://localhost:8080` with JMX metrics on port `9090`.

### Initial Setup
1. Open http://localhost:8080 in your browser
2. Accept the trial license and complete the setup wizard
3. Create a permanent API token:
   - Go to Admin → Your Profile → Account Security
   - Click "Create new permanent token"
   - Copy the token (format: `perm:...`)

### Generate Test Data (Optional)
```bash
# Configure environment with your YouTrack token
export $(cat scripts/.env | grep -v '#' | xargs)

# Run test data generation
docker compose --profile data-generation up test-data-setup

# Or use the helper script
chmod +x scripts/run_generator.sh
scripts/run_generator.sh
```

This will generate ~100,000 test issues and ~100 users in your YouTrack instance.

### Stop Service
```bash
docker compose down

# To also remove volumes (data)
docker compose down -v
```

# How to deploy monitoring stack

## Monitoring Stack Deployment (Prometheus + Grafana + cAdvisor)

The monitoring stack provides real-time performance metrics visualization for YouTrack and the load testing environment.

### Start Monitoring Stack
```bash
# Start monitoring services from project root
docker compose -f monitoring/docker-compose-monitoring.yml up -d

# Verify all services are running
docker compose -f monitoring/docker-compose-monitoring.yml ps
```

### Access Dashboards
- **Grafana**: http://localhost:3000 (login: admin / admin)
- **Prometheus**: http://localhost:9091
- **cAdvisor**: http://localhost:8081
- **JMX Exporter**: http://localhost:5556/metrics

### Available Dashboards
- **YouTrack Resource Monitoring**: Overall CPU, memory, and disk usage
- **YouTrack JMX Monitoring**: Java heap, GC metrics, thread counts

### Stop Monitoring Stack
```bash
docker compose -f monitoring/docker-compose-monitoring.yml down

# To also remove monitoring data
docker compose -f monitoring/docker-compose-monitoring.yml down -v
```

### Full Stack Setup
To run both YouTrack and monitoring together:
```bash
# Start both stacks
docker compose up -d youtrack
docker compose -f monitoring/docker-compose-monitoring.yml up -d

# View all containers
docker compose ps
docker compose -f monitoring/docker-compose-monitoring.yml ps
``` 

# How to run tests 
```bash
# renew the token 
YOUTRACK_TOKEN=<token>
# Run all three workload groups together in parallel for 10 minutes.
# UC01: create/update mix, 30% create / 70% update, 1000 rpm.
PERF_USERS=3 PERF_CREATE_RATIO=30 PERF_DURATION=600 \
  SIMULATION_CLASS=youtrack.UC01_createOrUpdate ./perf_test_scripts/run.sh &
UC01_PID=$!

# UC02: search workload, 1000 rpm.
PERF_USERS=3 PERF_DURATION=600 \
  SIMULATION_CLASS=youtrack.UC02_performSearches ./perf_test_scripts/run.sh &
UC02_PID=$!

# UC03: random issue view workload, 3000 rpm.
PERF_USERS=2 PERF_DURATION=600 \
  SIMULATION_CLASS=youtrack.UC03_viewIssue ./perf_test_scripts/run.sh &
UC03_PID=$!

# Wait for all three jobs to finish before exiting.
wait "$UC01_PID" "$UC02_PID" "$UC03_PID"

# Notes:
# - PERF_CREATE_RATIO is a percentage value, so 30 means 30% create and 70% update.
# - The user counts above match the workload table for the three scenario groups.
# - If you want a longer run, increase PERF_DURATION, for example to 3600 for a 60-minute scenario.
```