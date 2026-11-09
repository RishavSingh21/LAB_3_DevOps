import json
import logging
import os
import time
from logging.handlers import RotatingFileHandler

from flask import Flask, jsonify, render_template_string, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

app = Flask(__name__)

REQUESTS = Counter(
    "demo_http_requests_total",
    "HTTP requests served by the demo application",
    ("method", "status"),
)
LATENCY = Histogram(
    "demo_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ("method",),
)


class JsonFormatter(logging.Formatter):
    def format(self, record):
        event = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "event_fields"):
            event.update(record.event_fields)
        return json.dumps(event)


def configure_logging():
    logger = logging.getLogger("demo")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)
    formatter = JsonFormatter()
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    try:
        file_handler = RotatingFileHandler(
            os.getenv("APP_LOG_FILE", "/var/log/lab3/app.jsonl"),
            maxBytes=1_000_000,
            backupCount=2,
        )
    except OSError:
        logger.exception("Could not open the shared log file")
        raise
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger


logger = logging.getLogger("demo")


@app.before_request
def begin_request():
    request.start_time = time.perf_counter()


@app.after_request
def record_request(response):
    if request.path not in ("/metrics", "/health"):
        elapsed = time.perf_counter() - request.start_time
        REQUESTS.labels(request.method, str(response.status_code)).inc()
        LATENCY.labels(request.method).observe(elapsed)
        logger.info(
            "http_request",
            extra={
                "event_fields": {
                    "method": request.method,
                    "path": request.path,
                    "status": response.status_code,
                    "duration_seconds": round(elapsed, 6),
                }
            },
        )
    return response


@app.get("/")
def index():
    return render_template_string(
        """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Lab 3 Demo</title></head>
<body><main><h1>Lab 3 Demo Service</h1>
<p id="greeting" aria-live="polite">Loading greeting...</p>
<button id="refresh" type="button">Refresh greeting</button></main>
<script>
async function loadGreeting() {
  const response = await fetch('/api/greeting');
  if (!response.ok) throw new Error('Greeting request failed');
  const data = await response.json();
  document.querySelector('#greeting').textContent = data.message;
}
document.querySelector('#refresh').addEventListener('click', loadGreeting);
loadGreeting().catch(() => {
  document.querySelector('#greeting').textContent = 'Greeting unavailable';
});
</script></body></html>"""
    )


@app.get("/api/greeting")
def greeting():
    version_two = os.getenv("FEATURE_GREETING_V2", "false").lower() == "true"
    message = "Hello from Lab 3, version 2!" if version_two else "Hello from Lab 3!"
    return jsonify(message=message, feature_enabled=version_two)


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.get("/metrics")
def metrics():
    from flask import Response

    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    configure_logging()
    app.run(host="0.0.0.0", port=5000)  # nosec B104 - bind the container interface.
