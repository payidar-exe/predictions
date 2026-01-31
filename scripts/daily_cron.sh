#!/bin/bash
# Daily Cron Script for Altılı Zeka Predictions
# =============================================
# This script runs the daily prediction workflow.
#
# Setup:
# 1. Make executable: chmod +x scripts/daily_cron.sh
# 2. Add to crontab: crontab -e
# 3. Add line: 0 8 * * * /path/to/scripts/daily_cron.sh
#
# Or use macOS launchd for more reliability.

# Configuration
PROJECT_DIR="/Users/cemalpaytas/Documents/Github Projects/predictions"
LOG_DIR="${PROJECT_DIR}/logs"
PYTHON="/usr/bin/python3"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Timestamp for log
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="${LOG_DIR}/cron_${TIMESTAMP}.log"

# Run the daily runner
cd "$PROJECT_DIR"
echo "========================================" >> "$LOG_FILE"
echo "Daily Cron Started: $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

$PYTHON daily_runner.py >> "$LOG_FILE" 2>&1
EXIT_CODE=$?

echo "" >> "$LOG_FILE"
echo "Exit Code: $EXIT_CODE" >> "$LOG_FILE"
echo "Finished: $(date)" >> "$LOG_FILE"

# Optional: Send notification on failure
if [ $EXIT_CODE -ne 0 ]; then
    # macOS notification (adjust as needed)
    osascript -e 'display notification "Daily predictions failed! Check logs." with title "Altılı Zeka"' 2>/dev/null
fi

exit $EXIT_CODE
