# SentinelStack

> **A High-Performance API Gateway Infrastructure for Control, Security, and Observability.**

![Status](https://img.shields.io/badge/Status-Alpha%20v1-green)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green)
![Redis](https://img.shields.io/badge/Redis-Token%20Bucket-red)

## � Overview

**SentinelStack** is a production-oriented API Gateway designed to be the hard outer shell of your application infrastructure. It sits in front of your business logic, providing a unified layer for identity management, traffic control, and intelligent observability.

Unlike generic reverse proxies, SentinelStack integrates **deterministic rate limiting**, **stateless authentication**, and **AI-assisted incident diagnostics** directly into the request lifecycle.

## 🚀 Key Features

-   **🛡️ Robust Identity & Auth**: Secure, stateless authentication using JWT and Bcrypt hashing.
-   **⚡ Deterministic Rate Limiting**: Redis-backed Token Bucket algorithm ensures precise traffic control per user/IP.
-   **👁️ Total Observability**: Asynchronous, non-blocking logging pipeline that persists every request to PostgreSQL without latency penalties.
-   **🧠 AI Intelligence Engine**: Heuristic-based AI analyzes traffic patterns in real-time to detect anomalies (DDoS, Brute Force) and provides human-readable insights.
-   **📊 Live Ops Dashboard**: Real-time visualization of throughput (RPM), latency, and error rates.

## 🏗️ Architecture

SentinelStack follows a Gateway-First design philosophy where cross-cutting concerns are handled before traffic reaches business logic.

```mermaid
graph TD
    Client -->|"HTTP Request"| Gateway["SentinelStack Gateway"]
    Gateway -->|"1. Context"| Context["Request Context Spine"]
    Gateway -->|"2. Control"| RateLimit["Redis Token Bucket"]
    Gateway -->|"3. Auth"| Auth["JWT Validation"]
    Gateway -->|"4. Business"| App["Business Logic / APIs"]
    Gateway -->|"5. Logs (Async)"| Queue["Log Queue"]
    Queue -.->|"Batch Write"| DB[("(PostgreSQL)")]
    Queue -.->|"Analytics"| AI["AI Heuristics Engine"]
```

## 🛠️ Technology Stack

-   **Core Framework**: Python 3.10+, FastAPI, Pydantic
-   **Database**: PostgreSQL (AsyncPG), SQLAlchemy 2.0
-   **Caching & Throttling**: Redis (AsyncIO) + Lua Scripts
-   **Infrastructure**: Docker & Docker Compose
-   **Frontend**: HTML5, TailwindCSS, Chart.js (Dashboard)

## ⚡ Getting Started

### Prerequisites
-   Docker & Docker Compose
-   Python 3.10+

### Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/yourusername/SentinelStack.git
    cd SentinelStack
    ```

2.  **Set Up Virtual Environment**
    ```bash
    python -m venv venv
    # Windows
    venv\scripts\activate
    # Mac/Linux
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Start Infrastructure (Postgres & Redis)**
    ```bash
    docker-compose -f infra/docker-compose.yml up -d
    ```

5.  **Initialize Database**
    ```bash
    python -m alembic upgrade head
    ```

6.  **Run the Gateway**
    ```bash
    python -m uvicorn sentinelstack.gateway.main:app --reload
    ```

## 🖥️ Usage

### Ops Dashboard
Access the live metrics and AI insights at:
`http://localhost:8000/dashboard/`

### API Documentation
Interactive API docs (Swagger UI) are available at:
`http://localhost:8000/docs`

### Key Endpoints
-   `POST /auth/signup`: Register a new user.
-   `POST /auth/token`: Login and receive a JWT.
-   `GET /health`: System health check.
-   `GET /stats/dashboard`: Raw metrics JSON.
-   `GET /ai/insight`: AI-generated system status.

## 🔮 Roadmap (v2)
-   [ ] Distributed Rate Limiting (Redis Cluster)
-   [ ] User-Agent / Bot Detection
-   [ ] Integration with LLMs (OpenAI/Gemini) for deep log analysis
-   [ ] Comprehensive Unit Test Suite

## 📄 License
Proprietary / Confidential. All rights reserved.