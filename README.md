# Connector implementation guide

The V6 module supports validated CSV import and records pending connector configuration only. It intentionally does not make network calls.

For an approved vendor connector:
- Use the vendor-supported SDK/API and a strict host allowlist.
- Use OAuth/service-account scopes with least privilege.
- Store credentials in a managed secrets service, never in source code or uploaded CSV.
- Add pagination, retries, rate limits, timeouts and TLS verification.
- Validate schemas and preserve source timestamps.
- Redact tokens and personal data from logs.
- Test with synthetic fixtures and obtain security approval before activation.
