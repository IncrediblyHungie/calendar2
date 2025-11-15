"""
Gunicorn Production Configuration for Fly.io
Optimized for 16+ concurrent users with AI image generation
"""
import multiprocessing
import os

# Server Socket
bind = f"0.0.0.0:{os.getenv('PORT', '8080')}"
backlog = 2048

# Worker Processes - Optimized for Fly.io 4 vCPUs
# Rule: (2 x CPU cores) + 1
workers = min(multiprocessing.cpu_count() * 2 + 1, 9)  # Max 9 workers on 4 vCPUs
worker_class = 'sync'  # Use sync workers (better for long-running AI requests)
worker_connections = 1000
max_requests = 1000  # Restart workers after 1000 requests (prevent memory leaks)
max_requests_jitter = 100  # Add randomness to prevent all workers restarting at once

# Timeouts - Critical for AI image generation
timeout = 300  # 5 minutes (Gemini API can take 30-60 seconds per image)
graceful_timeout = 30
keepalive = 5

# Process Naming
proc_name = 'kevcal-hunkofthemonth'

# Logging
accesslog = '-'  # Log to stdout (Fly.io captures this)
errorlog = '-'   # Log to stderr
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Server Mechanics
daemon = False  # Don't daemonize (Fly.io needs foreground process)
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (handled by Fly.io proxy)
forwarded_allow_ips = '*'
proxy_protocol = True
proxy_allow_ips = '*'

# Pre/Post Fork Hooks
def on_starting(server):
    server.log.info("=" * 70)
    server.log.info("🚀 KevCal Production Server Starting")
    server.log.info(f"   Workers: {workers}")
    server.log.info(f"   Timeout: {timeout}s (AI generation support)")
    server.log.info(f"   Concurrency: ~{workers * 4} simultaneous requests")
    server.log.info("=" * 70)

def worker_int(worker):
    worker.log.info(f"Worker {worker.pid} received INT or QUIT signal")

def pre_fork(server, worker):
    pass

def post_fork(server, worker):
    server.log.info(f"Worker spawned (pid: {worker.pid})")

def pre_exec(server):
    server.log.info("Forked child, re-executing.")

def when_ready(server):
    server.log.info("Server is ready. Spawning workers")

def worker_abort(worker):
    worker.log.info(f"Worker {worker.pid} aborted")
