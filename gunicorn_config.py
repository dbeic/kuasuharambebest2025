import os

bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"
workers = 2
threads = 2
timeout = 120
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Security settings
worker_tmp_dir = "/dev/shm"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
preload_app = True

# Use wsgi:application
def when_ready(server):
    server.log.info("Gunicorn server is ready with security settings")

def pre_request(worker, req):
    # Log request for monitoring
    worker.log.debug(f"Request: {req.method} {req.path}")
