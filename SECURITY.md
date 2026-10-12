# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.x     | :white_check_mark: |
| < 2.0   | :x:                |

## Reporting a Vulnerability

Security and data privacy are core principles of this project:
- Raw dataset records are processed strictly in-memory and on your local machine.
- Local user authentication utilizes salted PBKDF2-HMAC-SHA256 password hashing.
- AI wording assistance only sends column schemas and questions—never data rows.

If you discover a security vulnerability, please **do not open a public issue**. Instead, please report it privately:
- Email: [srivastavasuyash803@gmail.com](mailto:srivastavasuyash803@gmail.com) with the subject `[SECURITY] Natural Language Data Analyst Vulnerability`.
- Provide detailed steps to reproduce the issue and any relevant system details.

We will acknowledge receipt within 48 hours and work with you to remediate the issue promptly.
