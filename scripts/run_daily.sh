#!/bin/bash
# run_daily.sh - Cron wrapper for daily automation
# 
# Crontab setup:
#   0 10 * * * /path/to/predictions/scripts/run_daily.sh publish >> /path/to/logs/publish.log 2>&1
#   0 22 * * * /path/to/predictions/scripts/run_daily.sh results >> /path/to/logs/results.log 2>&1

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Activate virtual environment if exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | xargs)
fi

case "$1" in
    publish)
        echo "🌅 Running daily publish..."
        python3 scripts/daily_publish.py
        ;;
    results)
        echo "🌙 Running daily results..."
        python3 scripts/daily_results.py
        ;;
    *)
        echo "Usage: $0 {publish|results}"
        exit 1
        ;;
esac
