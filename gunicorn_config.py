import multiprocessing

# Gunicorn configuration
bind = "0.0.0.0:5002"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = "logs/access.log"
errorlog = "logs/error.log"
loglevel = "info"

# Process naming
proc_name = "autojobapply"

# SSL (uncomment and modify if using HTTPS)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile" 