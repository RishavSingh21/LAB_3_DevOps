# Lab 3: Monitoring, Logging & DevSecOps

A local, reproducible lab for provisioning and configuring a small observable
service with Terraform, Ansible, Prometheus, Grafana, and the ELK stack. The
GitHub Actions workflow runs code and infrastructure checks, browser tests, and
a short k6 load test.

> **Lab-only setup:** Elasticsearch security is disabled and the services are
> published without authentication. Do not expose this stack to an untrusted
> network or use it for production data.

## Architecture

Terraform provisions a dedicated Docker network. Ansible then brings up the
Compose stack on that network. The Flask demo exposes Prometheus metrics and
writes JSON logs to a shared volume; Prometheus scrapes metrics, while Filebeat
ships logs through Logstash to Elasticsearch for exploration in Kibana.
Grafana is preconfigured with Prometheus and a small dashboard.

See [docs/architecture.md](docs/architecture.md) for the architecture,
workflow, and lab exercises.

## Prerequisites

- Docker Engine/Desktop with the Docker Compose v2 plugin
- Terraform 1.5+
- Ansible 2.15+ and the `community.docker` collection
- Python 3.11+ and Node.js 20+ (for local tests)

The ELK stack is memory-intensive. Allow Docker at least 4 GB of memory; the
Elasticsearch container also requires `vm.max_map_count >= 262144` on Linux.
On Windows, run Terraform and Ansible from WSL2 with Docker Desktop's WSL
integration enabled.

## Start the lab

From the repository root:

```sh
terraform -chdir=terraform init
terraform -chdir=terraform apply
ansible-galaxy collection install -r ansible/requirements.yml
ansible-playbook -i ansible/inventory.ini ansible/site.yml
```

Terraform creates the network; Ansible starts the services. Tear down the
Compose stack before removing the network:

```sh
ansible-playbook -i ansible/inventory.ini ansible/site.yml --tags stop
terraform -chdir=terraform destroy
```

The named `app-logs` volume is retained when the stack is stopped. To remove
stored logs as well, run `docker volume rm lab3_app-logs` after stopping the
stack.

## Service endpoints

| Service | URL | Credentials |
|---|---|---|
| Demo app | http://localhost:5000 | None |
| Prometheus | http://localhost:9090 | None |
| Grafana | http://localhost:3000 | `admin` / `lab3admin` |
| Kibana | http://localhost:5601 | None |

Grafana's `Demo Service` dashboard visualizes request rate and latency. In
Kibana, create a data view matching `lab3-*` to explore app logs.

## Verify and experiment

Run Python tests:

```sh
python -m pip install -r requirements-dev.txt
python -m pytest
```

Run browser tests (the app must be running):

```sh
cd browser-tests
npm install
npx playwright install chromium
npm test
```

Run the load test against the running app:

```sh
k6 run -e BASE_URL=http://localhost:5000 loadtest/smoke.js
```

Toggle the greeting feature flag by changing `FEATURE_GREETING_V2` in
`docker-compose.yml`, then apply the Compose stack again with Ansible.

## CI security and quality gates

The workflow in `.github/workflows/ci.yml` runs Python tests, Playwright
browser tests, a short k6 load test, Bandit, `pip-audit`, Trivy filesystem
scanning, Checkov, Terraform formatting/validation, and Ansible syntax checks.
CI failures block the workflow; review and resolve findings before merging.

## Troubleshooting

- **Elasticsearch exits:** allocate more Docker memory and, on Linux, set
  `vm.max_map_count=262144`.
- **Compose cannot find its network:** run `terraform apply` before Ansible.
- **Kibana has no logs:** wait for the services to become healthy, generate
  requests to the demo app, and verify Filebeat and Logstash container logs.
- **Terraform cannot connect to Docker:** ensure the Docker daemon is running
  and that your user can access its socket.
