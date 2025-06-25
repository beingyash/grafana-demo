from flask import Flask, Response
from prometheus_client import Counter, generate_latest, CollectorRegistry
import os
import time
import threading
import random

app = Flask(__name__)
registry = CollectorRegistry()

APP_NAME = os.environ.get("APP_NAME", "default-app")
REGIONS = ["us-east", "us-west", "eu-central"]
STATUSES = ["success", "failure"]
METHODS = ["GET", "POST"]
ENDPOINTS = ["/", "/health", "/orders", "/metrics"]

# Metrics with rich labels
http_requests = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["app", "method", "endpoint"],
    registry=registry
)

orders_total = Counter(
    "orders_total",
    "Total orders processed",
    ["app", "region", "status"],
    registry=registry
)

@app.route("/")
def index():
    http_requests.labels(app=APP_NAME, method="GET", endpoint="/").inc()
    return f"Hello from {APP_NAME}"

@app.route("/orders")
def orders():
    region = random.choice(REGIONS)
    status = random.choice(STATUSES)
    orders_total.labels(app=APP_NAME, region=region, status=status).inc()
    http_requests.labels(app=APP_NAME, method="GET", endpoint="/orders").inc()
    return f"Order status: {status} in {region}"

@app.route("/metrics")
def metrics():
    return Response(generate_latest(registry), mimetype="text/plain")


def background_load():
    """Generate synthetic traffic every few seconds."""
    while True:
        ep = random.choice(ENDPOINTS[:-1])  # exclude /metrics
        method = random.choice(METHODS)
        http_requests.labels(app=APP_NAME, method=method, endpoint=ep).inc()
        if ep == "/orders":
            orders_total.labels(
                app=APP_NAME,
                region=random.choice(REGIONS),
                status=random.choice(STATUSES)
            ).inc()
        time.sleep(random.uniform(0.5, 2.0))


if __name__ == "__main__":
    # Start background thread
    threading.Thread(target=background_load, daemon=True).start()
    app.run(host="0.0.0.0", port=8000)