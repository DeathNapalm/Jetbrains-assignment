"""
Configuration module for YouTrack test data generation.
"""
import os
from pathlib import Path

# YouTrack API Configuration
YOUTRACK_URL = os.getenv("YOUTRACK_URL", "http://youtrack:8080")
YOUTRACK_TOKEN = os.getenv("YOUTRACK_TOKEN", "")
YOUTRACK_PROJECT_KEY = "Demo"

# Test Data Configuration
TOTAL_USERS = int(os.getenv("TOTAL_USERS", "100"))
TOTAL_ISSUES = int(os.getenv("TOTAL_ISSUES", "100000"))
ISSUES_PER_BATCH = int(os.getenv("ISSUES_PER_BATCH", "100"))
BATCH_DELAY_SECONDS = float(os.getenv("BATCH_DELAY_SECONDS", "0.5"))

# Parallel Processing Configuration
NUM_WORKERS = int(os.getenv("NUM_WORKERS", "4"))
QUEUE_SIZE = int(os.getenv("QUEUE_SIZE", "100"))
TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", "30"))

# File Paths
SCRIPTS_DIR = Path(__file__).parent
DATA_DIR = SCRIPTS_DIR / "sample_data"
USERS_CSV = DATA_DIR / "users.csv"
ISSUES_CSV = DATA_DIR / "issues.csv"
LOGS_DIR = SCRIPTS_DIR / "logs"
BACKUP_DIR = SCRIPTS_DIR / "backups"

# Create necessary directories
LOGS_DIR.mkdir(exist_ok=True)
BACKUP_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = LOGS_DIR / "test_data_generation.log"

# HTTP Configuration
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

# Issue Generation Configuration
ISSUE_SUMMARIES = [
    "Fix login validation error",
    "Add user profile page",
    "Improve search performance",
    "Update documentation",
    "Refactor authentication module",
    "Add API endpoint for reports",
    "Fix database connection pool",
    "Implement caching layer",
    "Add export to PDF feature",
    "Optimize query performance",
]

ISSUE_DESCRIPTIONS = [
    "Users report {} issue when accessing the system.",
    "We need to implement {} feature for better user experience.",
    "Performance testing shows {} is needed.",
    "Documentation needs update on {}.",
    "Code refactoring required for {}.",
    "New functionality requested: {}.",
    "Bug found in {} module.",
    "Enhancement suggested for {}.",
    "Configuration issue with {}.",
    "Integration test needed for {}.",
]

# Group Configuration
ADMIN_GROUP = "Registered Users"
DEFAULT_PERMISSIONS = ["CAN_VIEW_ISSUE", "CAN_CREATE_ISSUE", "CAN_LINK_ISSUE"]

# Database Backup Configuration
CREATE_BACKUP_AFTER = True
BACKUP_NAME_PREFIX = "youtrack_testdata_backup"
