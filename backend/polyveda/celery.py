"""
Celery configuration for PolyVeda.
"""
import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'polyveda.settings.production')

app = Celery('polyveda')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# Celery configuration
app.conf.update(
    # Broker settings
    broker_url=settings.CELERY_BROKER_URL,
    result_backend=settings.CELERY_RESULT_BACKEND,
    
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone=settings.CELERY_TIMEZONE,
    enable_utc=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    
    # Task routing
    task_routes={
        'accounts.tasks.*': {'queue': 'accounts'},
        'academics.tasks.*': {'queue': 'academics'},
        'analytics.tasks.*': {'queue': 'analytics'},
        'notifications.tasks.*': {'queue': 'notifications'},
        'ai.tasks.*': {'queue': 'ai'},
        'blockchain.tasks.*': {'queue': 'blockchain'},
    },
    
    # Queue settings
    task_default_queue='default',
    task_default_exchange='default',
    task_default_routing_key='default',
    
    # Beat settings
    beat_scheduler='django_celery_beat.schedulers:DatabaseScheduler',
    
    # Result settings
    result_expires=3600,  # 1 hour
    result_persistent=True,
    
    # Security settings
    security_key=settings.SECRET_KEY,
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Error handling
    task_reject_on_worker_lost=True,
    task_acks_late=True,
    
    # Performance
    worker_concurrency=4,
    task_compression='gzip',
    result_compression='gzip',
)

@app.task(bind=True)
def debug_task(self):
    """Debug task to test Celery setup."""
    print(f'Request: {self.request!r}')
    return 'Celery is working!'

# Import tasks to ensure they are registered
from accounts.tasks import *
from academics.tasks import *
from analytics.tasks import *
from notifications.tasks import *
from ai.tasks import *
from blockchain.tasks import *