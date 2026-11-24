# AWS deployment

The AWS edition runs the collector on Lambda every five minutes via EventBridge and serves the latest observations and collection status from DynamoDB through an IAM-authenticated API Gateway REST API. It is intentionally a small, single-environment portfolio prototype. The original local dashboard and SQLite backend remain available for local development. The AWS API does not host the browser dashboard; use an AWS SigV4-capable API client. Historical snapshots are not yet retained by the AWS store.

## Deploy a demo

Prerequisites: AWS CLI configured with an authorized deployment identity, AWS SAM CLI, Python 3.12. From this folder:

```sh
sam validate --lint
sam build
sam deploy --guided --parameter-overrides Mode=demo
```

Acknowledge IAM role creation during deployment. The scheduled function will collect synthetic data within the next scheduled invocation. You can also invoke it manually using the CollectorFunction stack output:

```sh
aws lambda invoke --function-name YOUR_COLLECTOR_FUNCTION --payload '{}' --cli-binary-format raw-in-base64-out result.json
```

Read `ApiUrl` from the stack outputs. Use an IAM principal permitted `execute-api:Invoke` on the desired API stage/method/path and an AWS SigV4 client (for example, Postman with AWS Signature authorization, service `execute-api`, and your deployment region). GET `/api/signals` and `/api/collectors`. No anonymous API access is intended. The Lambda execution role is distinct from the caller's role. No browser credentials should be embedded in HTML. Delete the stack with `sam delete` when finished; AWS usage may incur charges.

## Connect real vendors

Copy `vendor-config.example.json` into a **private** configuration file outside this repository; enable only your authorized targets and insert the appropriate credentials. Create a Secrets Manager secret from that JSON in the deployment region. Use a separate stack name for live mode and set `Mode=live` and `ConfigSecretArn=YOUR_SECRET_ARN` with `sam deploy --guided --parameter-overrides ...`. The collector role can read only that secret (default Secrets Manager encryption assumed; customer-managed KMS requires an additional key grant). Never commit tokens, credentials, actual infrastructure names, or raw queries. Do not expose employer infrastructure. CloudWatch uses the execution role, not static AWS access keys.

- `montell/collectors/aws_cloudwatch.py`: native SDK call for configured metrics (one resource identifier per unique metric/dimension combination); thresholds optional, absence of datapoints is unknown. Cross-account roles are not implemented.
- `montell/collectors/tls.py`: verified TLS socket certificate expiry. Invalid certificates surface as collector errors.
- `montell/collectors/ciphertrust.py`, `norton.py`, `cyberark.py`, `dynatrace.py`, `sqlserver.py`: extension points for your authorized native APIs or approved normalized HTTPS gateways. Override `fetch`, `headers`, and `normalize` as necessary. The default response contract is `{"items":[{"resource":"demo","metric":"latency","value":120,"unit":"ms","status":"healthy"}]}`; it is not a native vendor schema. For SQL Server use an approved gateway or package a compatible read-only SQL driver, query catalog/DMVs and return separate `Signal` rows for inventory, expensive queries and long-running queries. Do not collect raw SQL or credentials.
- Private endpoints require VPC connectivity, DNS, security groups and routing (not included). Public endpoints use verified HTTPS; allowlist approved destinations before enabling live collection. Existing HTTP transport follows redirects by default; review this before sending vendor credentials to untrusted endpoints.

The Lambda runs collectors sequentially; errors from collection are isolated and the invocation is marked failed when any collector fails. Malformed secret configuration fails before collection starts. Last-known values persist; check `observed_at` and collector status. No stale-resource deletion, retention, pagination at the API boundary, DLQ, or production alerting is implemented. DynamoDB stores one current row per signal identity per mode; reads query all latest rows and are suitable only for small datasets. For fleet scale, shard by application/source and add paginated queries and historical storage. Do not use this prototype for regulated or sensitive production data without hardening.

Local tests: `python -m unittest discover -s tests -v`. AWS tests use injected fake clients. The AWS deployment and live integrations have not been executed or verified against real AWS accounts.
