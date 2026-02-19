# Phase 5 -- Advanced Cloud Deployment

Event-driven Todo App deployed to DigitalOcean DOKS with Kafka (via Dapr pub/sub), Redis state store, and dedicated event consumers.

## Overview

Phase 5 evolves the Todo List application into a fully event-driven, cloud-deployed system. Every task lifecycle operation (create, update, complete, delete) publishes a domain event to Kafka through Dapr's pub/sub building block. Three dedicated consumers -- notification, recurrence, and audit -- process these events independently. The backend exposes a Dapr subscription discovery endpoint and receives CloudEvents through a consumer router. Redis provides distributed state caching via Dapr's state store abstraction. The entire stack is deployable to DigitalOcean Kubernetes Service (DOKS) via Helm charts, with Docker Compose available for local development.

**Stack:** FastAPI, Next.js 14, PostgreSQL, Apache Kafka, Redis, Dapr, Docker, Helm, DigitalOcean DOKS, Terraform

## Architecture

```mermaid
graph TB
    subgraph "DigitalOcean DOKS Cluster"
        subgraph "Application Layer"
            FE["Next.js Frontend<br/>(nginx :80)"]
            BE["FastAPI Backend<br/>(:8000)"]
        end

        subgraph "Dapr Sidecar"
            DS["Dapr Sidecar<br/>(:3500)<br/>app-id: todo-backend"]
        end

        subgraph "Event Bus"
            KAFKA["Apache Kafka<br/>(:9092)"]
            ZK["Zookeeper<br/>(:2181)"]
        end

        subgraph "Event Consumers (in-process)"
            NC["Notification Handler<br/>task.reminder.due"]
            RC["Recurrence Handler<br/>task.completed"]
            AC["Audit Handler<br/>all other events"]
        end

        subgraph "Data Layer"
            PG[("PostgreSQL<br/>(:5432)")]
            REDIS[("Redis<br/>(:6379)")]
        end

        FE -->|"HTTP"| BE
        BE -->|"publish_event()"| DS
        DS -->|"Dapr Pub/Sub"| KAFKA
        KAFKA -->|"CloudEvent"| BE
        BE --> NC
        BE --> RC
        BE --> AC
        DS -->|"State Store"| REDIS
        BE -->|"SQLModel ORM"| PG
        KAFKA --> ZK
    end

    subgraph "Ingress"
        ING["NGINX Ingress<br/>todo.local"]
    end

    USER((User)) --> ING
    ING -->|"/"| FE
    ING -->|"/api/*"| BE
```

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Docker & Docker Compose | 24+ | Container builds and local dev |
| kubectl | 1.28+ | Kubernetes CLI |
| Helm | 3.13+ | Chart-based deployment |
| Dapr CLI | 1.12+ | Dapr runtime installation |
| doctl | Latest | DigitalOcean CLI (DOKS setup) |
| Terraform | 1.5+ | Infrastructure provisioning (optional) |
| Node.js | 20+ | Frontend build |
| Python | 3.12+ | Backend runtime |

## Quick Start (Docker Compose)

Start all six services locally with a single command:

```bash
cd docker
docker compose up --build
```

| Service | URL | Notes |
|---------|-----|-------|
| Frontend | http://localhost:3000 | Next.js static export via nginx |
| Backend API | http://localhost:8000 | FastAPI with auto-reload |
| Swagger Docs | http://localhost:8000/docs | Interactive API documentation |
| ReDoc | http://localhost:8000/redoc | Alternative API docs |
| Kafka | localhost:9092 | Confluent Platform 7.5.0 |
| Redis | localhost:6379 | Redis 7 Alpine |
| PostgreSQL | localhost:5432 | PostgreSQL 16 Alpine |

Docker Compose starts: backend, frontend (nginx), postgres, zookeeper, kafka, and redis. The backend waits for postgres health checks before starting, and includes its own health check at `/health`.

## Event-Driven Architecture

### Event Types

| Event Type | Trigger | Payload |
|------------|---------|---------|
| `task.created` | Task created via POST /api/tasks | `title`, `priority` |
| `task.updated` | Task modified via PATCH /api/tasks/{id} | Changed fields only (partial diff) |
| `task.completed` | Task toggled via POST /api/tasks/{id}/complete | `status`, `is_recurring`, `recurrence_rule` |
| `task.deleted` | Task removed via DELETE /api/tasks/{id} | (empty) |
| `task.reminder.due` | Reminder time reached | `title` |
| `task.recurring.triggered` | Recurring task auto-creates next occurrence | `original_task_id`, `recurrence_rule`, `next_due_date` |

### Event Consumers

All three consumers run in-process within the FastAPI backend, receiving CloudEvents from Dapr at `POST /events/task-events`:

| Consumer | Handles | Responsibility |
|----------|---------|----------------|
| **Notification** | `task.reminder.due` | Logs reminder alerts for due tasks |
| **Recurrence** | `task.completed` | Detects recurring tasks and logs next occurrence creation |
| **Audit** | All other events | Logs every event for observability and audit trail |

### Event Flow

```
1. User creates/updates/completes/deletes a task via REST API
2. Router handler calls task_service for DB operation
3. Router handler constructs a TaskEvent and calls publish_event()
4. publish_event() POSTs to Dapr sidecar:
     http://localhost:3500/v1.0/publish/pubsub/task-events
5. Dapr publishes the event to Kafka topic "task-events"
6. Dapr delivers the event as a CloudEvent POST to /events/task-events
7. Consumer router dispatches to the appropriate handler via match/case
```

## Dapr Integration

Dapr provides two building blocks for this application:

### Pub/Sub Component (Kafka-backed)

Defined in `k8s/dapr-components/pubsub.yaml`:

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

### State Store Component (Redis-backed)

Defined in `k8s/dapr-components/statestore.yaml`:

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
```

### Subscription Routing

Dapr discovers subscriptions via two mechanisms:

1. **Programmatic** -- The backend exposes `GET /dapr/subscribe` returning:
   ```json
   [{"pubsubname": "pubsub", "topic": "task-events", "route": "/events/task-events"}]
   ```

2. **Declarative** -- `k8s/dapr-components/subscription.yaml` scoped to `todo-backend`:
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
       - todo-backend
   ```

### Dapr State Store API

The `app/dapr/state.py` module provides `get_state()`, `save_state()`, and `delete_state()` helpers that communicate with the Dapr sidecar at `http://localhost:{DAPR_HTTP_PORT}/v1.0/state/statestore/{key}`.

## DOKS Deployment

### Step 1: Create the Cluster

**Option A -- Using doctl:**

```bash
./infra/setup-doks.sh
```

This creates a 2-node DOKS cluster (`s-2vcpu-4gb` per node) in `nyc1` and saves the kubeconfig.

**Option B -- Using Terraform:**

```bash
cd infra
export TF_VAR_do_token="your-digitalocean-api-token"
terraform init
terraform plan
terraform apply
```

The Terraform configuration (`do-cluster.tf`) provisions:
- Cluster name: `todo-cluster`
- Region: `nyc1`
- Node pool: 2 nodes, `s-2vcpu-4gb` each
- Kubernetes version: `1.28.2-do.0`

### Step 2: Install Kafka (Strimzi)

```bash
./scripts/setup-kafka.sh
```

This script:
1. Installs the Strimzi Kafka Operator in the `kafka` namespace
2. Creates a single-replica Kafka cluster (`todo-kafka`) with ephemeral storage
3. Creates the `task-events` topic with 3 partitions

### Step 3: Install Dapr

```bash
./scripts/setup-dapr.sh
```

This script:
1. Installs the Dapr CLI if not present
2. Initializes Dapr on Kubernetes (runtime v1.12)
3. Applies all Dapr component YAMLs (pubsub, statestore, subscription)

### Step 4: Deploy the Application

```bash
export DATABASE_URL="postgresql://user:pass@host/tododb"
export REGISTRY="registry.digitalocean.com/todo-app"
./scripts/deploy-doks.sh
```

This script:
1. Builds and pushes Docker images to DOCR
2. Creates the `todo` namespace
3. Applies Dapr component YAMLs
4. Deploys via Helm with image and DATABASE_URL overrides
5. Verifies pods, services, and ingress

## Helm Values Reference

| Key | Default | Description |
|-----|---------|-------------|
| `backend.image` | `todo-backend:latest` | Backend Docker image |
| `backend.replicas` | `2` | Backend pod replica count |
| `backend.port` | `8000` | Backend container port |
| `backend.resources.requests.cpu` | `100m` | CPU request |
| `backend.resources.requests.memory` | `128Mi` | Memory request |
| `backend.resources.limits.cpu` | `500m` | CPU limit |
| `backend.resources.limits.memory` | `512Mi` | Memory limit |
| `backend.env.DATABASE_URL` | `""` | PostgreSQL connection (from secret) |
| `backend.env.CORS_ORIGINS` | `http://todo.local` | Allowed CORS origins |
| `backend.env.KAFKA_BOOTSTRAP_SERVERS` | `kafka:9092` | Kafka broker address |
| `backend.env.DAPR_HTTP_PORT` | `3500` | Dapr sidecar HTTP port |
| `backend.dapr.enabled` | `true` | Enable Dapr sidecar injection |
| `backend.dapr.appId` | `todo-backend` | Dapr application ID |
| `backend.dapr.appPort` | `8000` | Port Dapr forwards to |
| `frontend.image` | `todo-frontend:latest` | Frontend Docker image |
| `frontend.replicas` | `2` | Frontend pod replica count |
| `frontend.port` | `80` | Frontend container port (nginx) |
| `frontend.resources.requests.cpu` | `50m` | CPU request |
| `frontend.resources.limits.cpu` | `200m` | CPU limit |
| `frontend.resources.limits.memory` | `256Mi` | Memory limit |
| `ingress.enabled` | `true` | Enable NGINX ingress |
| `ingress.host` | `todo.local` | Ingress hostname |
| `kafka.bootstrapServers` | `kafka:9092` | Kafka broker address |
| `kafka.topics[0].name` | `task-events` | Kafka topic name |
| `kafka.topics[0].partitions` | `3` | Topic partition count |
| `dapr.enabled` | `true` | Enable Dapr components |
| `dapr.pubsubName` | `pubsub` | Dapr pub/sub component name |
| `dapr.stateStoreName` | `statestore` | Dapr state store component name |
| `redis.host` | `redis:6379` | Redis host and port |
| `hpa.enabled` | `true` | Enable horizontal pod autoscaler |
| `hpa.minReplicas` | `2` | Minimum backend replicas |
| `hpa.maxReplicas` | `10` | Maximum backend replicas |
| `hpa.targetCPUUtilization` | `70` | CPU percentage threshold for scaling |

## K8s Resources Created

| Resource | Name | Purpose |
|----------|------|---------|
| Deployment | `*-backend` | FastAPI backend (2 replicas, Dapr sidecar injected) |
| Deployment | `*-frontend` | Nginx frontend (2 replicas, static export) |
| Service | `*-backend` | ClusterIP for backend on port 8000 |
| Service | `*-frontend` | ClusterIP for frontend on port 80 |
| ConfigMap | `*-config` | Non-sensitive env: CORS origins, Kafka address, Dapr port |
| Secret | `*-secret` | DATABASE_URL (base64-encoded) |
| Ingress | `*-ingress` | Routes `/api/*` to backend, `/` to frontend |
| HPA | `*-backend-hpa` | Auto-scales backend pods (2-10) on CPU utilization |
| Dapr Component | `pubsub` | Kafka-backed pub/sub |
| Dapr Component | `statestore` | Redis-backed state store |
| Dapr Subscription | `task-events-subscription` | Routes `task-events` topic to `/events/task-events` |

## Testing

### Backend Tests

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows
pip install -r requirements.txt
pytest tests/ -v
```

30 tests total:
- **21 API tests** (`test_tasks_api.py`): health check, create (success, missing title, with due date, with recurrence), list (empty, filter by priority, search, sort, filter by tag), get (success, not found), update (partial, not found), delete (success, not found), toggle complete (pending-to-completed, completed-to-pending, recurring auto-create, not found), Dapr subscription endpoint
- **9 event tests** (`test_events.py`): EventType enum values and count, TaskEvent creation/serialization/default payload, consumer handling of created/completed/reminder events, DaprEvent model parsing

All API tests mock `publish_event` to isolate from Kafka/Dapr.

### Frontend Build Verification

```bash
cd frontend
npm install
npm run build
```

Builds as a static export (`output: "export"` in `next.config.js`), producing the `out/` directory served by nginx.

## API Endpoints

| Method | Path | Description | Events Published |
|--------|------|-------------|-----------------|
| `POST` | `/api/tasks/` | Create a new task | `task.created` |
| `GET` | `/api/tasks/` | List tasks with filter/sort/search | -- |
| `GET` | `/api/tasks/{id}` | Get a single task by UUID | -- |
| `PATCH` | `/api/tasks/{id}` | Partial update a task | `task.updated` |
| `DELETE` | `/api/tasks/{id}` | Delete a task by UUID | `task.deleted` |
| `POST` | `/api/tasks/{id}/complete` | Toggle completion status | `task.completed`, `task.recurring.triggered` (if recurring) |
| `GET` | `/health` | Kubernetes liveness/readiness probe | -- |
| `GET` | `/dapr/subscribe` | Dapr subscription discovery | -- |
| `POST` | `/events/task-events` | Dapr CloudEvent consumer endpoint | -- |

### Query Parameters for `GET /api/tasks/`

| Parameter | Type | Example | Description |
|-----------|------|---------|-------------|
| `status` | enum | `pending`, `in_progress`, `completed` | Filter by task status |
| `priority` | enum | `low`, `medium`, `high` | Filter by priority |
| `tag` | string | `work` | Filter by tag |
| `search` | string | `meeting` | Search title and description |
| `sort_by` | string | `due_date`, `priority`, `created_at`, `title` | Sort field |
| `sort_order` | string | `asc`, `desc` | Sort direction (default: `asc`) |

## Environment Variables

### Backend

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://user:pass@localhost/tododb` | PostgreSQL connection string |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed origins |
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Kafka broker address |
| `DAPR_HTTP_PORT` | `3500` | Dapr sidecar HTTP port |

Copy `backend/.env.example` to `backend/.env` and fill in values for local development.

### Frontend

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend API base URL (build-time) |

## Troubleshooting

### Docker Compose services fail to start

```bash
# Check container logs
docker compose -f docker/docker-compose.yml logs backend
docker compose -f docker/docker-compose.yml logs kafka

# Restart with a clean state
docker compose -f docker/docker-compose.yml down -v
docker compose -f docker/docker-compose.yml up --build
```

### Kafka not receiving events

```bash
# Verify Kafka is running and the topic exists
docker exec -it docker-kafka-1 kafka-topics --list --bootstrap-server localhost:9092

# Check if Dapr sidecar is running (in K8s)
kubectl get pods -n todo -o wide
kubectl logs <backend-pod> -c daprd
```

### Backend cannot connect to PostgreSQL

```bash
# Docker Compose: check postgres health
docker compose -f docker/docker-compose.yml ps

# K8s: verify the secret has a valid DATABASE_URL
kubectl get secret -n todo -o yaml
kubectl logs -l app.kubernetes.io/component=backend -n todo --tail=50
```

### Dapr sidecar not injecting on DOKS

```bash
# Verify Dapr is installed
dapr status -k

# Check annotations on the backend deployment
kubectl get deployment -n todo -o yaml | grep dapr

# Restart Dapr
dapr init -k --runtime-version 1.12 --wait
```

### Pods stuck in ImagePullBackOff on DOKS

```bash
# Verify images are pushed to DOCR
doctl registry repository list

# Check pod events
kubectl describe pod <pod-name> -n todo
```

### Port-forwarding for debugging

```bash
kubectl port-forward svc/todo-app-backend 8000:8000 -n todo
kubectl port-forward svc/todo-app-frontend 3000:80 -n todo
```

### Ingress not routing correctly

```bash
# Check ingress resource
kubectl get ingress -n todo
kubectl describe ingress -n todo

# Verify NGINX ingress controller is running
kubectl get pods -n ingress-nginx
```

## Project Structure

```
phase-5-cloud/
+-- backend/                          # FastAPI application
|   +-- app/
|   |   +-- __init__.py
|   |   +-- main.py                   # App entry, CORS, health, /dapr/subscribe
|   |   +-- config.py                 # Settings from env vars (DB, Kafka, Dapr)
|   |   +-- db.py                     # SQLModel engine + session dependency
|   |   +-- models.py                 # Task SQLModel table definition
|   |   +-- schemas.py                # Pydantic request/response schemas
|   |   +-- routers/
|   |   |   +-- tasks.py              # REST CRUD endpoints + event publishing
|   |   +-- services/
|   |   |   +-- task_service.py       # Task CRUD business logic
|   |   |   +-- recurrence_service.py # Recurring task auto-creation
|   |   +-- events/
|   |   |   +-- schemas.py            # EventType enum + TaskEvent model
|   |   |   +-- producer.py           # Dapr HTTP pub/sub publisher
|   |   |   +-- consumer.py           # CloudEvent consumer router + handlers
|   |   +-- dapr/
|   |       +-- pubsub.py             # Dapr pub/sub helper (publish_to_topic)
|   |       +-- state.py              # Dapr state store helper (get/save/delete)
|   +-- tests/
|   |   +-- test_tasks_api.py         # 21 API integration tests
|   |   +-- test_events.py            # 9 event schema + consumer tests
|   +-- alembic/                      # Database migrations
|   |   +-- env.py
|   |   +-- versions/
|   +-- alembic.ini
|   +-- requirements.txt
|   +-- .env.example
+-- frontend/                         # Next.js 14 static export
|   +-- src/
|   |   +-- app/
|   |   |   +-- layout.tsx            # Root layout
|   |   |   +-- page.tsx              # Main page
|   |   |   +-- globals.css           # Tailwind global styles
|   |   +-- components/
|   |   |   +-- FilterBar.tsx         # Status/priority/tag filters
|   |   |   +-- SearchInput.tsx       # Debounced search input
|   |   |   +-- TaskCard.tsx          # Single task display card
|   |   |   +-- TaskForm.tsx          # Create/edit task form
|   |   |   +-- TaskList.tsx          # Task list container
|   |   +-- hooks/
|   |   |   +-- useDebounce.ts        # Debounce hook for search
|   |   |   +-- useTasks.ts           # Task CRUD data fetching hook
|   |   +-- lib/
|   |   |   +-- api.ts                # Centralized API client
|   |   +-- types/
|   |       +-- task.ts               # TypeScript task interfaces
|   +-- next.config.js                # output: "export" (static)
|   +-- tailwind.config.ts
|   +-- tsconfig.json
|   +-- package.json
+-- docker/
|   +-- Dockerfile.backend            # Python multi-stage (slim, non-root)
|   +-- Dockerfile.frontend           # Node build + nginx serve
|   +-- docker-compose.yml            # 6 services: backend, frontend, postgres,
|   |                                 #   zookeeper, kafka, redis
|   +-- nginx.conf                    # Nginx config for frontend + API proxy
+-- k8s/
|   +-- helm/todo-app/
|   |   +-- Chart.yaml                # Chart v0.5.0, app v0.5.0
|   |   +-- values.yaml               # Default values (see reference above)
|   |   +-- templates/
|   |       +-- _helpers.tpl           # Template helpers
|   |       +-- backend-deployment.yaml  # Backend with Dapr annotations
|   |       +-- backend-service.yaml   # ClusterIP :8000
|   |       +-- frontend-deployment.yaml # Nginx frontend
|   |       +-- frontend-service.yaml  # ClusterIP :80
|   |       +-- configmap.yaml         # Non-sensitive config
|   |       +-- secret.yaml            # DATABASE_URL
|   |       +-- ingress.yaml           # NGINX ingress rules
|   |       +-- hpa.yaml               # Backend autoscaler (2-10 pods)
|   +-- dapr-components/
|       +-- pubsub.yaml               # pubsub.kafka component
|       +-- statestore.yaml           # state.redis component
|       +-- subscription.yaml         # task-events subscription (scoped)
+-- infra/
|   +-- do-cluster.tf                 # Terraform: DOKS cluster provisioning
|   +-- setup-doks.sh                 # doctl-based cluster setup script
+-- scripts/
|   +-- setup-kafka.sh                # Strimzi operator + Kafka cluster + topics
|   +-- setup-dapr.sh                 # Dapr CLI install + K8s init + components
|   +-- deploy-doks.sh                # Build, push, Helm deploy to DOKS
+-- README.md
```
