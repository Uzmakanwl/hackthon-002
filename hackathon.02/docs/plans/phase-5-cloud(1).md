# Phase 5: Advanced Cloud Deployment — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Deploy the todo app to DigitalOcean DOKS with event-driven architecture using Kafka (pub/sub via Dapr), Redis state store, and separate microservices for notifications, recurrence, and audit logging.

**Architecture:** Backend publishes domain events to Kafka via Dapr pub/sub. Three consumer services handle events: Notification (reminders), Recurrence (auto-scheduling), and Audit (logging). Dapr sidecars manage pub/sub, state (Redis), and service invocation. Helm charts deploy everything to DOKS. CI/CD via GitHub Actions.

**Tech Stack:** Python 3.12+, FastAPI, SQLModel, Apache Kafka (via Dapr), Dapr, Redis, Docker, Helm 3, DigitalOcean DOKS, Terraform (optional), GitHub Actions

---

## Task 1: Backend — Base CRUD Layer (From Phase 2)

**Files:**
- Create: All backend files under `phase-5-cloud/backend/`

**Step 1: Copy Phase 2 backend code**

Adapt all CRUD code. Config should include Kafka and Dapr settings:

```python
# app/config.py additions
self.KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
self.DAPR_HTTP_PORT: int = int(os.getenv("DAPR_HTTP_PORT", "3500"))
self.DAPR_GRPC_PORT: int = int(os.getenv("DAPR_GRPC_PORT", "50001"))
```

**Step 2: Verify with tests**

Run: `cd phase-5-cloud/backend && python -m pytest -v`
Expected: All CRUD tests PASS

**Step 3: Commit**

```bash
git add phase-5-cloud/backend/
git commit -m "phase-5: feat: add backend base CRUD layer"
```

---

## Task 2: Event Schemas and Producer

**Files:**
- Create: `phase-5-cloud/backend/app/events/schemas.py`
- Create: `phase-5-cloud/backend/app/events/producer.py`
- Test: `phase-5-cloud/backend/tests/test_events.py`

**Step 1: Write the failing test**

```python
# tests/test_events.py
import pytest
from datetime import datetime
from app.events.schemas import TaskEvent, EventType


class TestEventSchemas:
    def test_event_creation(self):
        event = TaskEvent(
            event_type=EventType.TASK_CREATED,
            task_id="abc-123",
            payload={"title": "Buy groceries", "priority": "high"},
        )
        assert event.event_type == EventType.TASK_CREATED
        assert event.task_id == "abc-123"
        assert event.timestamp is not None

    def test_event_types(self):
        assert EventType.TASK_CREATED.value == "task.created"
        assert EventType.TASK_UPDATED.value == "task.updated"
        assert EventType.TASK_COMPLETED.value == "task.completed"
        assert EventType.TASK_DELETED.value == "task.deleted"
        assert EventType.REMINDER_DUE.value == "task.reminder.due"
        assert EventType.RECURRING_TRIGGERED.value == "task.recurring.triggered"

    def test_event_serialization(self):
        event = TaskEvent(
            event_type=EventType.TASK_COMPLETED,
            task_id="abc-123",
            payload={"title": "Done"},
        )
        data = event.model_dump()
        assert "event_type" in data
        assert "task_id" in data
        assert "timestamp" in data
        assert "payload" in data
```

**Step 2: Run test to verify it fails**

Run: `cd phase-5-cloud/backend && python -m pytest tests/test_events.py -v`
Expected: FAIL

**Step 3: Implement event schemas**

```python
# app/events/schemas.py
"""Event schemas for Kafka domain events."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Domain event types."""
    TASK_CREATED = "task.created"
    TASK_UPDATED = "task.updated"
    TASK_COMPLETED = "task.completed"
    TASK_DELETED = "task.deleted"
    REMINDER_DUE = "task.reminder.due"
    RECURRING_TRIGGERED = "task.recurring.triggered"


class TaskEvent(BaseModel):
    """A domain event for the task system."""
    event_type: EventType
    task_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    payload: dict[str, Any] = {}
```

**Step 4: Implement producer**

```python
# app/events/producer.py
"""Event producer — publishes domain events via Dapr pub/sub."""

import httpx
import json
import logging

from app.config import get_settings
from app.events.schemas import TaskEvent

logger = logging.getLogger(__name__)

PUBSUB_NAME = "pubsub"
TOPIC_NAME = "task-events"


async def publish_event(event: TaskEvent) -> bool:
    """Publish a domain event to Kafka via Dapr pub/sub.

    Args:
        event: The TaskEvent to publish.

    Returns:
        True if published successfully, False otherwise.
    """
    settings = get_settings()
    dapr_url = f"http://localhost:{settings.DAPR_HTTP_PORT}/v1.0/publish/{PUBSUB_NAME}/{TOPIC_NAME}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                dapr_url,
                json=event.model_dump(mode="json"),
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            logger.info(f"Published event: {event.event_type.value} for task {event.task_id}")
            return True
    except Exception as exc:
        logger.error(f"Failed to publish event: {exc}")
        return False
```

**Step 5: Run test to verify it passes**

Run: `cd phase-5-cloud/backend && python -m pytest tests/test_events.py -v`
Expected: PASS (schema tests only — producer requires Dapr)

**Step 6: Commit**

```bash
git add phase-5-cloud/backend/app/events/
git add phase-5-cloud/backend/tests/test_events.py
git commit -m "phase-5: feat: add event schemas and Dapr pub/sub producer"
```

---

## Task 3: Event Consumers — Notification, Recurrence, Audit

**Files:**
- Create: `phase-5-cloud/backend/app/events/consumer.py`

**Step 1: Implement consumer.py**

```python
# app/events/consumer.py
"""Event consumers — handle domain events from Kafka via Dapr."""

import logging
from fastapi import APIRouter
from pydantic import BaseModel

from app.events.schemas import EventType

logger = logging.getLogger(__name__)

router = APIRouter(tags=["events"])


class DaprEvent(BaseModel):
    """Dapr CloudEvent wrapper."""
    data: dict
    datacontenttype: str = "application/json"
    id: str = ""
    source: str = ""
    specversion: str = "1.0"
    type: str = ""


@router.post("/events/task-events")
async def handle_task_event(event: DaprEvent):
    """Dapr subscription handler for task events.

    Routes events to the appropriate consumer based on event_type.
    """
    event_data = event.data
    event_type = event_data.get("event_type", "")
    task_id = event_data.get("task_id", "")

    logger.info(f"Received event: {event_type} for task {task_id}")

    match event_type:
        case EventType.REMINDER_DUE:
            await _handle_reminder(event_data)
        case EventType.TASK_COMPLETED:
            await _handle_completion(event_data)
        case _:
            await _handle_audit(event_data)

    return {"status": "ok"}


async def _handle_reminder(event_data: dict) -> None:
    """Notification consumer — send reminder for due tasks."""
    task_id = event_data.get("task_id")
    payload = event_data.get("payload", {})
    title = payload.get("title", "Unknown task")
    logger.info(f"REMINDER: Task '{title}' (ID: {task_id}) is due!")
    # TODO: Send push notification, email, or webhook


async def _handle_completion(event_data: dict) -> None:
    """Recurrence consumer — create next occurrence if recurring."""
    task_id = event_data.get("task_id")
    payload = event_data.get("payload", {})
    is_recurring = payload.get("is_recurring", False)

    if is_recurring:
        recurrence_rule = payload.get("recurrence_rule")
        logger.info(f"RECURRENCE: Creating next {recurrence_rule} occurrence for task {task_id}")
        # TODO: Call recurrence service to create next task


async def _handle_audit(event_data: dict) -> None:
    """Audit consumer — log all events for observability."""
    event_type = event_data.get("event_type")
    task_id = event_data.get("task_id")
    logger.info(f"AUDIT: {event_type} — Task {task_id} — {event_data.get('payload', {})}")
```

**Step 2: Wire consumer router into main.py**

```python
# Add to app/main.py:
from app.events.consumer import router as events_router
app.include_router(events_router)
```

**Step 3: Commit**

```bash
git add phase-5-cloud/backend/app/events/consumer.py
git add phase-5-cloud/backend/app/main.py
git commit -m "phase-5: feat: add event consumers for notification, recurrence, and audit"
```

---

## Task 4: Wire Events Into Task Service

**Files:**
- Modify: `phase-5-cloud/backend/app/services/task_service.py`

**Step 1: Add event publishing to CRUD operations**

After each CRUD operation, publish the appropriate event:

```python
# Add to task_service.py — after create_task:
from app.events.producer import publish_event
from app.events.schemas import TaskEvent, EventType

# In create_task, after session.commit():
await publish_event(TaskEvent(
    event_type=EventType.TASK_CREATED,
    task_id=task.id,
    payload={"title": task.title, "priority": task.priority.value},
))

# In toggle_complete, when completing:
await publish_event(TaskEvent(
    event_type=EventType.TASK_COMPLETED,
    task_id=task.id,
    payload={
        "title": task.title,
        "is_recurring": task.is_recurring,
        "recurrence_rule": task.recurrence_rule,
    },
))

# Similar for update and delete
```

**Note:** Make route handlers `async def` and add `await` for event publishing. Wrap publish calls in try/except so CRUD operations succeed even if event publishing fails.

**Step 2: Run tests**

Run: `cd phase-5-cloud/backend && python -m pytest -v`
Expected: All CRUD tests still PASS (events fail silently without Dapr)

**Step 3: Commit**

```bash
git add phase-5-cloud/backend/app/services/task_service.py
git commit -m "phase-5: feat: wire domain events into task service CRUD operations"
```

---

## Task 5: Dapr Integration — Pub/Sub and State Store

**Files:**
- Create: `phase-5-cloud/backend/app/dapr/pubsub.py`
- Create: `phase-5-cloud/backend/app/dapr/state.py`

**Step 1: Implement Dapr pub/sub helper**

```python
# app/dapr/pubsub.py
"""Dapr pub/sub helper for publishing and subscribing to events."""

import httpx
from app.config import get_settings


async def publish_to_topic(pubsub_name: str, topic: str, data: dict) -> bool:
    """Publish a message to a Dapr pub/sub topic."""
    settings = get_settings()
    url = f"http://localhost:{settings.DAPR_HTTP_PORT}/v1.0/publish/{pubsub_name}/{topic}"
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data)
        return response.status_code == 204


def get_subscription_routes() -> list[dict]:
    """Return Dapr subscription configuration."""
    return [
        {
            "pubsubname": "pubsub",
            "topic": "task-events",
            "route": "/events/task-events",
        }
    ]
```

**Step 2: Implement Dapr state store helper**

```python
# app/dapr/state.py
"""Dapr state store helper — Redis-backed caching."""

import httpx
from app.config import get_settings

STORE_NAME = "statestore"


async def get_state(key: str) -> dict | None:
    """Get a value from Dapr state store."""
    settings = get_settings()
    url = f"http://localhost:{settings.DAPR_HTTP_PORT}/v1.0/state/{STORE_NAME}/{key}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code == 200 and response.content:
            return response.json()
    return None


async def save_state(key: str, value: dict) -> bool:
    """Save a value to Dapr state store."""
    settings = get_settings()
    url = f"http://localhost:{settings.DAPR_HTTP_PORT}/v1.0/state/{STORE_NAME}"
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=[{"key": key, "value": value}])
        return response.status_code == 204


async def delete_state(key: str) -> bool:
    """Delete a value from Dapr state store."""
    settings = get_settings()
    url = f"http://localhost:{settings.DAPR_HTTP_PORT}/v1.0/state/{STORE_NAME}/{key}"
    async with httpx.AsyncClient() as client:
        response = await client.delete(url)
        return response.status_code == 204
```

**Step 3: Add Dapr subscription endpoint to main.py**

```python
# Add to app/main.py:
from app.dapr.pubsub import get_subscription_routes

@app.get("/dapr/subscribe")
def subscribe():
    """Dapr subscription endpoint — tells Dapr which topics to route."""
    return get_subscription_routes()
```

**Step 4: Commit**

```bash
git add phase-5-cloud/backend/app/dapr/
git commit -m "phase-5: feat: add Dapr pub/sub and state store helpers"
```

---

## Task 6: Frontend — App Code (From Phase 2)

**Files:**
- Create: All frontend files under `phase-5-cloud/frontend/`

**Step 1: Copy Phase 2 frontend code**

Same as Phase 4 — ensure standalone output for Docker.

**Step 2: Commit**

```bash
git add phase-5-cloud/frontend/
git commit -m "phase-5: feat: add frontend app code"
```

---

## Task 7: Docker — Dockerfiles and Compose

**Files:**
- Create: `phase-5-cloud/docker/Dockerfile.backend`
- Create: `phase-5-cloud/docker/Dockerfile.frontend`
- Create: `phase-5-cloud/docker/nginx.conf`
- Create: `phase-5-cloud/docker/docker-compose.yml`

**Step 1: Write Dockerfiles (same as Phase 4)**

Copy from Phase 4 plan.

**Step 2: Write docker-compose.yml with Kafka + Redis**

```yaml
version: '3.8'
services:
  backend:
    build:
      context: ../backend
      dockerfile: ../docker/Dockerfile.backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://todouser:todopass@postgres:5432/tododb
      CORS_ORIGINS: http://localhost:3000
      KAFKA_BOOTSTRAP_SERVERS: kafka:9092
    depends_on:
      postgres:
        condition: service_healthy
      kafka:
        condition: service_started

  frontend:
    build:
      context: ../frontend
      dockerfile: ../docker/Dockerfile.frontend
      args:
        NEXT_PUBLIC_API_URL: http://localhost:8000
    ports:
      - "3000:3000"

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: tododb
      POSTGRES_USER: todouser
      POSTGRES_PASSWORD: todopass
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U todouser -d tododb"]
      interval: 10s
      timeout: 5s
      retries: 5

  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  pgdata:
```

**Step 3: Test compose up**

Run: `cd phase-5-cloud/docker && docker compose up --build -d`
Expected: All services start (backend, frontend, postgres, kafka, zookeeper, redis)

**Step 4: Commit**

```bash
git add phase-5-cloud/docker/
git commit -m "phase-5: feat: add Docker config with Kafka, Redis, and Postgres"
```

---

## Task 8: Dapr Component YAMLs

**Files:**
- Create: `phase-5-cloud/k8s/dapr-components/pubsub.yaml`
- Create: `phase-5-cloud/k8s/dapr-components/statestore.yaml`
- Create: `phase-5-cloud/k8s/dapr-components/subscription.yaml`

**Step 1: Write pubsub.yaml**

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: pubsub
spec:
  type: pubsub.kafka
  version: v1
  metadata:
    - name: brokers
      value: "kafka:9092"
    - name: authRequired
      value: "false"
    - name: consumeRetryEnabled
      value: "true"
    - name: maxRetries
      value: "3"
```

**Step 2: Write statestore.yaml**

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: statestore
spec:
  type: state.redis
  version: v1
  metadata:
    - name: redisHost
      value: "redis:6379"
    - name: redisPassword
      value: ""
    - name: actorStateStore
      value: "false"
```

**Step 3: Write subscription.yaml**

```yaml
apiVersion: dapr.io/v2alpha1
kind: Subscription
metadata:
  name: task-events-subscription
spec:
  pubsubname: pubsub
  topic: task-events
  routes:
    default: /events/task-events
  scopes:
    - backend
```

**Step 4: Commit**

```bash
git add phase-5-cloud/k8s/dapr-components/
git commit -m "phase-5: feat: add Dapr component YAMLs for Kafka pub/sub and Redis state"
```

---

## Task 9: Helm Chart for DOKS

**Files:**
- Create: `phase-5-cloud/k8s/helm/todo-app/Chart.yaml`
- Create: `phase-5-cloud/k8s/helm/todo-app/values.yaml`
- Create: All templates under `phase-5-cloud/k8s/helm/todo-app/templates/`

**Step 1: Write Chart.yaml and values.yaml**

Same as Phase 4 but add Kafka, Redis, Dapr sections to values:

```yaml
# Additional values.yaml entries:
kafka:
  enabled: true
  bootstrapServers: kafka:9092

redis:
  enabled: true
  host: redis:6379

dapr:
  enabled: true
  annotations:
    dapr.io/enabled: "true"
    dapr.io/app-id: "backend"
    dapr.io/app-port: "8000"
```

**Step 2: Add Dapr annotations to backend deployment template**

```yaml
# In backend-deployment.yaml, add to pod template metadata:
{{- if .Values.dapr.enabled }}
annotations:
  dapr.io/enabled: "true"
  dapr.io/app-id: "backend"
  dapr.io/app-port: "{{ .Values.backend.port }}"
{{- end }}
```

**Step 3: Copy remaining templates from Phase 4**

Include: Services, Ingress, ConfigMap, Secret, HPA, _helpers.tpl

**Step 4: Verify Helm template renders**

Run: `helm template test phase-5-cloud/k8s/helm/todo-app/`
Expected: Valid YAML

**Step 5: Commit**

```bash
git add phase-5-cloud/k8s/helm/
git commit -m "phase-5: feat: add Helm chart for DOKS with Dapr annotations"
```

---

## Task 10: Infrastructure — Terraform and Scripts

**Files:**
- Create: `phase-5-cloud/infra/do-cluster.tf`
- Create: `phase-5-cloud/infra/setup-doks.sh`
- Create: `phase-5-cloud/scripts/deploy-doks.sh`
- Create: `phase-5-cloud/scripts/setup-kafka.sh`
- Create: `phase-5-cloud/scripts/setup-dapr.sh`

**Step 1: Write do-cluster.tf**

```hcl
terraform {
  required_providers {
    digitalocean = {
      source  = "digitalocean/terraform-provider-digitalocean"
      version = "~> 2.0"
    }
  }
}

provider "digitalocean" {
  token = var.do_token
}

variable "do_token" {
  description = "DigitalOcean API token"
  type        = string
  sensitive   = true
}

variable "cluster_name" {
  default = "todo-cluster"
}

variable "region" {
  default = "nyc1"
}

resource "digitalocean_kubernetes_cluster" "todo" {
  name    = var.cluster_name
  region  = var.region
  version = "1.28.2-do.0"

  node_pool {
    name       = "default-pool"
    size       = "s-2vcpu-4gb"
    node_count = 2
  }
}

output "cluster_id" {
  value = digitalocean_kubernetes_cluster.todo.id
}

output "endpoint" {
  value = digitalocean_kubernetes_cluster.todo.endpoint
}

output "kubeconfig" {
  value     = digitalocean_kubernetes_cluster.todo.kube_config[0].raw_config
  sensitive = true
}
```

**Step 2: Write setup scripts**

```bash
# scripts/setup-dapr.sh
#!/bin/bash
set -euo pipefail
echo "=== Installing Dapr on Kubernetes ==="
dapr init -k --wait
dapr status -k
echo "=== Dapr installed ==="
```

```bash
# scripts/setup-kafka.sh
#!/bin/bash
set -euo pipefail
echo "=== Installing Kafka (Strimzi) on Kubernetes ==="
kubectl create namespace kafka || true
kubectl apply -f https://strimzi.io/install/latest?namespace=kafka -n kafka
# Wait for operator
kubectl wait deployment/strimzi-cluster-operator -n kafka --for=condition=Available --timeout=120s
echo "=== Strimzi operator installed ==="
echo "Apply your Kafka cluster YAML next."
```

```bash
# scripts/deploy-doks.sh
#!/bin/bash
set -euo pipefail
echo "=== Deploying Todo App to DOKS ==="

# Build and push images to registry
REGISTRY=${REGISTRY:-"registry.digitalocean.com/todo-app"}

docker build -f docker/Dockerfile.backend -t $REGISTRY/backend:latest backend/
docker build -f docker/Dockerfile.frontend -t $REGISTRY/frontend:latest frontend/
docker push $REGISTRY/backend:latest
docker push $REGISTRY/frontend:latest

# Apply Dapr components
kubectl apply -f k8s/dapr-components/

# Deploy with Helm
helm upgrade --install todo-app k8s/helm/todo-app/ \
    --set backend.image.repository=$REGISTRY/backend \
    --set frontend.image.repository=$REGISTRY/frontend \
    --set database.url="$DATABASE_URL" \
    --wait --timeout 180s

kubectl get pods
echo "=== Deployment complete ==="
```

**Step 3: Make scripts executable**

Run: `chmod +x phase-5-cloud/scripts/*.sh phase-5-cloud/infra/*.sh`

**Step 4: Commit**

```bash
git add phase-5-cloud/infra/ phase-5-cloud/scripts/
git commit -m "phase-5: feat: add Terraform, DOKS setup, and deployment scripts"
```

---

## Task 11: README and Final Polish

**Files:**
- Create: `phase-5-cloud/README.md`

**Step 1: Write comprehensive README**

Cover:
- Architecture diagram (Mermaid: Frontend → Backend → Kafka → Consumers, with Dapr sidecars, Redis, PostgreSQL)
- Prerequisites (doctl, Docker, Helm, kubectl, dapr CLI, Terraform)
- Local dev (Docker Compose with Kafka + Redis)
- DOKS cluster setup (Terraform or manual doctl)
- Kafka setup (Strimzi)
- Dapr setup and component reference
- Event-driven architecture explanation
  - Event types table
  - Consumer responsibilities
- Deployment pipeline (CI/CD with GitHub Actions)
- Monitoring and observability
- Troubleshooting

**Step 2: End-to-end verification plan**

1. `docker compose up` — local dev with all services
2. Create a task via API → verify `task.created` event in logs
3. Complete a recurring task → verify new task auto-created
4. Deploy to DOKS → verify pods, services, ingress

**Step 3: Commit**

```bash
git add phase-5-cloud/README.md
git commit -m "phase-5: docs: add README with DOKS, Kafka, Dapr architecture and setup"
```

---

## Summary

| Task | What |
|------|------|
| 1 | Backend base CRUD layer |
| 2 | Event schemas + Kafka producer |
| 3 | Event consumers (notification, recurrence, audit) |
| 4 | Wire events into task service |
| 5 | Dapr pub/sub + state store helpers |
| 6 | Frontend app code |
| 7 | Docker (Dockerfiles + Compose with Kafka/Redis) |
| 8 | Dapr component YAMLs |
| 9 | Helm chart for DOKS |
| 10 | Terraform + deployment scripts |
| 11 | README + final polish |

**Total: 11 tasks. ~10 automated tests + extensive manual/integration testing across 11 tasks.**
