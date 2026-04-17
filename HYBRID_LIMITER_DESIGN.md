# Hybrid Rate Limiter Architecture

## The Cold Truth First
Before we get to the mechanics: optimizing this is a classic trap. You think you want a hybrid limiter because "Redis is too slow." Is it? Redis can handle 100k+ ops/sec with sub-millisecond latency. Have you actually benchmarked Redis as your bottleneck, or are you just over-engineering? 

If you build a local-to-Redis sync, you are trading strict accuracy for lower latency. You *will* have race conditions, nodes *will* drift out of sync, and smart clients *will* temporarily exceed their rate limits during the sync window. If absolute limits (e.g., for billing) are mandatory, drop this design immediately and stick to a purely centralized Redis data store. If you can tolerate a 5-10% overflow margin for the sake of 0ms ingress latency, proceed.

---

## 1. When to use Local Memory? (L1 Cache)

Local memory is your ingress firewall. Every single request hits local memory first.

* **The Fast Path:** Read the local token bucket or counter.
* **If Local says REJECT:** Drop the request instantly. Do not bother Redis. You save a network hop on obvious abusers.
* **If Local says ALLOW:** Let the request pass, increment the local counter, and queue an asynchronous event for the Redis sync.

**Rule of thumb:** Local memory is used for *optimistic allowance* and *aggressive rejection*.

## 2. When to sync with Redis? (L2 / Global State)

If you sync synchronously on every request, you've just built a slower version of talking to Redis directly. Syncing must be **asynchronous** and **batched**.

* **Time-based Flushing:** A background thread flushes local increments to Redis every `N` milliseconds (e.g., 50ms to 200ms).
* **Threshold-based Flushing:** If a specific local counter increments by `X` within the time window, flush it early.
* **The "Delta" Method:** Do not sync the *absolute* value to Redis. Node A shouldn't say "The user has 50 requests". Node A should say "Add +5 to the user's total". Use Redis `INCRBY` (or atomic Lua scripts) to push the *delta*.

## 3. What happens on a mismatch? (Resolution)

"Mismatch" is the wrong mental model. It's not a mismatch; it's a **staleness problem**. Redis is the ultimate source of truth. Your local nodes are always out of date.

* **The Merge:** When the background job fires, it pushes its local deltas to Redis. Redis executes the increments and returns the *new global total*.
* **Local Overwrite:** The local node takes the Redis response and forcefully overwrites its local cache for that key.
* **The "Burst Overflow" Scenario:** 
  * Limit is 100 req/sec. Global state sits at 95.
  * Node A gets 5 requests. Node B gets 5 requests.
  * Both nodes locally see 95. Both optimistically add 5 to their local tracking (total 100) and allow the traffic.
  * *Reality:* 105 requests were allowed.
  * *Resolution:* Node A and B sync with Redis. Redis now says 105. Both nodes pull down 105. Both nodes now aggressively reject the 106th request.

You do not "fix" the mismatch of those 5 overflowing requests. You eat them. That is the cost of a hybrid distributed system.

---

## Architectural Verdict
Build this if your API is processing 10,000+ requests per second across a multi-node cluster and Redis latency is measurably degrading your P99 response times. If you have 5 instances handling 500 RPS total, stop right now, delete this idea, and just use a standard Redis sliding window.
