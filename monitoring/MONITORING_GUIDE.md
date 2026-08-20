# YouTrack Resource Monitoring Under Load

This guide explains how to monitor YouTrack container resource consumption (CPU, memory, network, disk I/O) during load testing with time-series graphs.

## Quick Start

### 1. Start Monitoring Stack with YouTrack

```bash
# Start YouTrack and all monitoring services
docker-compose -f docker-compose.yml -f monitoring/docker-compose-monitoring.yml up -d
```

This starts:
- **YouTrack** (port 8080) - Your issue tracking system
- **Prometheus** (port 9090) - Time-series metrics database
- **cAdvisor** (port 8081) - Docker container metrics collector
- **JMX Exporter** (port 5556) - JVM/JMX to Prometheus bridge for YouTrack
- **Grafana** (port 3000) - Visual dashboard with graphs

### 2. Access the Dashboards

| Service | URL | Login |
|---------|-----|-------|
| YouTrack | http://localhost:8080 | (Your setup credentials) |
| Prometheus | http://localhost:9090 | (No login) |
| Grafana | http://localhost:3000 | admin / admin |
| cAdvisor | http://localhost:8081 | (No login) |
| JMX Exporter | http://localhost:5556/metrics | (No login) |

### 3. View Resource Graphs in Grafana

1. Open http://localhost:3000
2. Login with `admin` / `admin`
3. Go to **Dashboards** → **YouTrack Resource Consumption Under Load**
4. The dashboard shows:
   - **CPU Usage**: % of available CPU cores over time
   - **Memory Usage**: RAM consumption in bytes
   - **Network I/O**: Network traffic (RX/TX) rate
   - **Disk I/O**: Disk operations rate

## Running Load Tests

### Option 1: Using Gatling (Recommended)

1. **Start monitoring stack** (see Quick Start above)
2. **Generate test data** (if needed):
   ```bash
   docker compose --profile data-generation up test-data-setup
   ```
3. **Run Gatling load test**:
   ```bash
   # Update gatling/run-gatling.sh with your simulation
   ./gatling/run-gatling.sh
   ```
4. **Monitor in real-time** at http://localhost:3000

### Option 2: Using Python Test Script

```bash
# While monitoring dashboard is open
python scripts/generate_test_data.py --num-concurrent-requests 100
```

### Option 3: Using curl for Simple Load Testing

```bash
# Generate continuous GET requests (30 seconds)
for i in {1..100}; do
  curl -s http://localhost:8080/api/issues?max=100 &
done
wait
```

## Metrics Explained

### CPU Usage
- **Metric**: `rate(container_cpu_usage_seconds_total[30s])`
- **Unit**: Percentage (0-1.0)
- **Interpretation**: 1.0 = using 100% of 1 CPU core
- **Guideline**: Should stay below 80% for safe operation

### Memory Usage
- **Metric**: `container_memory_usage_bytes`
- **Unit**: Bytes (shown as MB/GB)
- **Interpretation**: Total RAM used by container
- **Guideline**: Monitor for memory leaks (continuously rising)

### Network I/O
- **Metric**: `rate(container_network_receive_bytes_total[30s])` and `transmit`
- **Unit**: Bytes per second
- **Interpretation**: Data flowing in/out of container
- **Guideline**: RX/TX ratio indicates request size vs response size

### Disk I/O
- **Metric**: `rate(container_fs_io_current[30s])`
- **Unit**: Operations per second
- **Interpretation**: Storage system activity
- **Guideline**: Watch for sustained high I/O (> 1000 ops/sec)

## Advanced: Custom Queries

### In Prometheus (http://localhost:9090)

1. Go to **Graph** tab
2. Enter query like:
   ```
   # Average CPU over last 5 minutes
   avg_over_time(rate(container_cpu_usage_seconds_total{container_label_com_docker_compose_service="youtrack"}[30s])[5m:30s])
   
   # 95th percentile memory usage
   histogram_quantile(0.95, container_memory_usage_bytes{container_label_com_docker_compose_service="youtrack"})
   
   # Network latency (if JMeter metrics available)
   rate(container_network_receive_errors_total{container_label_com_docker_compose_service="youtrack"}[5m])
   ```

### In Grafana (http://localhost:3000)

1. Edit dashboard → Add Panel → Prometheus
2. Use queries like above
3. Customize visualization (graph, gauge, table, etc.)

## Troubleshooting

### Prometheus not collecting metrics

```bash
# Check if Prometheus is scraping targets
curl http://localhost:9090/api/v1/targets

# Check prometheus config
curl http://localhost:9090/api/v1/status/config

# Verify JMX target is up
curl "http://localhost:9090/api/v1/query?query=up%7Bjob%3D%22youtrack-jmx%22%7D"
```

### cAdvisor not showing data

```bash
# Ensure cAdvisor can access Docker socket
docker-compose logs cadvisor

# Should see "Manager started"
```

### Grafana dashboard blank

1. Check data source in Grafana: **Configuration** → **Data Sources** → **Prometheus**
2. Click **Test** to verify connection
3. Try manual query: `up{job="cadvisor"}` should show `1`

## Persistence

- **Prometheus data**: Stored in `prometheus-data/` volume (30 days retention)
- **Grafana dashboards**: Stored in `grafana-data/` volume
- **Backups**: Export dashboard JSON from Grafana UI

To keep data after container restart:
```bash
docker-compose -f docker-compose.yml -f monitoring/docker-compose-monitoring.yml down
# Data persists in volumes
docker-compose -f docker-compose.yml -f monitoring/docker-compose-monitoring.yml up -d
```

To clear data:
```bash
docker-compose -f docker-compose.yml -f monitoring/docker-compose-monitoring.yml down -v
```

## Integration with Load Testing Tools

### With Gatling
Gatling outputs metrics that can be pushed to Prometheus. Update your Gatling simulation:
```scala
// In your Gatling simulation
import io.gatling.metrics.prometheus.PrometheusMetricsCollector

new PrometheusMetricsCollector(configuration)
```

### With JMeter
Use JMeter Prometheus plugin to export metrics:
- Install: JMeter Plugins Manager → Prometheus Backend Listener
- Configure: Add Prometheus Backend Listener → `http://prometheus:9091/metrics`

### With Apache Bench
For simple load tests:
```bash
ab -n 10000 -c 100 -g results.tsv http://localhost:8080/
```
Monitor metrics in Grafana dashboard simultaneously.

## Example: Complete Load Test Workflow

```bash
# Terminal 1: Start monitoring
docker-compose -f docker-compose.yml -f monitoring/docker-compose-monitoring.yml up -d

# Terminal 2: Open Grafana in browser
# Visit http://localhost:3000
# Open YouTrack Resource Consumption dashboard

# Terminal 3: Run load test
for i in {1..1000}; do
  curl -s http://localhost:8080/api/issues?max=50 > /dev/null &
  if (( i % 50 == 0 )); then
    echo "Sent $i requests"
    sleep 1
  fi
done
wait
echo "Load test complete"

# Keep monitoring for 5 minutes to see cool-down
sleep 300

# Stop services
docker-compose -f docker-compose.yml -f monitoring/docker-compose-monitoring.yml down

# Data persists in volumes for later analysis
```

## Performance Benchmarks

Expected resource usage for YouTrack under various loads:

| Load Level | CPU | Memory | Network RX/TX |
|-----------|-----|--------|---------------|
| Idle (no users) | <5% | 300-500MB | <100 KB/s |
| Light (10 concurrent) | 10-20% | 400-600MB | 1-5 MB/s |
| Medium (50 concurrent) | 30-50% | 600-1000MB | 5-20 MB/s |
| Heavy (100+ concurrent) | 60-80% | 1000-1500MB | 20-50 MB/s |
| Overloaded (200+ concurrent) | 90%+ | 1500MB+ | 50-100+ MB/s |

These vary based on YouTrack configuration, dataset size, and query complexity.

## Next Steps

1. **Baseline**: Run light load test and note metrics for comparison
2. **Stress Test**: Gradually increase load to find breaking point
3. **Optimize**: Identify bottlenecks (CPU? Memory? I/O?)
4. **Scale**: Increase container resources or add clustering based on findings
5. **Document**: Save Grafana dashboards and test results

For more details on YouTrack performance tuning, see [YouTrack Admin Guide](https://www.jetbrains.com/help/youtrack/server/Configuring-YouTrack.html).
