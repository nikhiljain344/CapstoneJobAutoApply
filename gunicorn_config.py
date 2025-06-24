import multiprocessing

# Gunicorn configuration
bind = "0.0.0.0:5002"
workers = 1  # Single worker to reduce memory usage
worker_class = "sync"
worker_connections = 100
timeout = 30
keepalive = 2

# Memory optimization
worker_tmp_dir = "/dev/shm"
worker_max_requests = 1000
worker_max_requests_jitter = 50

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "debug"  # Temporarily set to debug to see what's happening
capture_output = True
enable_stdio_inheritance = True

# Process naming
proc_name = "autojobapply"

# Disable auto-reloading
reload = False
preload_app = False  # Disable preloading to prevent potential loops

# Debug settings
spew = False  # Disable detailed debug logging
check_config = True  # Check configuration before starting

# SSL (uncomment and modify if using HTTPS)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile" 