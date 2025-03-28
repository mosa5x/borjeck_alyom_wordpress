#!/bin/bash

# Check if Redis is running, and start it if not
redis_running=$(pgrep -x redis-server || echo "")
if [ -z "$redis_running" ]; then
    echo "Starting Redis server..."
    redis-server --daemonize yes
else
    echo "Redis server is already running."
fi

# Start the Celery worker with appropriate log level
echo "Starting Celery worker..."
celery -A celery_config worker --loglevel=info --logfile=celery_worker.log --detach

# Start the Celery beat scheduler for periodic tasks
echo "Starting Celery beat scheduler..."
celery -A celery_config beat --loglevel=info --logfile=celery_beat.log --detach

echo "Celery worker and beat scheduler started!"
echo "Check logs at:"
echo "  - celery_worker.log"
echo "  - celery_beat.log"
echo "  - tasks_horoscope.log"
echo "  - celery_horoscope.log"


