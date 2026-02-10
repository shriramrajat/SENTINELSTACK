# SentinelStack v1 (In Development)

> **A Unified API Gateway Infrastructure for Control, Safety, and Operability.**

![Status](https://img.shields.io/badge/Status-Alpha%20v1-green)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green)
![Redis](https://img.shields.io/badge/Redis-Token%20Bucket-red)

## 🚧 Project Status: Alpha v1 Complete
**SentinelStack Core Infrastructure is Operational.**
The 10-day sprint is complete. The system is ready for integration testing.

- [x] **Day 1**: Foundation & Docker
- [x] **Day 2**: Identity Schema (Postgres+Alembic)
- [x] **Day 3**: Auth Logic (JWT/Bcrypt)
- [x] **Day 4**: Request Context Spine
- [x] **Day 5**: Rate Limit Engine (Redis+Lua)
- [x] **Day 6**: Control Middleware
- [x] **Day 7**: Async Logging Pipeline
- [x] **Day 8**: Aggregation & Metrics
- [x] **Day 9**: Ops Dashboard
- [x] **Day 10**: AI Explainability & Polish

---

## 1. What SentinelStack Actually Is
SentinelStack is a production-oriented API Gateway Infrastructure Core that sits in front of application APIs. It is unrelated to traditional "microservices" products; it is a single deployable system designed to be the hard outer shell of your API.

It provides **cross-cutting control primitives**:
1.  **Identity**: Who are you? (Bcrypt/JWT)
2.  **Control**: Can you do this? (Deterministic Rate Limiting)
3.  **Observability**: What happened? (Async Logging)
4.  **Explanation**: Why did it break? (AI-Assisted Incident Summaries)

## 2. Design Philosophy (Non-Negotiable)
1.  **Gateway-First**: All traffic flows through one controlled request lifecycle.
2.  **Deterministic Control**: Rate limits are rule-based and explainable. No "maybe" logic.
3.  **Async by Default**: Logging never blocks the request. If the logger dies, the API stays up.
4.  **AI Explains, Never Decides**: AI summarizes confirmed incidents. It never bans users autonomously.

## 3. High-Level Architecture
```mermaid
graph TD
    Client -->|HTTP Request| Gateway[SentinelStack Gateway]
    Gateway -->|1. Context| Context[Request Context]
    Gateway -->|2. Control| RateLimit[Redis Token Bucket]
    Gateway -->|3. Auth| Auth[JWT Validation]
    Gateway -->|4. Business| App[Business Logic]
    Gateway -->|5. Logs (Async)| Queue[Log Queue]
    Queue -.->|Batch Write| DB[(PostgreSQL)]
```

## 4. Technology Stack
- **Core**: Python 3.10+, FastAPI, Pydantic
- **Data**: PostgreSQL (AsyncPG), SQLAlchemy 2.0
- **Cache**: Redis (AsyncIO) + Lua Scripts
- **Infra**: Docker Compose

## 5. Development Setup

### Prerequisites
- Docker & Docker Compose
- Python 3.10+

### Quick Start
1.  **Clone & Env**:
    ```bash
    git clone https://github.com/yourusername/SentinelStack.git
    cd SentinelStack
    python -m venv venv
    source venv/bin/activate  # Windows: venv\scripts\activate
    pip install -r requirements.txt
    ```

2.  **Start Infrastructure**:
    ```bash
    docker-compose -f infra/docker-compose.yml up -d
    ```

3.  **Run Migrations**:
    ```bash
    python -m alembic upgrade head
    ```

4.  **Start Gateway**:
    ```bash
    python -m uvicorn sentinelstack.gateway.main:app --reload
    ```

## 7. Features & Access
### 🤖 AI-Powered Ops Dashboard
Access the real-time monitoring dashboard at: `http://localhost:8000/dashboard/`
- **Live Metrics**: Throughput (RPM), Latency (ms), Error Rate.
- **AI Diagnostics**: The system self-diagnoses traffic anomalies (e.g., DDoS, Brute Force) and displays human-readable insights.

### 🔒 Security & Limits
- **Authentication**: JWT-based stateless auth.
- **Rate Limiting**: Configurable Token Bucket algorithm backed by Redis Lua scripts.
- **Logging**: Non-blocking async logger writing to PostgreSQL.

## 8. License
Proprietary / TBD.