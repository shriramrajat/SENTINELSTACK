# Benchmark Report

## Hardware / Environment
- **Machine:** [Your CPU/RAM] (e.g., M1 Macbook Air or AWS t3.medium)
- **OS:** Windows / Linux
- **Network:** Localhost (Docker)

## Results

### Load Test (Endpoint: `/health`)

| Load | Avg Latency | p95 Latency | Errors (%) | Notes |
|------|-------------|-------------|------------|-------|
| 1k RPM | 5.29ms | 11.26ms | 0.00% | Excellent performance, well below 500ms threshold. |
| 5k RPM | 4.54ms | 8.44ms | 0.00% | Latency actually improved/stayed stable under higher load. |

### Rate Limit Behavior
*Observation of how the system handles traffic spikes.*

- **Endpoint:** `/not-found` (Triggers global rate limiter)
- **Observations:**
  - Tested at **2k RPM** (approx 33 RPS).
  - **99.05%** of requests returned expected status (mostly 429s once limit hit).
  - **0.94%** failed checks (likely 500s or timeouts during initial spike).
  - Latency remained low even during rejection (p95: **16.17ms**).
  - System correctly identifies and rejects excess traffic without crashing.

## Methodology
- Tool: k6
- Duration: 30s warmup, 1m measurement
- Middleware: Active