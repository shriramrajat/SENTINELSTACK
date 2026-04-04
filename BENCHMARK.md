# SentinelStack Benchmark & Resilience Report

## Hardware & Environment Constraints
- **Host System:** Windows OS 
- **Gateway Server:** Uvicorn (Local Execution - Single Worker)
- **Dependencies:** PostgreSQL and Redis (Docker Compose)
- **Testing Tool:** Locust (Python)
- **Constraint Identified:** Windows `select()` event loop enforces a hard limit of 512 concurrent socket connections. Testing was capped safely at 450 users to prevent OS-level execution termination of the Uvicorn worker (`ValueError: too many file descriptors`).

---

## 1. Load Testing & Throughput Optimizations

### The Scenario
Traffic was pushed leveraging up to **450 concurrent users** with an aggressive spawn rate (100 users/sec), hitting protected authentication and rate-limited endpoints.

### Baseline vs Optimized Results
*Earlier un-pooled Redis connections caused severe blocking which restricted throughout to ~69 RPS.*

| Configuration | Users | Peak RPS   | Limiting Factor / Bottleneck |
|---------------|-------|------------|-------------------------------|
| Non-Pooled    | 500   | 69.8       | Redis connection tear-downs. |
| **Pooled (Fix)** | **450** | **~110.0** | **Bcrypt hashing CPU saturation.** |

### Architectural Findings
By introducing a massive connection pool (`max_connections=1000`) within `cache.py`, the system successfully bypassed Redis network choke-points. 
- The Gateway effectively scaled up to **~110 RPS**. 
- Because `/auth/login` utilizes synchronous `bcrypt` hashing which is heavily CPU-bound in Python, 110 RPS represents the virtual mathematical maximum capacity for a single Uvicorn worker process. 
- *To scale beyond 300+ RPS in production, horizontal scaling via multi-worker Uvicorn (`--workers 4`) is required.*

---

## 2. Chaos Engineering & Resilience (Failure Testing)

### The Fragility Test: Redis Cluster Outage
To determine system fragility, a simulated catastrophic loss of the caching layer was performed.

* **Action:** `docker stop sentinel_redis` (Manual termination of the Redis pipeline during active Locust traffic).
* **Initial Behavior (Vulnerable):** 
  - The Gateway Middleware directly queried Redis to compute the Token Bucket limits. When Redis abruptly died, the unhandled `ConnectionError` bled through the stack and crashed the active API.
  - Locust recorded massive spikes in **`500 Internal Server Errors`**.

### The Resolution (In-Memory Fallback)
To address this single point of failure, `middleware.py` was patched with a **fail-open circuit breaker** mixed with an **Emergency Fallback Rate Limiter**.
We wrapped `rate_limiter.check_request()` in a `try/except` loop and activated a local Python dictionary Token Bucket upon catching exception logic.

**Final Hardened Results:**
- When Redis was executed mid-flight, the system gracefully transitioned to local memory tokens.
- Locust recorded exactly **0 `500 Internal Server Errors`**.
- Excess DDoS traffic was correctly met with `429 Emergency Rate limit exceeded. Service degraded.` ensuring database protection was maintained securely even without Redis availability.