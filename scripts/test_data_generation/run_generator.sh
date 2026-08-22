#!/bin/bash
# Helper script to run YouTrack test data generation with proper environment

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}YouTrack Test Data Generator${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

# Check if token is provided
if [ -z "$YOUTRACK_TOKEN" ]; then
    echo -e "${RED}Error: YOUTRACK_TOKEN environment variable not set${NC}"
    echo ""
    echo "To generate a token:"
    echo "  1. Go to YouTrack Admin UI"
    echo "  2. Your Profile → Account Security"
    echo "  3. Create new permanent token"
    echo "  4. Run: export YOUTRACK_TOKEN='perm:<your-token>'"
    echo ""
    exit 1
fi

# Set defaults if not provided
YOUTRACK_URL="${YOUTRACK_URL:-http://youtrack:8080}"
TOTAL_USERS="${TOTAL_USERS:-100}"
TOTAL_ISSUES="${TOTAL_ISSUES:-100000}"
NUM_WORKERS="${NUM_WORKERS:-4}"
LOG_LEVEL="${LOG_LEVEL:-INFO}"

# Display configuration
echo -e "${YELLOW}Configuration:${NC}"
echo "  YouTrack URL: $YOUTRACK_URL"
echo "  Total Users: $TOTAL_USERS"
echo "  Total Issues: $TOTAL_ISSUES"
echo "  Workers: $NUM_WORKERS"
echo "  Log Level: $LOG_LEVEL"
echo ""

# Export for Python script
export YOUTRACK_URL
export YOUTRACK_TOKEN
export TOTAL_USERS
export TOTAL_ISSUES
export NUM_WORKERS
export LOG_LEVEL

# Check Python availability
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 not found${NC}"
    exit 1
fi

# Check if requirements are installed
echo -e "${YELLOW}Checking dependencies...${NC}"
if ! python3 -c "import requests" 2>/dev/null; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip3 install -q -r "$SCRIPT_DIR/requirements.txt"
    echo -e "${GREEN}Dependencies installed${NC}"
fi

echo ""
echo -e "${GREEN}Starting test data generation...${NC}"
echo ""

# Run the main script
cd "$SCRIPT_DIR"
python3 generate_test_data.py

exit_code=$?

echo ""
if [ $exit_code -eq 0 ]; then
    echo -e "${GREEN}Test data generation completed successfully!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Verify data in YouTrack UI"
    echo "  2. Create database backup if not auto-created"
    echo "  3. Run performance tests"
else
    echo -e "${RED}Test data generation failed (exit code: $exit_code)${NC}"
fi

exit $exit_code
