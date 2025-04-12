from celery import Celery

from mytask.common.settings import get_settings

settings = get_settings()

app = Celery(
    "mytask",
    broker=f"redis://{settings.redis_host}:{settings.redis_port}",
    backend=f"redis://{settings.redis_host}:{settings.redis_port}"
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Load tasks from all modules in the tasks package
app.autodiscover_tasks(["mytask.workers.tasks"]) 