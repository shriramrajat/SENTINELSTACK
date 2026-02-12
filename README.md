# SentinelStack v1

> **A High-Performance API Gateway Infrastructure for Control, Security, and Observability.**

![Status](https://img.shields.io/badge/Status-Alpha%20v1-green)
![CI Pipeline](https://img.shields.io/badge/Build-Passing-brightgreen)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green)
![Prometheus](https://img.shields.io/badge/Prometheus-Monitoring-orange)

## 👁️ Overview

**SentinelStack** is a production-oriented API Gateway designed to be the hard outer shell of your application infrastructure. It sits in front of your business logic, providing a unified layer for identity management, traffic control, and intelligent observability.

Unlike generic reverse proxies, SentinelStack integrates **deterministic rate limiting**, **stateless authentication**, and **real-time metrics** directly into the request lifecycle.

## 🏗️ Architecture

SentinelStack follows a Gateway-First design philosophy where cross-cutting concerns are handled before traffic reaches business logic.

```mermaid
graph TD
    Client -->|"HTTP Request"| Gateway["SentinelStack Gateway"]
    Gateway -->|"1. Metrics"| Prom["Prometheus Exporter"]
    Gateway -->|"2. Control"| RateLimit["Redis Token Bucket"]
    Gateway -->|"3. Auth"| Auth["JWT Validation"]
    Gateway -->|"4. Business"| App["Business Logic / APIs"]
    
    Prom -.->|"Scrape (15s)"| Prometheus["Prometheus Server"]
    Prometheus -.->|"Query"| Grafana["Grafana Dashboard"]
```

## 🚀 Key Features

-   **🛡️ Robust Identity & Auth**: Secure, stateless authentication using JWT and Bcrypt (No passlib dependency).
-   **⚡ Deterministic Rate Limiting**: Redis-backed Token Bucket algorithm ensures precise traffic control per user/IP.
-   **👁️ Monitoring Stack**: 
    -   **Prometheus**: Scrapes `/metrics` for throughput, latency, and error rates.
    -   **Grafana**: Visualizes real-time performance on port `3001`.
-   **✅ CI/CD Ready**: GitHub Actions pipeline for linting, testing, and Docker build verification.
-   **🧪 Integration Tested**: Full test suite covering Signup -> Login -> Rate Limiting flows.

## 🛠️ Technology Stack

-   **Core Framework**: Python 3.10+, FastAPI, Pydantic
-   **Database**: PostgreSQL (AsyncPG), SQLAlchemy 2.0
-   **Caching & Throttling**: Redis (AsyncIO) + Lua Scripts
-   **Monitoring**: Prometheus (Client & Server), Grafana
-   **Testing**: Pytest, AsyncIO, HTTPX
-   **Infrastructure**: Docker & Docker Compose

## ⚡ Getting Started (Local Development)

### Prerequisites
-   Docker & Docker Compose
-   Python 3.10+

### Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/shriramrajat/sentinelstack.git
    cd SentinelStack
    ```

2.  **Run with Docker (Best for Demo)**
    This spins up Postgres, Redis, Prometheus, Grafana, and the API.
    ```bash
    docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build
    ```

3.  **Access the Services**
    -   **API**: `http://localhost:8000`
    -   **Docs**: `http://localhost:8000/docs`
    -   **Grafana**: `http://localhost:3001` (User: `admin` / `admin`)
    -   **Prometheus**: `http://localhost:9090`

## 🧪 Running Tests

To run the integration test suite (requires local env or test containers):

```bash
# Install test dependencies
pip install -r requirements.txt

# Run tests
pytest
```

## ☁️ Deployment (Production)

1.  **Prepare Server**: Ubuntu 24.04 LTS with Docker.
2.  **Configure Secrets**: Create `.env.prod`.
3.  **Deploy**:
    ```bash
    docker compose --env-file .env.prod -f docker-compose.prod.yml up -d
    ```

## 🔮 Roadmap (v2)
-   [ ] Distributed Rate Limiting (Redis Cluster)
-   [ ] User-Agent / Bot Detection
-   [ ] Integration with LLMs (OpenAI/Gemini) for deep log analysis

## 📄 License
Proprietary / Confidential. All rights reserved.