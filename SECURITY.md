# Security Policy

## Supported Versions

Use this section to tell people about which versions of your project are
currently being supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability within SentinelStack, please do not disclose it publicly until it has been addressed.

1.  **Draft a Report**: Include details about the vulnerability, steps to reproduce, and potential impact.
2.  **Contact**: Please email the security team or the maintainer directly.
3.  **Response**: We will acknowledge your report within 48 hours and provide an estimated timeline for a fix.
4.  **Patch**: Once a fix is ready, we will release a patch and credit you for the discovery (if desired).

## Security Best Practices included in SentinelStack

-   **Stateless Authentication**: Uses JWTs with short expiration times.
-   **Password Hashing**: Uses `bcrypt` for secure password storage.
-   **Rate Limiting**: Protects against brute-force and DDoS attacks.
-   **Input Validation**: Strict input validation using Pydantic models.