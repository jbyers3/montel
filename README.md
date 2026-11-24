# Montell — AWS observability backend

AWS edition: scheduled Lambda collectors, DynamoDB latest telemetry and IAM-authenticated API Gateway. See [AWS deployment](AWS-DEPLOY.md) for the SAM template, Secrets Manager configuration, native CloudWatch collector, and limitations. Local mode described below remains available.


Python 3.10+; standard library only. Standalone local portfolio prototype. The dashboard reads the backend, not hard-coded HTML values.

## Run

`python -m montell` starts a synthetic demo. `python -m montell --mode live --interval 60` enables configured collectors. `--once` collects without serving. Demo/live use separate default SQLite files. Bind is loopback only; no authentication. Do not expose publicly.

## Plug in vendors

Each vendor module extends `RestCollector`. Override `fetch()` for native SDK/auth/pagination and `normalize(payload)` to return `Signal` objects. The default HTTP fetch uses HTTPS and optional bearer credentials; its default `items` response schema is a Montell adapter contract, **not a verified native vendor API schema**. No guessed vendor endpoints are included. Configure each enabled vendor with `PREFIX_ENABLED=1`, `PREFIX_URL`, `PREFIX_PATH`, `PREFIX_TOKEN`, `PREFIX_APPLICATION`. Prefixes: CIPHERTRUST, NORTON, CYBERARK, DYNATRACE, CLOUDWATCH, SQLSERVER. Supply real credentials through a secure runtime mechanism, never commit them.

Example generic proxy or test endpoint:

```sh
export DYNATRACE_ENABLED=1
export DYNATRACE_URL=https://your-approved-gateway.example
export DYNATRACE_PATH=/normalized-metrics
python -m montell --mode live --once
```

Expected adapter-contract response: `{"items":[{"resource":"demo","metric":"latency","value":120,"unit":"ms","status":"healthy"}]}`. For direct Dynatrace calls override headers and normalization for your API version. CloudWatch requires AWS signing/SDK; SQL Server requires a driver and read-only catalog/DMV queries, or approved HTTPS gateways. CyberArk and CipherTrust may need session/token exchange. Norton/Symantec product and API versions vary. These native clients are not implemented. For SQL inventory, expensive queries and long-running queries, emit separate metric rows with safe query identifiers, not raw SQL text. TLS has a real verified socket collector: set TLS_ENABLED=1, TLS_HOST, optional TLS_PORT/TLS_APPLICATION. Certificate verification failures appear as collector errors.

## Pipeline

Collectors -> normalized Signal -> SQLite -> /api/signals -> dashboard. /api/collectors reports latest collection outcomes. A failed collector does not stop others. Stored last-known observations remain available after errors; inspect timestamps and collector status. No retention, production scheduler, retries, pagination, secret vault or multitenant security yet. Keep data synthetic or explicitly authorized. Tests: `python -m unittest discover -s tests -v`.
