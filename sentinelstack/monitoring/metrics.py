from prometheus_client import Counter, Histogram, Gauge

# ---------------------------------------------------------
# HTTP RED METRICS (Rate, Errors, Duration)
# ---------------------------------------------------------

# Counter: Total number of HTTP requests
# Labels:
# - method: GET, POST, etc.
# - path: The endpoint path (e.g., /auth/token)
# - status_code: 200, 400, 500
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total count of HTTP requests",
    ["method", "path", "status_code"]
)

# Histogram: Request latency in seconds
# Buckets optimized for API latency (10ms to 5s)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

# ---------------------------------------------------------
# BUSINESS METRICS
# ---------------------------------------------------------

# Counter: Rate limit hits (429s)
RATE_LIMIT_HITS = Counter(
    "rate_limit_hits_total",
    "Total number of rate limit rejections",
    ["path", "client_ip"]
)

# Gauge: Size of the async log queue
# Monitors if the logging system is backing up
LOG_QUEUE_SIZE = Gauge(
    "log_queue_size",
    "Current number of logs waiting to be written to DB"
)

# Counter: System Errors (Internal 500s captured by middleware)
SYSTEM_ERRORS = Counter(
    "system_unhandled_errors_total",
    "Total unhandled exceptions caught by middleware",
    ["path", "error_type"]
)