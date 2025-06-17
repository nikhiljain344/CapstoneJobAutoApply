import os
from celery import Celery
from kombu import Queue

def make_celery(app_name=__name__):
    """Create Celery instance"""
    
    # Redis configuration
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    celery = Celery(
        app_name,
        broker=redis_url,
        backend=redis_url,
        include=['src.services.automation_tasks']
    )
    
    # Celery configuration
    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=30 * 60,  # 30 minutes
        task_soft_time_limit=25 * 60,  # 25 minutes
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=1000,
        
        # Queue configuration
        task_routes={
            'src.services.automation_tasks.apply_to_job': {'queue': 'job_applications'},
            'src.services.automation_tasks.scrape_job_details': {'queue': 'job_scraping'},
            'src.services.automation_tasks.send_notification': {'queue': 'notifications'},
        },
        
        # Define queues
        task_queues=(
            Queue('job_applications', routing_key='job_applications'),
            Queue('job_scraping', routing_key='job_scraping'),
            Queue('notifications', routing_key='notifications'),
            Queue('celery', routing_key='celery'),  # Default queue
        ),
        
        # Retry configuration
        task_default_retry_delay=60,  # 1 minute
        task_max_retries=3,
        
        # Beat schedule for periodic tasks
        beat_schedule={
            'process_application_queue': {
                'task': 'src.services.automation_tasks.process_application_queue',
                'schedule': 300.0,  # Every 5 minutes
            },
            'cleanup_old_tasks': {
                'task': 'src.services.automation_tasks.cleanup_old_tasks',
                'schedule': 3600.0,  # Every hour
            },
        },
    )
    
    return celery

# Create Celery instance
celery_app = make_celery()

