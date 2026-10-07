"""Exercise 4 Step 1: Celery application configuration (Order & Invoice System).

Points the Celery app at a local Redis broker/result backend.  For RabbitMQ
use broker='pyamqp://guest@localhost//' and backend='rpc://' instead.

Run the worker from this directory with either:
    celery -A tasks worker --loglevel=info
    celery -A celery_config worker --loglevel=info
"""

from celery import Celery

app = Celery(
    "order_system",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
    include=["tasks"],
)

app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    enable_utc=True,
)
