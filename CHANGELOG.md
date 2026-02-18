# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-02-18

### Added
- **Core API Gateway**: Initial release of SentinelStack with FastAPI.
- **Authentication**: Stateless JWT authentication with bcrypt password hashing.
- **Rate Limiting**: Deterministic Redis-backed Token Bucket algorithm.
- **AI Integration**: OpenAI-powered incident analysis and root cause detection.
- **Monitoring**: Real-time dashboard, Prometheus metrics exporter, and Grafana integration.
- **Database**: PostgreSQL integration with AsyncPG and SQLAlchemy 2.0.
- **Infrastructure**: Docker and Docker Compose support for production deployment.
- **CI/CD**: GitHub Actions pipeline for testing, linting, and build verification.