from flask import Flask, Response
from prometheus_client import Counter, Gauge, Histogram, Summary, generate_latest, CollectorRegistry
import os
import time
import threading
import random
import sys # Import sys for stderr printing

app = Flask(__name__)
registry = CollectorRegistry()

APP_NAME = os.environ.get("APP_NAME", "default-app")
REGIONS = ["us-east", "us-west", "eu-central"]
STATUSES = ["success", "failure"]
METHODS = ["GET", "POST", "PUT", "DELETE"] # Added more methods for variety
ENDPOINTS = ["/", "/health", "/orders", "/metrics", "/data", "/admin"] # Added more endpoints

# --- Prometheus Metrics Definitions ---
# All metrics are registered with the custom registry.

# Counter: Increments for each HTTP request
http_requests = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["app", "method", "endpoint", "status_code"], # Added status_code label
    registry=registry
)

# Counter: Tracks total orders processed with status and region
orders_total = Counter(
    "orders_total",
    "Total orders processed",
    ["app", "region", "status"],
    registry=registry
)

# Counter: Tracks different types of errors
errors_total = Counter(
    "errors_total",
    "Total error count by type",
    ["app", "error_type"],
    registry=registry
)

# Gauge: Represents current state, like in-progress orders
in_progress_orders = Gauge(
    "in_progress_orders",
    "Current in-progress orders",
    ["app", "region"],
    registry=registry
)

# Gauge: Example for current active users (randomly changing)
active_users = Gauge(
    "active_users",
    "Current number of active users",
    ["app"],
    registry=registry
)

# Histogram: Samples observations and counts them in configurable buckets (e.g., request latency)
request_latency = Histogram(
    "http_request_duration_seconds",
    "Histogram of HTTP request durations",
    ["app", "endpoint", "method"], # Added method label for more detail
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0], # More granular buckets
    registry=registry
)

# Summary: Samples observations and provides quantiles (e.g., order processing time)
order_processing_time = Summary(
    "order_processing_time_seconds",
    "Summary of order processing time",
    ["app", "region"],
    registry=registry
)

# --- Flask Routes ---

@app.route("/")
def index():
    start_time = time.time()
    method = "GET"
    endpoint = "/"
    status_code = random.choice([200, 200, 200, 404, 500]) # Simulate different status codes

    http_requests.labels(app=APP_NAME, method=method, endpoint=endpoint, status_code=status_code).inc()
    
    # Simulate some work
    time.sleep(random.uniform(0.01, 0.1))

    latency = time.time() - start_time
    request_latency.labels(app=APP_NAME, endpoint=endpoint, method=method).observe(latency)

    if status_code == 404:
        errors_total.labels(app=APP_NAME, error_type="not_found").inc()
        return "Not Found", 404
    elif status_code == 500:
        errors_total.labels(app=APP_NAME, error_type="server_error").inc()
        return "Internal Server Error", 500
    return f"Hello from {APP_NAME}!", 200

@app.route("/health")
def health():
    start_time = time.time()
    method = "GET"
    endpoint = "/health"
    status_code = 200 # Health checks are usually successful

    http_requests.labels(app=APP_NAME, method=method, endpoint=endpoint, status_code=status_code).inc()
    
    # Simulate quick check
    time.sleep(random.uniform(0.001, 0.005))

    latency = time.time() - start_time
    request_latency.labels(app=APP_NAME, endpoint=endpoint, method=method).observe(latency)
    return "OK", 200

@app.route("/orders", methods=["GET", "POST"])
def orders():
    start_time = time.time()
    method = random.choice(["GET", "POST"])
    endpoint = "/orders"
    region = random.choice(REGIONS)
    status = random.choice(STATUSES)
    status_code = 200 if status == "success" else 500

    http_requests.labels(app=APP_NAME, method=method, endpoint=endpoint, status_code=status_code).inc()
    
    # Simulate order processing
    processing_duration = random.uniform(0.1, 1.5)
    time.sleep(processing_duration)

    orders_total.labels(app=APP_NAME, region=region, status=status).inc()
    order_processing_time.labels(app=APP_NAME, region=region).observe(processing_duration)

    if status == "failure":
        errors_total.labels(app=APP_NAME, error_type="order_processing_failure").inc()
        return f"Order processing failed in {region}", 500
    
    latency = time.time() - start_time
    request_latency.labels(app=APP_NAME, endpoint=endpoint, method=method).observe(latency)
    return f"Order processed successfully in {region}", 200

@app.route("/error")
def simulate_error():
    start_time = time.time()
    method = "GET"
    endpoint = "/error"
    error_type = random.choice(["database_connection", "api_timeout", "invalid_input"])
    status_code = 500

    http_requests.labels(app=APP_NAME, method=method, endpoint=endpoint, status_code=status_code).inc()
    errors_total.labels(app=APP_NAME, error_type=error_type).inc()

    # Simulate error condition
    time.sleep(random.uniform(0.05, 0.2))

    latency = time.time() - start_time
    request_latency.labels(app=APP_NAME, endpoint=endpoint, method=method).observe(latency)
    return f"Simulated {error_type} error", 500

@app.route("/metrics")
def metrics():
    # This endpoint exposes the Prometheus metrics in a format that Prometheus can scrape.
    return Response(generate_latest(registry), mimetype="text/plain")

# --- Background Metric Generation ---
def generate_random_metrics():
    """
    Simulates various metric updates in the background to show dynamic data
    even without direct HTTP requests to all endpoints.
    """
    while True:
        # Simulate in-progress orders fluctuating
        for region in REGIONS:
            current_in_progress = random.randint(0, 50)
            in_progress_orders.labels(app=APP_NAME, region=region).set(current_in_progress)
            
            # Simulate some background order completions/failures
            if random.random() < 0.2: # 20% chance to complete/fail an order
                orders_total.labels(app=APP_NAME, region=region, status=random.choice(STATUSES)).inc()
                order_processing_time.labels(app=APP_NAME, region=region).observe(random.uniform(0.05, 1.0))

        # Simulate active users fluctuating
        active_users.labels(app=APP_NAME).set(random.randint(5, 200))

        # Simulate background errors (e.g., cron jobs, internal services)
        if random.random() < 0.1: # 10% chance of a background error
            errors_total.labels(app=APP_NAME, error_type=random.choice(["background_job_fail", "db_connection_pool_exhausted"])).inc()

        # Simulate latency for other endpoints not hit by direct routes
        for endpoint in ENDPOINTS:
            if endpoint not in ["/", "/health", "/orders", "/error", "/metrics"]: # Avoid double counting for routed ones
                method = random.choice(METHODS)
                latency = random.uniform(0.01, 0.5)
                request_latency.labels(app=APP_NAME, endpoint=endpoint, method=method).observe(latency)
                http_requests.labels(app=APP_NAME, method=method, endpoint=endpoint, status_code=200).inc() # Assume success for background

        time.sleep(random.uniform(1, 5)) # Update metrics every 1-5 seconds

if __name__ == "__main__":
    # Start the background thread for metric generation
    metrics_thread = threading.Thread(target=generate_random_metrics, daemon=True)
    metrics_thread.start()

    # Run the Flask application
    # IMPORTANT FIX: Bind to '0.0.0.0' to be accessible from outside the container
    print(f"Starting Flask app '{APP_NAME}' on http://0.0.0.0:5000", file=sys.stderr)
    print("Metrics available at http://0.0.0.0:5000/metrics", file=sys.stderr)
    app.run(host='0.0.0.0', debug=True, use_reloader=False)