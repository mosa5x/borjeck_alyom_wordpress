import os
import logging
from celery import Celery
from celery.schedules import crontab
import pytz
import tasks

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='celery_horoscope.log'
)
logger = logging.getLogger(__name__)

# Baghdad timezone
baghdad_tz = pytz.timezone('Asia/Baghdad')

# Initialize Celery
app = Celery('horoscope_scraper')

# Configure Celery
app.conf.update(
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/0',
    timezone='Asia/Baghdad',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=6*60*60,  # 6 hour time limit for tasks (matching your time_limit)
    worker_max_tasks_per_child=100,
    worker_concurrency=1,  # Process one task at a time
)

# Include tasks from tasks.py
app.conf.imports = ['tasks']  # This tells Celery to import your tasks.py file

# Schedule the scraping tasks
app.conf.beat_schedule = {
    'first-scrape': {
        'task': 'tasks.first_scrape',
        'schedule': crontab(hour=4, minute=40),  # 1:30 AM Baghdad time
    },
    'second-scrape': {
        'task': 'tasks.second_scrape',
        'schedule': crontab(hour=5, minute=0),   # 5:00 AM Baghdad time
    },
    'third-scrape': {
        'task': 'tasks.third_scrape',
        'schedule': crontab(hour=9, minute=0),   # 9:00 AM Baghdad time
    },
}

if __name__ == '__main__':
    app.start()
