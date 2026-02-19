# Building SentinelStack: A Gateway That Doesn’t Let Observability Become the Bottleneck

**Author:** Rajat Shriram  
**Date:** 2024-02-19

## The Core Problem
In microservices architectures, the API Gateway is the single point of failure. It is also the perfect place for observability, security, and traffic control. The engineering challenge is simple but brutal: **How do we add heavy instrumentation (logging, metrics, AI analysis) without destroying the latency budget?**

SentinelStack was built to answer this. We didn't want a "black box" gateway; we wanted a system that provides deep insights while staying out of the way.

---

## key Design Decisions

### 1. Asynchronous "Fire-and-Forget" Logging
**The Decision:** We decoupled the request-response cycle from the logging persistence layer.

**Why:** Writing to a database (PostgreSQL) is an I/O blocking operation. If we waited for the log to be written before returning a response to the user, our p95 latency would be tied to database write performance.

**Implementation:** 
- We use an in-memory `asyncio.Queue` to buffer logs.
- A background worker task consumers this queue and performs batch inserts.
- **Result:** The user receives their response immediately. The observability cost is near-zero on the critical path.

### 2. Rate Limiting with Redis & Lua
**The Decision:** We implemented the **Token Bucket** algorithm using Redis Lua scripts.

**Why:** We needed atomic operations to prevent race conditions during high concurrency. A "Check-then-Set" approach in application code would fail under load (Time-of-Check to Time-of-Use race condition).

**Implementation:**
- Lua allows us to run the `get_tokens`, `decrement`, and `update_timestamp` logic server-side in Redis as a single atomic transaction.
- This minimizes network round-trips to exactly one per request.

### 3. Fail-Open Architecture
**The Decision:** If the observability or security subsystems fail, the gateway should (mostly) keep working.

**Philosophy:** "Availability over Consistency" for non-critical components.
- If Redis is down -> The Rate Limiter logs the error and **allows** the request. We'd rather suffer a temporary DDOS than block legitimate traffic due to a cache outage.
- If the Log DB is down -> The background worker retries, then drops logs if the queue overflows. The API stays up.

---

## Tradeoffs & Constraints

### Python vs. The World
**Tradeoff:** We chose Python (FastAPI) over Go or Rust.
- **Pros:** faster development velocity, rich ecosystem for AI integration (SentinelStack's core differentiator).
- **Cons:** The Global Interpreter Lock (GIL) and lower raw throughput.
- **Mitigation:** Heavy use of `async/await` for I/O bound tasks. For CPU-bound tasks (like cryptographic verification), we rely on optimized C-extensions via `uvloop` logic where possible.

### Precision vs. Performance in Metrics
**Tradeoff:** We use `prometheus-client` to aggregate metrics in-process.
- **Pros:** Zero network overhead for metric generation.
- **Cons:** If the worker process restarts, ephemeral counters are lost before scrape.
- **Decision:** Accepted. Trends are more important than individual data points for health monitoring.

---

## Failure Modes Analysis

| Component | Failure Scenario | System Behavior | Impact |
|-----------|------------------|-----------------|--------|
| **Redis** | Connection Timeout | Bypass Rate Limiter (Fail Open) | Risk of overload; API remains available. |
| **Postgres** | Connection Refused | Logs queue up in memory | API available. Memory usage spikes until queue cap is hit. |
| **AI Service** | LLM API Timeout | Return "Analysis Unavailable" | Core dashboard works; Insight widgets show placeholder. |

---

## Scaling: The Road to v2.0
If SentinelStack were to handle 100k+ RPM, the current architecture would need these evolutions:

1. **Log Ingestion:** Direct DB writes would choke. We would introduce a message broker (Kafka/RabbitMQ) between the Gateway and the DB worker to handle backpressure.
2. **Edge Rate Limiting:** Move the initial coarse-grained rate limiting to the load balancer level (Nginx/Envoy) to drop malicious traffic before it even hits Python.
3. **Distributed Caching:** Shard the Redis instance to prevent the single cache node from becoming a hot spot.

## Conclusion
SentinelStack proves that you don't need to sacrifice speed for insight. By strictly separating the **Critical Path** (Request -> Response) from the **Observability Path** (Queue -> Worker -> DB), we achieved sub-5ms internal latency overhead while maintaining rich audit trails and AI-powered insights.