import os
import logging
import asyncio
import json
from datetime import datetime, timedelta
import pytz
from celery import shared_task

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='tasks_horoscope.log'
)
logger = logging.getLogger(__name__)

# Baghdad timezone
baghdad_tz = pytz.timezone('Asia/Baghdad')

# Import all necessary functions from your existing script
from horoscope_scraper_publisher import (
    run_scrape_with_retry,
    main_scrape_and_publish,
    run_manual_scrape
)

# Data directory for status tracking
STATUS_DIR = 'data'
if not os.path.exists(STATUS_DIR):
    os.makedirs(STATUS_DIR)

def get_last_successful_date():
    """Get the date of the last successful scrape from status file"""
    status_file = os.path.join(STATUS_DIR, 'last_successful_scrape.txt')
    try:
        with open(status_file, 'r') as f:
            date_str = f.read().strip()
            return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (FileNotFoundError, ValueError):
        return None

def save_successful_date(date):
    """Save the date of a successful scrape to status file"""
    status_file = os.path.join(STATUS_DIR, 'last_successful_scrape.txt')
    with open(status_file, 'w') as f:
        f.write(date.strftime('%Y-%m-%d'))
    logger.info(f"Saved successful scrape date: {date}")

@shared_task
def scrape_horoscopes(attempt_number=1, hours_between_retries=1):
    """
    Task to scrape horoscopes and publish them to WordPress
    
    Args:
        attempt_number: The current attempt number (1, 2, or 3)
        hours_between_retries: Hours to wait between retry attempts
    """
    # Get current date in Baghdad timezone
    now = datetime.now(baghdad_tz)
    current_date = now.date()
    
    # Check if we already have successful data for today
    last_successful_date = get_last_successful_date()
    if last_successful_date == current_date:
        logger.info(f"Already have horoscope data for today ({current_date}). Skipping attempt {attempt_number}.")
        return True
    
    logger.info(f"Starting horoscope scrape attempt #{attempt_number} for {current_date}")
    
    # Set number of retries based on which attempt this is
    if attempt_number == 1:
        num_retries = 2  # First attempt - fewer retries
    elif attempt_number == 2:
        num_retries = 3  # Second attempt - moderate retries
    else:
        num_retries = 4  # Third attempt - more aggressive retries
    
    # Run the scraping process using your existing code
    try:
        success = asyncio.run(run_scrape_with_retry(num_retries=num_retries, hours_between=hours_between_retries))
        
        if success:
            logger.info(f"Horoscope scrape attempt #{attempt_number} was successful for {current_date}")
            save_successful_date(current_date)
            return True
        else:
            logger.warning(f"Horoscope scrape attempt #{attempt_number} failed for {current_date}")
            return False
    except Exception as e:
        logger.error(f"Error in scrape_horoscopes task: {str(e)}", exc_info=True)
        return False

@shared_task
def first_scrape():
    """First scheduled attempt to scrape horoscopes (early morning)"""
    logger.info("Running first scheduled horoscope scrape")
    return scrape_horoscopes(attempt_number=1, hours_between_retries=1)

@shared_task
def second_scrape():
    """Second scheduled attempt to scrape horoscopes if first attempt failed (mid-morning)"""
    # Get current date in Baghdad timezone
    now = datetime.now(baghdad_tz)
    current_date = now.date()
    
    # Check if we already have successful data for today
    last_successful_date = get_last_successful_date()
    if last_successful_date == current_date:
        logger.info(f"Already have horoscope data for today ({current_date}). Skipping second attempt.")
        return True
    
    logger.info("Running second scheduled horoscope scrape")
    return scrape_horoscopes(attempt_number=2, hours_between_retries=0.75)

@shared_task
def third_scrape():
    """Third and final scheduled attempt to scrape horoscopes if previous attempts failed (late morning)"""
    # Get current date in Baghdad timezone
    now = datetime.now(baghdad_tz)
    current_date = now.date()
    
    # Check if we already have successful data for today
    last_successful_date = get_last_successful_date()
    if last_successful_date == current_date:
        logger.info(f"Already have horoscope data for today ({current_date}). Skipping third attempt.")
        return True
    
    logger.info("Running third and final scheduled horoscope scrape")
    return scrape_horoscopes(attempt_number=3, hours_between_retries=0.5)

@shared_task
def manual_scrape(date_str=None):
    """Run a manual scrape for a specific date"""
    logger.info(f"Running manual scrape for date: {date_str if date_str else 'today'}")
    try:
        success = run_manual_scrape(date_str)
        return success
    except Exception as e:
        logger.error(f"Error in manual_scrape task: {str(e)}", exc_info=True)
        return False