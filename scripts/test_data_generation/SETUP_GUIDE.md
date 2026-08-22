# YouTrack Test Data Generation Setup Guide

## Quick Start

### Prerequisites
- Docker and Docker Compose
- 30 minutes to 3 hours depending on performance (for 100k issues)
- 2+ CPU cores, 3+ GB RAM for YouTrack

### Step 1: Prepare Environment

```bash
# Copy example environment file
cp scripts/test_data_generation/.env.example scripts/test_data_generation/.env

# Edit .env and set your permanent token
# You'll need to complete YouTrack setup first and create a token
nano scripts/test_data_generation/.env
```

### Step 2: Start YouTrack

```bash
# Start YouTrack only (wait for health check to pass)
docker compose up -d youtrack

# Watch the startup logs
docker compose logs -f youtrack
```

### Step 3: Complete YouTrack Initial Setup

1. Open http://localhost:8080
2. Accept the trial license
3. Complete the setup wizard
4. Go to Admin → Your Profile
5. Account Security tab → Create new permanent token
6. Copy the token and add to `scripts/test_data_generation/.env`: `YOUTRACK_TOKEN=perm:...`

### Step 4: Generate Test Data

#### Option A: Docker Compose (Recommended)

```bash
# Load environment from .env
export $(cat scripts/test_data_generation/.env | grep -v '#' | xargs)

# Run data generation service
docker compose --profile data-generation up test-data-setup

# Watch logs in real-time
docker compose logs -f test-data-setup
```

#### Option B: Direct Python Execution

```bash
# Load environment
export $(cat scripts/test_data_generation/.env | grep -v '#' | xargs)

# Install dependencies
pip install -r scripts/test_data_generation/requirements.txt

# Run generator
python scripts/test_data_generation/generate_test_data.py
```

#### Option C: Bash Helper Script

```bash
# Load environment
export $(cat scripts/test_data_generation/.env | grep -v '#' | xargs)

# Make script executable
chmod +x scripts/test_data_generation/run_generator.sh

# Run
scripts/test_data_generation/run_generator.sh
```

### Step 5: Verify Test Data

1. Go to http://localhost:8080
2. Issues → Search All → Count should show ~100,000 issues
3. Admin → Users → Count should show ~100 users
4. Check that users are assigned to Demo project

### Step 6: Create Database Backup (Optional)

```bash
# Via Docker
docker exec youtrack curl -X POST \
  -H "Authorization: Bearer $YOUTRACK_TOKEN" \
  -H "Accept: application/json" \
  http://localhost:8080/youtrack/api/backup

# Or manually via UI:
# Admin → Maintenance → Create Backup
```

## Configuration Reference

### Performance Tuning

For **faster** generation (more load on server):
```bash
NUM_WORKERS=8              # More parallel workers
ISSUES_PER_BATCH=500       # Larger batches
BATCH_DELAY_SECONDS=0.1    # Minimal delay
```

For **slower** generation (less load on server):
```bash
NUM_WORKERS=2              # Fewer workers
ISSUES_PER_BATCH=50        # Smaller batches
BATCH_DELAY_SECONDS=2.0    # Longer delay
```

For **testing** (fast setup):
```bash
TOTAL_USERS=10
TOTAL_ISSUES=1000
NUM_WORKERS=4
```

## Understanding the Output

### Typical Execution Flow

```
YouTrack Test Data Generation Started
Target: 100 users, 100000 issues
YouTrack URL: http://youtrack:8080
Project: Demo
Workers: 4

============================================================
STEP 1: Creating users
============================================================
Loaded 20 user templates from CSV
Total users to create: 100
Batch 1: Created 10 users
Batch 2: Created 10 users
...
Batch 10: Created 10 users
Total users created: 100/100

============================================================
STEP 2: Setting up project team
============================================================
Added 100 users to project team

============================================================
STEP 3: Setting up group permissions
============================================================
Added 100 users to Registered Users group

============================================================
STEP 4: Creating test issues in parallel
============================================================
Starting to create 100000 issues with 4 workers
Progress: 5000/100000 issues, Rate: 500.0 issues/sec, ETA: 31.7 minutes
Progress: 10000/100000 issues, Rate: 510.2 issues/sec, ETA: 29.4 minutes
...
Progress: 100000/100000 issues
Issue creation completed in 185.3s. Created: 100000/100000 (540.0 issues/sec)

============================================================
TEST DATA GENERATION SUMMARY
============================================================
Users created: 100/100
Issues created: 100000/100000
Failed operations: 0

============================================================
STEP 5: Creating database backup
============================================================
Database backup initiated

YouTrack Test Data Generation Started
Test data generation completed successfully
```

## Troubleshooting

### "YOUTRACK_TOKEN is not set"
```bash
# Solution: Create token in YouTrack and set environment variable
export YOUTRACK_TOKEN="perm:xxx"
echo "YOUTRACK_TOKEN=$YOUTRACK_TOKEN" >> scripts/test_data_generation/.env
```

### "Failed to connect to YouTrack API"
```bash
# Check if YouTrack is running
docker compose ps youtrack

# Check health
curl http://localhost:8080/login

# View logs
docker compose logs youtrack
```

### "HTTP 401 Unauthorized"
```bash
# Token invalid or expired
# 1. Generate new token in YouTrack UI
# 2. Update YOUTRACK_TOKEN in scripts/test_data_generation/.env
# 3. Re-run script
```

### Generation is very slow
```bash
# Option 1: Check server resource usage
docker stats youtrack

# Option 2: Reduce parallelism
export NUM_WORKERS=2
export BATCH_DELAY_SECONDS=1.0

# Option 3: Check server logs
docker compose logs youtrack | tail -100
```

### Generation stops/hangs
```bash
# Option 1: Increase timeout
export TIMEOUT_SECONDS=60

# Option 2: Reduce batch size
export ISSUES_PER_BATCH=50

# Option 3: Kill container and restart
docker compose restart test-data-setup
```

## Monitoring Progress

### In Real-Time

```bash
# Watch generation logs
docker compose logs -f test-data-setup

# Alternative: tail the log file
tail -f scripts/test_data_generation/logs/test_data_generation.log
```

### Via YouTrack UI

```bash
# Monitor issue count growth
Open http://localhost:8080
Issues → View All → Check issue count
```

### Via Docker

```bash
# Check container status
docker compose ps

# Check resource usage
docker stats

# Get exit code
docker compose ps test-data-setup
```

## Typical Performance Metrics

With default settings (4 workers, 100 issues/batch):

| Metric | Time |
|--------|------|
| User creation (100 users) | 5 min |
| Project team setup (100 users) | 2 min |
| Issue creation (100k issues) | 180-200 min |
| **Total** | **187-207 min** |

**Throughput**: 500-1000 issues/sec depending on resources

## File Organization

```
jb-try-2/
├── docker-compose.yml               # Container orchestration
├── scripts/
│   └── test_data_generation/
│       ├── generate_test_data.py    # Main script
│       ├── config.py                # Configuration module
│       ├── youtrack_api.py          # REST API client
│       ├── backup_utils.py          # Backup utilities
│       ├── run_generator.sh         # Bash helper
│       ├── requirements.txt         # Python dependencies
│       ├── README.md                # Detailed documentation
│       ├── .env.example             # Example config
│       ├── logs/                    # Generated logs
│       ├── backups/                 # Generated backups
│       └── sample_data/
│           ├── users.csv            # User templates
│           └── issues.csv           # Issue templates
├── perf_test_scripts/
│   └── run.sh                       # Load testing script
└── youtrack/
    ├── data/                    # YouTrack data volume
    ├── conf/                    # Configuration
    ├── logs/                    # Application logs
    └── backups/                 # Database backups
```

## Next Steps

After test data is generated:

1. **Verify data integrity**
   - Check issue count matches target
   - Spot-check random issues for data quality

2. **Create baseline backup**
   ```bash
   # Keep a clean backup for test reruns
   docker cp youtrack:/opt/youtrack/backups ./backups/
   ```

3. **Run performance tests**
   ```bash
   # Using Gatling (if available)
   cd gatling
   ./run-gatling.sh
   ```

4. **Analyze results**
   - Review test reports
   - Compare against SLOs
   - Identify bottlenecks

## Additional Resources

- [YouTrack REST API Documentation](https://www.jetbrains.com/help/youtrack/devportal/youtrack-rest-api.html)
- [Permanent Token Authorization](https://www.jetbrains.com/help/youtrack/devportal/authentication-with-permanent-token.html)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [YouTrack Installation Guide](https://www.jetbrains.com/help/youtrack/server/youtrack-docker-installation.html)

## Getting Help

If you encounter issues:

1. Check logs: `tail -f scripts/test_data_generation/logs/test_data_generation.log`
2. Review troubleshooting section above
3. Check YouTrack server logs: `docker compose logs youtrack`
4. Verify environment variables: `echo $YOUTRACK_TOKEN`
5. Test API connectivity: `curl http://localhost:8080/youtrack/api/issues`

## Support

For issues related to:
- **Test data generation**: See `scripts/test_data_generation/README.md`
- **YouTrack API**: See YouTrack documentation
- **Docker Compose**: See Docker documentation
