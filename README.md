# 📊 Grafana Monitoring Stack Demo

This project sets up a local monitoring environment using **Grafana**, **Prometheus**, **Node Exporter**, and a **simulated metrics app** with Docker Compose.

It’s ideal for:
- Demonstrating Grafana features (templating, drilldowns, annotations)
- Simulating real-time metrics
- Local testing and learning observability tools

---

## 🧱 Stack Components

| Component       | Role                                 | URL                  |
|----------------|--------------------------------------|----------------------|
| **Prometheus**  | Metrics scraping & storage            | http://localhost:9090 |
| **Grafana**     | Dashboards & visualization            | http://localhost:3000 |
| **Node Exporter** | System-level metrics (CPU, mem, disk) | http://localhost:9100/metrics |
| **App Metrics** | Simulated application metrics         | http://localhost:8000/metrics |

---

## 🚀 Quick Start

### 1. Prerequisites

- Docker & Docker Compose installed
- Free ports: `3000`, `9090`, `9100`, `8000`

### 2. Folder Structure
grafana-demo/
├── docker-compose.yml
├── prometheus.yml
├── app_metrics.py
├── grafana/
│   └── provisioning/
│       ├── datasources/
│       │   └── datasource.yaml
│       └── dashboards/
│           ├── dashboards.yaml
│           └── demo-dashboard.json
├── README.md

### 3. Start the Stack

```bash
docker-compose up