#!/usr/bin/env python3
"""
Daily Runner - Automated Forecast Generation System
====================================================
This script orchestrates the daily prediction workflow:
1. Scrape today's race program from TJK
2. Refresh galop (training) data
3. Generate predictions for all Turkish cities
4. Sync results to Supabase

Run manually: python3 daily_runner.py
Scheduled:    Cron at 08:00 AM daily
"""

import subprocess
import sys
import os
import logging
from datetime import datetime
from pathlib import Path

# Setup
PROJECT_DIR = Path(__file__).parent.absolute()
LOG_DIR = PROJECT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Configure logging
log_file = LOG_DIR / f"daily_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_command(cmd: list, description: str) -> bool:
    """Execute a command and log output."""
    logger.info(f"🚀 Starting: {description}")
    logger.info(f"   Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        if result.stdout:
            for line in result.stdout.strip().split('\n')[-20:]:  # Last 20 lines
                logger.info(f"   {line}")
        
        if result.returncode == 0:
            logger.info(f"✅ Completed: {description}")
            return True
        else:
            logger.error(f"❌ Failed: {description}")
            if result.stderr:
                logger.error(f"   Error: {result.stderr[:500]}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"⏰ Timeout: {description}")
        return False
    except Exception as e:
        logger.error(f"💥 Exception in {description}: {e}")
        return False


def step_1_scrape_program():
    """Scrape today's race program."""
    today = datetime.now().strftime("%d/%m/%Y")
    return run_command(
        ["python3", "tjk_scraper/scrape.py", "--start_date", today],
        f"Scrape race program for {today}"
    )


def step_2_refresh_galops():
    """Refresh galop training data."""
    return run_command(
        ["python3", "refresh_gallops.py"],
        "Refresh galop data"
    )


def step_3_generate_forecasts():
    """Generate predictions for all cities."""
    return run_command(
        ["python3", "push_forecasts_v10.py", "--all-cities"],
        "Generate forecasts for all TR cities"
    )


def step_4_sync_supabase():
    """Push forecasts to Supabase."""
    return run_command(
        ["python3", "supabase_sync.py"],
        "Sync forecasts to Supabase"
    )


def main():
    """Main orchestration flow."""
    start_time = datetime.now()
    logger.info("="*60)
    logger.info("🏇 DAILY RUNNER - Starting Automated Forecast Generation")
    logger.info(f"   Date: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*60)
    
    steps = [
        ("Program Scrape", step_1_scrape_program),
        ("Galop Refresh", step_2_refresh_galops),
        ("Forecast Generation", step_3_generate_forecasts),
        ("Supabase Sync", step_4_sync_supabase),
    ]
    
    results = {}
    all_success = True
    
    for name, func in steps:
        success = func()
        results[name] = "✅" if success else "❌"
        if not success:
            all_success = False
            # Continue anyway to try other steps
    
    # Summary
    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info("")
    logger.info("="*60)
    logger.info("📊 DAILY RUNNER - Summary")
    logger.info("="*60)
    for name, status in results.items():
        logger.info(f"   {status} {name}")
    logger.info(f"   ⏱️  Total Time: {elapsed:.1f} seconds")
    logger.info("="*60)
    
    if all_success:
        logger.info("🎉 All steps completed successfully!")
    else:
        logger.warning("⚠️ Some steps failed. Check logs above.")
    
    return 0 if all_success else 1


if __name__ == "__main__":
    sys.exit(main())
