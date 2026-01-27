import os


_redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
broker_url = _redis_url
result_backend = _redis_url

task_serializer = "json"
accept_content = ["json"]
result_serializer = "json"
timezone = "UTC"
enable_utc = True

# Worker settings
worker_prefetch_multiplier = 1
task_acks_late = True
task_reject_on_worker_lost = True
worker_max_tasks_per_child = 1000
