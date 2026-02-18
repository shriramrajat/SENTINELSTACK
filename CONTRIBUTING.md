# Contributing to SentinelStack

First off, thanks for taking the time to contribute!

The following is a set of guidelines for contributing to SentinelStack. These depend on the hosting platform (GitHub), but the core principles remain.

## Code of Conduct

This project and everyone participating in it is governed by the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/). By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

-   **Use the Issue Tracker**: Create a new issue describing the bug.
-   **Include Logs**: Attach relevant error logs or stack traces.
-   **Reproducible Steps**: Provide clear steps to reproduce the issue.

### Suggesting Enhancements

-   **Describe the Goal**: What problem does this enhancement solve?
-   **Explain the Solution**: How should it be implemented?

### Pull Requests

1.  **Fork the Repo** (if external) or create a new branch `feature/your-feature`.
2.  **Follow Style Guide**: Stick to PEP 8.
3.  **Run Tests**: Ensure all tests pass (`pytest`).
4.  **Update Docs**: Keep README and docstrings up to date.
5.  **Submit PR**: Create a descriptive PR outlining your changes.

## Development Setup

1.  Clone repo.
2.  Install dependencies: `pip install -r requirements.txt`.
3.  Set up [.env](cci:7://file:///d:/Rajat/Projects/SENTINELSTACK/.env:0:0-0:0) with DB and Redis credentials.
4.  Run migrations: `alembic upgrade head`.
5.  Start server: `uvicorn sentinelstack.main:app --reload`.