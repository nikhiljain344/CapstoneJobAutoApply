import multiprocessing

# Gunicorn configuration
bind = "0.0.0.0:5002"
workers = 1  # Reduce to 1 worker for debugging
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stdout
loglevel = "debug"
capture_output = True
enable_stdio_inheritance = True

# Process naming
proc_name = "autojobapply"

# Debug mode
reload = True
spew = True

# SSL (uncomment and modify if using HTTPS)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile" 