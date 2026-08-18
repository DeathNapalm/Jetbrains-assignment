# YouTrack Test Data Generation

This directory contains scripts and utilities for generating test data for YouTrack performance testing.

## Overview

The test data generation system creates:
- **100 users** with unique login credentials
- **100,000 issues** distributed across the Demo project
- **Project team setup** with all users added to the Demo project
- **Group permissions** to support collaborative access
- **Database backup** after data generation completes

## Architecture

### Components

1. **`config.py`** - Central configuration module
   - YouTrack API credentials and URL
   - Test data targets (users, issues)
   - Parallelization settings
   - File paths and logging configuration

2. **`youtrack_api.py`** - REST API client
   - Authentication with permanent tokens
   - User management operations
   - Project team management
   - Issue CRUD operations
   - Database backup operations
   - Automatic retry with exponential backoff

3. **`generate_test_data.py`** - Main generation script
   - Parallel issue creation with thread pool
   - CSV-based data templates
   - Progress tracking and logging
   - Error handling and recovery
   - Batch processing with configurable delays

4. **`sample_data/users.csv`** - User data templates
   - 10 sample users (expanded to 100 via script)
   - Format: id, login, name, email

5. **`sample_data/issues.csv`** - Issue data templates
   - 5 issue templates with summary and description patterns
   - Used to generate variety in 100,000 issues

## Prerequisites

- Python 3.8+
- YouTrack 2026.1.13456 or later
- Permanent token with `YouTrack` and `YouTrack Administration` scopes
- Network access to YouTrack API

## Installation

```bash
# Install dependencies
pip install -r scripts/requirements.txt
```

## Configuration

Set environment variables before running:

```bash
# Required
export YOUTRACK_URL="http://youtrack:8080"
export YOUTRACK_TOKEN="<your-permanent-token>"

# Optional (defaults shown)
export TOTAL_USERS="100"
export TOTAL_ISSUES="100000"
export NUM_WORKERS="4"
export ISSUES_PER_BATCH="100"
export BATCH_DELAY_SECONDS="0.5"
export LOG_LEVEL="INFO"
```

## Usage

### Basic Setup (Docker Container)

If using Docker Compose:

```bash
# Build the services
docker compose build

# Start YouTrack
docker compose up -d youtrack

# Wait for YouTrack to be ready (health check passes)
docker compose ps

# Get the wizard token
docker exec youtrack cat /opt/youtrack/conf/internal/services/configurationWizard/wizard_token.txt

# Complete setup via web UI (http://localhost:8080)
# 1. Accept trial license
# 2. Complete initial setup
# 3. Create a permanent token in Admin settings

# Run test data generation
docker compose run --rm test-data-setup
```

### Manual Execution

```bash
# Navigate to scripts directory
cd scripts

# Ensure config is set via environment variables
export YOUTRACK_URL="http://localhost:8080"
export YOUTRACK_TOKEN="perm:<your-token>"

# Run the generation script
python generate_test_data.py
```

## How It Works

### Phase 1: User Creation
- Loads 10 user templates from `sample_data/users.csv`
- Generates additional users to reach 100 total
- Creates users via REST API in batches of 10

### Phase 2: Project Team Setup
- Adds all 100 users to the Demo project team
- Each user gets default project permissions
- Enables collaborative issue creation

### Phase 3: Group Permissions
- Adds users to "Registered Users" group
- Configures group-level view/modify permissions
- Supports multi-user access patterns

### Phase 4: Issue Generation (Parallel)
- Generates 100,000 issues with variety:
  - Randomized summaries from 10 templates
  - Descriptions with issue number and context
  - Random reporter (30% assigned to random user)
  - Random assignee (30% chance)
- Uses thread pool with configurable workers
- Batches requests to avoid overwhelming API
- Tracks progress and ETA in logs

### Phase 5: Database Backup
- Triggers automatic backup after data generation
- Backup can be restored before performance tests

## Performance Characteristics

### Expected Performance

With default settings (4 workers, 100 issues/batch):
- **User creation**: ~50 users/min (5 min for 100 users)
- **Issue creation**: ~500-1000 issues/min (100-200 min for 100,000 issues)
- **Total time**: 2-3 hours for full dataset

### Optimization Tips

**Increase throughput:**
```bash
# More parallel workers (if system can handle it)
export NUM_WORKERS="8"

# Larger batch size (less overhead, bigger spikes)
export ISSUES_PER_BATCH="500"

# Reduce batch delay (faster but more load on server)
export BATCH_DELAY_SECONDS="0.1"
```

**Reduce server load:**
```bash
# Fewer workers
export NUM_WORKERS="2"

# Smaller batches
export ISSUES_PER_BATCH="50"

# Longer delay between batches
export BATCH_DELAY_SECONDS="2.0"
```

## Logging

Logs are written to:
- **Console**: Real-time progress and status
- **File**: `scripts/logs/test_data_generation.log`

Log levels:
- `DEBUG`: Detailed per-item operations
- `INFO`: Phase summaries and progress
- `WARNING`: Recoverable issues (failed user, partial batch)
- `ERROR`: Fatal errors that stop execution

## CSV File Format

### users.csv
```csv
id,login,name,email
1,user001,Alice Johnson,alice.johnson@example.com
2,user002,Bob Smith,bob.smith@example.com
```

Template users are used as examples. Script auto-generates additional users to reach `TOTAL_USERS`.

### issues.csv
```csv
id,summary,description
1,Bug report template,Description for bug: [TEMPLATE]
2,Feature request template,Description for feature: [TEMPLATE]
```

Templates are used cyclically. Script generates variety via:
- Random selection from predefined summaries
- Dynamic descriptions with issue numbers
- Random user assignment

## Error Handling

- **Connection failures**: Automatic retry with exponential backoff (up to 3 attempts)
- **Partial failures**: Logged but doesn't stop generation
- **API errors**: Detailed error messages in logs
- **Timeout**: Configurable per operation (default 30s)

Failed operations are tracked and reported in summary:
```
Failed operations:
  - User creation: user050
  - Issue creation: connection timeout
  ... and 5 more
```

## Troubleshooting

### "YOUTRACK_TOKEN not set"
- Generate permanent token in YouTrack Admin UI
- Set environment variable: `export YOUTRACK_TOKEN="perm:..."`

### "Failed to connect to YouTrack API"
- Verify YouTrack is running: `curl http://youtrack:8080/login`
- Check network connectivity
- Confirm YOUTRACK_URL is correct

### "HTTP 401 Unauthorized"
- Token expired or invalid
- Generate new token in YouTrack
- Token may not have required scopes (`YouTrack` + `YouTrack Administration`)

### Slow issue creation
- Reduce `NUM_WORKERS` if server is overwhelmed
- Increase `BATCH_DELAY_SECONDS`
- Check YouTrack server resources (CPU, memory, disk)
- Review server logs for database issues

### "No module named config" or "No module named youtrack_api"
- Run from `scripts/` directory: `cd scripts && python generate_test_data.py`
- Or add to PYTHONPATH: `export PYTHONPATH="${PYTHONPATH}:/path/to/scripts"`

## Testing Locally

Generate smaller dataset for testing:
```bash
export TOTAL_USERS="10"
export TOTAL_ISSUES="1000"
python generate_test_data.py
```

## Integration with Performance Testing

After test data is generated:

1. **Backup the database** (automatic or manual):
   ```bash
   # Via YouTrack Admin UI: Admin → Backup
   ```

2. **Run performance tests** (e.g., Gatling):
   ```bash
   cd ../gatling
   ./run-gatling.sh
   ```

3. **Restore backup** before next test run:
   ```bash
   # Via YouTrack Admin UI: Admin → Restore
   ```

## File Structure

```
scripts/
├── generate_test_data.py      # Main generation script
├── config.py                   # Configuration module
├── youtrack_api.py            # REST API client
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── logs/                      # Log files (created)
│   └── test_data_generation.log
├── backups/                   # Backup files (created)
│   └── *.backup
└── sample_data/               # CSV templates
    ├── users.csv
    └── issues.csv
```

## Related Documentation

- [YouTrack REST API](https://www.jetbrains.com/help/youtrack/devportal/youtrack-rest-api.html)
- [Permanent Token Authorization](https://www.jetbrains.com/help/youtrack/devportal/authentication-with-permanent-token.html)
- [Database Backup](https://www.jetbrains.com/help/youtrack/server/back-up-the-database.html)
- [Docker Installation](https://www.jetbrains.com/help/youtrack/server/youtrack-docker-installation.html)
