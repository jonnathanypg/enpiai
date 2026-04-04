"""
Celery Application Factory — Phase 11: Enterprise Scale.
Provides async task execution for heavy operations (PDF, RAG, Broadcasts).

Usage:
    # Start worker:
    celery -A celery_app.celery worker --loglevel=info

Migration Path: Task queue will transition to a P2P job mesh.
"""
import os
import logging
from celery import Celery

logger = logging.getLogger(__name__)


def make_celery(app=None):
    """Create a Celery instance tied to the Flask app context."""
    broker = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6381/0')
    backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6381/1')

    celery = Celery(
        'enpi_ai',
        broker=broker,
        backend=backend,
        include=['tasks']  # Auto-discover tasks module
    )

    celery.conf.update(
        task_serializer='json',
        result_serializer='json',
        accept_content=['json'],
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,
        task_acks_late=True,              # Requeue on worker crash
        worker_prefetch_multiplier=1,     # Fair scheduling
        broker_connection_retry_on_startup=True,
    )

    if app:
        celery.conf.update(app.config)

        class ContextTask(celery.Task):
            """Ensure Flask app context is available inside tasks."""
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)

        celery.Task = ContextTask

    return celery


# Default instance (can be used without Flask for worker startup)
celery = make_celery()
