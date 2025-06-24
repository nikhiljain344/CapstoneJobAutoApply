import multiprocessing

# Gunicorn configuration
bind = "0.0.0.0:5002"
workers = 1  # Single worker to reduce memory usage
worker_class = "sync"
worker_connections = 100  # Reduced from 1000
max_requests = 1000  # Restart workers after 1000 requests to free memory
max_requests_jitter = 50
timeout = 30
keepalive = 2

# Memory optimization
worker_tmp_dir = "/dev/shm"  # Use RAM for temporary files
worker_max_requests = 1000
worker_max_requests_jitter = 50

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stdout
loglevel = "info"  # Changed from debug to reduce memory usage
capture_output = True
enable_stdio_inheritance = True

# Process naming
proc_name = "autojobapply"

# Preload app to save memory across workers
preload_app = True

# Debug mode
reload = True
spew = True

# SSL (uncomment and modify if using HTTPS)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile" 