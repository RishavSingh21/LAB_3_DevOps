# Lab 3 Architecture and Workflow

## Goals

The lab demonstrates an automated and observable infrastructure workflow with
infrastructure provisioning, configuration management, centralized metrics
and logs, and security and quality gates. It is intentionally local so the
complete stack can be run without a cloud account.

## Component map

```text
Terraform ── creates ──> Docker network
                              │
Ansible ── runs Compose ──────┤
                              ├── Flask demo ──> Prometheus ──> Grafana
                              │       │
                              │       └── JSON log volume ──> Filebeat
                              │                                │
                              │                                v
                              │                          Logstash ──> Elasticsearch ──> Kibana
                              │
GitHub Actions ── quality/security scans, pytest, Playwright, k6
```

### Provisioning and configuration

- `terraform/` uses the Docker provider to create the dedicated external
  network. It does not create containers; Compose owns service lifecycle.
- `ansible/site.yml` verifies Docker Compose is available and uses the
  `community.docker.docker_compose_v2` module to build and start or stop the
  stack.
- `docker-compose.yml` runs all services on the Terraform-managed network.

### Observability

- `app/` provides `/health`, `/metrics`, and a small greeting UI/API.
- Prometheus scrapes the app's request counter and latency histogram.
- Grafana provisions a Prometheus data source and the `Demo Service`
  dashboard.
- The app writes structured JSON events to stdout and the shared `app-logs`
  volume. Filebeat tails the volume, Logstash decodes the JSON, and
  Elasticsearch indexes events under `lab3-*` for Kibana.

### DevSecOps and quality

The GitHub Actions workflow runs on pushes and pull requests. It includes
Python unit tests, Playwright browser checks, a bounded k6 smoke test, Bandit
and `pip-audit` for Python, Trivy filesystem scanning, Checkov for Terraform,
Terraform formatting/validation, and Ansible syntax validation.

The `FEATURE_GREETING_V2` environment variable provides a simple feature flag.
The default is off; set it to `true` and redeploy to show the alternate
greeting.

## Lab exercises

1. Start the stack and confirm `/health` and `/metrics` return successfully.
2. Observe `demo_http_requests_total` in Prometheus and the Grafana dashboard.
3. Generate app traffic, create a `lab3-*` Kibana data view, and inspect
   structured logs.
4. Run `k6 run -e BASE_URL=http://localhost:5000 loadtest/smoke.js`; inspect
   request rates and latency metrics while it runs.
5. Enable `FEATURE_GREETING_V2`, redeploy, and verify the browser-visible
   greeting changes.
6. Introduce a deliberately vulnerable dependency or insecure Terraform
   setting in a disposable branch and observe the appropriate CI scanner.
   Revert the experiment before merging.

## Trust boundaries and limitations

This is a teaching environment, not a production reference deployment.
Elasticsearch security is disabled, Grafana uses a lab password, and ports are
published to the local host. Logs are retained in a local Docker volume.
There is no TLS, identity provider, persistent Elasticsearch volume, alert
manager, or cloud resource provisioning. Production deployments should add
authentication, network restrictions, secrets management, TLS, durable
storage, alerting, and managed infrastructure appropriate to their provider.
