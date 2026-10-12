# Hosting and production readiness

Fieldnote is intentionally configured for local demos and private single-machine analysis. It now has local accounts and per-account dataset checks, but that local login is not a production identity system. Do not change the host to `0.0.0.0` and expose this server publicly; datasets are held in process memory and the app has not had a production security review.

Before an internet-facing deployment, add and review all of the following:

- Production identity management, hardened sessions, workspace membership, and authorization review for every dataset and analysis request
- TLS termination, CSRF protection, request limits, upload scanning, and rate limiting
- Durable database-backed datasets with tenant isolation, explicit retention and deletion, and encrypted storage
- Scheduled backups with a tested restore procedure
- Secret management outside source control and a documented process for key rotation
- Monitoring for availability, request failures, storage use, and model-provider errors, without logging uploaded rows
- A privacy notice and retention policy that match the actual hosting and AI-provider configuration
- Automated security, parser, and analysis checks before each release

For a class or judge presentation, keep the default localhost setup and use the built-in sample data. The optional model adapter currently sends only the question and schema, but verify the chosen provider's current terms and settings before enabling it for sensitive data.
