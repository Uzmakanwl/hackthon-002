# CLAUDE.md — Hackathon II: Spec-Driven Todo App

## Project Overview

A progressive todo application built across 5 phases, evolving from an in-memory Python console app to a cloud-deployed, AI-powered, Kubernetes-orchestrated full-stack system. Each phase is **fully independent** with its own codebase, dependencies, and data models.

**Owner:** mAzam (Senior Fullstack Developer)
**Feature Target:** ALL levels — Basic + Intermediate + Advanced (recurring tasks, due dates, reminders)

---

## Repository Structure

```
hackathon-todo/
├── claude.md                  # This file — project-wide instructions
├── README.md                  # Project overview and phase summaries
├── .gitignore                 # Global gitignore
│
├── phase-1-console/           # Python console app (in-memory)
│   ├── README.md
│   ├── requirements.txt
│   ├── src/
│   │   ├── main.py            # Entry point — CLI loop
│   │   ├── models.py          # Task dataclass/model
│   │   ├── store.py           # In-memory task store
│   │   ├── commands.py        # CRUD + search/filter/sort handlers
│   │   ├── recurrence.py      # Recurring task logic
│   │   └── utils.py           # Validators, formatters, helpers
│   └── tests/
│       └── test_commands.py
│
├── phase-2-fullstack/         # Next.js + FastAPI + SQLModel + Neon DB
│   ├── README.md
│   ├── backend/
│   │   ├── requirements.txt
│   │   ├── alembic/           # DB migrations
│   │   ├── app/
│   │   │   ├── main.py        # FastAPI app entry
│   │   │   ├── models.py      # SQLModel table definitions
│   │   │   ├── schemas.py     # Pydantic request/response schemas
│   │   │   ├── routers/
│   │   │   │   └── tasks.py   # Task CRUD + filter/sort endpoints
│   │   │   ├── services/
│   │   │   │   ├── task_service.py
│   │   │   │   └── recurrence_service.py
│   │   │   ├── db.py          # Neon DB connection + session
│   │   │   └── config.py      # Environment config
│   │   └── tests/
│   └── frontend/
│       ├── package.json
│       ├── next.config.js
│       ├── tailwind.config.js
│       ├── src/
│       │   ├── app/            # Next.js App Router
│       │   ├── components/     # UI components
│       │   ├── hooks/          # Custom React hooks
│       │   ├── lib/            # API client, utils
│       │   └── types/          # TypeScript interfaces
│       └── tests/
│
├── phase-3-ai-chatbot/        # OpenAI ChatKit + Agents SDK + MCP
│   ├── README.md
│   ├── backend/               # Same structure as phase-2 backend + AI layer
│   │   ├── app/
│   │   │   ├── agents/        # OpenAI Agents SDK definitions
│   │   │   ├── mcp/           # MCP server for todo operations
│   │   │   └── ...            # Same CRUD structure
│   └── frontend/              # ChatKit-powered UI
│
├── phase-4-k8s-local/         # Docker + Minikube + Helm
│   ├── README.md
│   ├── backend/               # Same app code, containerized
│   ├── frontend/              # Same app code, containerized
│   ├── docker/
│   │   ├── Dockerfile.backend
│   │   ├── Dockerfile.frontend
│   │   └── docker-compose.yml # Local dev compose
│   ├── k8s/
│   │   ├── helm/
│   │   │   └── todo-app/      # Helm chart
│   │   │       ├── Chart.yaml
│   │   │       ├── values.yaml
│   │   │       └── templates/
│   │   └── manifests/         # Raw K8s manifests (fallback)
│   └── scripts/
│       ├── setup-minikube.sh
│       └── deploy.sh
│
└── phase-5-cloud/             # Kafka + Dapr + DigitalOcean DOKS
    ├── README.md
    ├── backend/
    │   ├── app/
    │   │   ├── events/        # Kafka producers/consumers
    │   │   ├── dapr/          # Dapr sidecar config
    │   │   └── ...
    ├── frontend/
    ├── docker/
    ├── k8s/
    │   ├── helm/
    │   └── dapr-components/   # Dapr component YAMLs
    ├── infra/
    │   ├── do-cluster.tf      # Optional Terraform for DOKS
    │   └── setup-doks.sh
    └── scripts/
```

---

## Universal Data Model (Todo/Task Entity)

Each phase implements this independently, but the logical model is consistent:

```
Task {
  id              : unique identifier (UUID or auto-increment)
  title           : string, required, max 200 chars
  description     : string, optional, max 2000 chars
  status          : enum ["pending", "in_progress", "completed"]
  priority        : enum ["low", "medium", "high"]
  tags            : list of strings (e.g., ["work", "home", "urgent"])
  due_date        : datetime, optional
  reminder_at     : datetime, optional (for browser notifications)
  is_recurring    : boolean, default false
  recurrence_rule : string, optional (e.g., "daily", "weekly", "monthly", or cron-like)
  next_occurrence : datetime, optional (auto-calculated from recurrence_rule)
  created_at      : datetime, auto-set
  updated_at      : datetime, auto-set
  completed_at    : datetime, optional, set when status → completed
}
```

---

## Feature Checklist (ALL Phases Must Implement)

### Basic (Core CRUD)
- [ ] Add task with title, description, priority, tags
- [ ] Delete task by ID
- [ ] Update task fields (partial update supported)
- [ ] View all tasks (list view)
- [ ] Mark as complete / toggle completion status
- [ ] View single task detail

### Intermediate (Organization & Usability)
- [ ] Assign priority levels (high / medium / low)
- [ ] Assign tags/categories (free-form labels)
- [ ] Search tasks by keyword (title + description)
- [ ] Filter by: status, priority, tag, date range
- [ ] Sort by: due date, priority, created date, alphabetical
- [ ] Combined filter + sort (e.g., "high priority, due this week, sorted by date")

### Advanced (Intelligent Features)
- [ ] Recurring tasks with rules: daily, weekly, monthly, custom
- [ ] Auto-create next occurrence when a recurring task is completed
- [ ] Due dates with date/time picker (UI) or date input (CLI)
- [ ] Reminder timestamps (Phase 2+ uses browser Notification API)
- [ ] Overdue task highlighting / detection

---

## Phase-Specific Instructions

### Phase 1 — In-Memory Python Console App

**Stack:** Python 3.12+, no external DB
**Points:** 100 | **Due:** Dec 7, 2025

**Architecture:**
- Pure Python, no frameworks (no Flask/Django)
- In-memory storage using a dictionary/list in `store.py`
- CLI menu-driven interface with numbered options
- Use Python `dataclass` or Pydantic `BaseModel` for the Task model
- UUID for task IDs

**CLI Interface Pattern:**
```
=== Todo App ===
1. Add Task
2. View All Tasks
3. View Task Details
4. Update Task
5. Delete Task
6. Mark Complete/Incomplete
7. Search Tasks
8. Filter Tasks
9. Sort Tasks
10. Exit
```

**Recurrence Logic (Phase 1):**
- When a recurring task is marked complete, automatically create a clone with the next due date
- Support: daily, weekly, monthly, yearly
- Use `dateutil.relativedelta` or manual timedelta calculations

**Testing:**
- Use `pytest`
- Test all CRUD operations
- Test search/filter/sort edge cases
- Test recurrence auto-scheduling

**Constraints:**
- All data is lost on exit (in-memory only) — this is expected
- No async, no threading
- Keep it simple, well-structured, and readable

---

### Phase 2 — Full-Stack Web Application

**Stack:** Next.js 14+ (App Router), FastAPI, SQLModel, Neon DB (PostgreSQL)
**Points:** 150 | **Due:** Dec 14, 2025

**Backend (FastAPI + SQLModel):**
- Use SQLModel for ORM (it's SQLAlchemy + Pydantic combined)
- Connect to Neon DB (serverless PostgreSQL) — use connection string from env
- Use Alembic for database migrations
- RESTful API design:
  ```
  POST   /api/tasks          — Create task
  GET    /api/tasks          — List tasks (query params for filter/sort/search)
  GET    /api/tasks/{id}     — Get single task
  PATCH  /api/tasks/{id}     — Partial update
  DELETE /api/tasks/{id}     — Delete task
  POST   /api/tasks/{id}/complete — Toggle completion
  ```
- Query params pattern: `?status=pending&priority=high&search=meeting&sort_by=due_date&sort_order=asc&tag=work`
- Return proper HTTP status codes (201 created, 404 not found, 422 validation error)
- Use FastAPI dependency injection for DB sessions

**Frontend (Next.js):**
- App Router with server components where appropriate
- Client components for interactive parts (forms, filters, toggles)
- Tailwind CSS for styling — clean, minimal, functional design
- Use `fetch` or a lightweight client (no axios bloat)
- Implement debounced search input
- Date/time picker for due dates and reminders
- Browser Notification API for reminders (request permission, schedule via setTimeout or service worker)
- Responsive layout (mobile-friendly)
- Toast notifications for CRUD feedback

**Environment Variables:**
```
# backend/.env
DATABASE_URL=postgresql://...@neon.tech/tododb
CORS_ORIGINS=http://localhost:3000

# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Testing:**
- Backend: `pytest` + `httpx` for API tests
- Frontend: Component tests where critical

---

### Phase 3 — AI-Powered Todo Chatbot

**Stack:** OpenAI ChatKit, OpenAI Agents SDK, Official MCP SDK
**Points:** 200 | **Due:** Dec 21, 2025

**Architecture:**
- Extend Phase 2's backend with an AI agent layer
- MCP (Model Context Protocol) server exposes todo CRUD as tools
- OpenAI Agent uses MCP tools to manage tasks via natural language

**MCP Server Tools:**
```
create_task(title, description?, priority?, tags?, due_date?, recurrence_rule?)
list_tasks(status?, priority?, search?, sort_by?, tag?)
get_task(task_id)
update_task(task_id, fields...)
delete_task(task_id)
complete_task(task_id)
```

**OpenAI Agent Definition:**
- System prompt: "You are a personal task management assistant. Help the user manage their todos using natural language. When the user says things like 'remind me to buy groceries tomorrow', create a task with appropriate due date and priority."
- Use Agents SDK to wire MCP tools to the agent
- Handle ambiguity gracefully (ask for clarification when needed)

**ChatKit Frontend:**
- Conversational UI — chat-based interaction
- Show task list alongside chat for context
- Natural language commands: "add a high priority task to review PRs by Friday", "show me all overdue tasks", "mark the grocery task as done"

**Environment Variables:**
```
OPENAI_API_KEY=sk-...
```

---

### Phase 4 — Local Kubernetes Deployment

**Stack:** Docker, Minikube, Helm, kubectl-ai, kagent
**Points:** 250 | **Due:** Jan 4, 2026

**Containerization:**
- Multi-stage Dockerfiles for both backend and frontend
- Backend: Python slim image, non-root user, health check endpoint `/health`
- Frontend: Node build stage → nginx serve stage
- `docker-compose.yml` for local development (app + postgres)

**Kubernetes (Minikube):**
- Helm chart in `k8s/helm/todo-app/`
- Resources to define:
  - Deployments: backend (2 replicas), frontend (2 replicas)
  - Services: ClusterIP for backend, NodePort or Ingress for frontend
  - ConfigMap: non-sensitive config
  - Secret: DB credentials, API keys
  - Ingress: NGINX ingress controller
  - HPA: Horizontal Pod Autoscaler for backend (CPU threshold)
  - PersistentVolumeClaim: if running local postgres (not needed if using Neon)

**Helm values.yaml:**
```yaml
backend:
  image: todo-backend:latest
  replicas: 2
  port: 8000
  env:
    DATABASE_URL: "" # from secret
frontend:
  image: todo-frontend:latest
  replicas: 2
  port: 80
ingress:
  enabled: true
  host: todo.local
```

**kubectl-ai & kagent:**
- Document how to use kubectl-ai for natural language K8s operations
- kagent for AI-powered cluster management

**Scripts:**
- `setup-minikube.sh`: Start minikube, enable addons (ingress, metrics-server)
- `deploy.sh`: Build images, helm install, verify pods

---

### Phase 5 — Advanced Cloud Deployment

**Stack:** Kafka, Dapr, DigitalOcean DOKS
**Points:** 300 | **Due:** Jan 18, 2026

**DigitalOcean DOKS Setup:**
- Create Kubernetes cluster via DO console or doctl CLI
- Minimum: 2 nodes, 2 vCPU / 4GB each
- Install Dapr on the cluster
- Deploy Kafka (Strimzi operator or Confluent Cloud)

**Event-Driven Architecture with Kafka:**
- Events to publish:
  - `task.created` — when a new task is added
  - `task.updated` — when a task is modified
  - `task.completed` — when a task is marked done
  - `task.deleted` — when a task is removed
  - `task.reminder.due` — when a reminder time is reached
  - `task.recurring.triggered` — when a recurring task auto-creates next instance
- Consumers:
  - Notification service: listens to `task.reminder.due`, sends notifications
  - Recurrence service: listens to `task.completed`, creates next occurrence if recurring
  - Audit/log service: logs all events for observability

**Dapr Integration:**
- Use Dapr pub/sub building block backed by Kafka
- Use Dapr state store for caching (Redis sidecar)
- Use Dapr service invocation for inter-service communication
- Dapr component YAMLs in `k8s/dapr-components/`

**Deployment Pipeline:**
- Container registry: DigitalOcean Container Registry (DOCR) or GitHub Container Registry
- CI/CD: GitHub Actions → build images → push to registry → helm upgrade on DOKS
- Blue-green or rolling update strategy

---

## Coding Conventions

### General
- **Language versions:** Python 3.12+, Node.js 20+, TypeScript strict mode
- **No `any` types** in TypeScript — always define proper interfaces
- **Meaningful variable names** — no single letters except loop counters
- **Functions under 40 lines** — extract if longer
- **One responsibility per file** — no god files

### Python (Phases 1, 2, 3 backend)
- Use type hints everywhere
- Use `pydantic` for validation in Phase 2+
- Use `async def` for FastAPI route handlers
- Raise `HTTPException` with clear messages, never return raw error strings
- Docstrings for all public functions (Google style)
- Use `ruff` for linting, `black` for formatting

### TypeScript / Next.js (Phases 2-5 frontend)
- Strict TypeScript — `"strict": true` in tsconfig
- Use App Router conventions (page.tsx, layout.tsx, loading.tsx, error.tsx)
- Prefer server components; use `"use client"` only when needed
- Custom hooks in `hooks/` directory
- API calls through a centralized client in `lib/api.ts`
- Use `eslint` + `prettier`

### Git Conventions
- **Branch naming:** `phase-{n}/{feature}` (e.g., `phase-1/add-recurrence`)
- **Commit format:** `phase-{n}: <type>: <description>`
  - Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`
  - Example: `phase-2: feat: add task filtering by priority and tags`
- **Never commit:** `.env` files, `node_modules`, `__pycache__`, `.venv`

### Error Handling
- **Python:** Use custom exception classes; catch at the route layer, not deep in services
- **TypeScript:** Use try/catch with typed error responses; show user-friendly toast messages
- **Never silently swallow errors** — always log or surface them

### Testing
- Every phase must have tests for CRUD operations at minimum
- Phase 1: `pytest` unit tests
- Phase 2+: API integration tests + critical component tests
- Aim for happy path + edge cases (empty list, not found, duplicate, invalid input)

---

## Environment & Tooling Setup

### Python Projects
```bash
cd phase-{n}/backend   # or phase-1/
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Next.js Projects
```bash
cd phase-{n}/frontend
npm install
npm run dev
```

### Docker (Phase 4+)
```bash
docker compose up --build          # Local dev
eval $(minikube docker-env)        # Use minikube's Docker daemon
docker build -t todo-backend .     # Build for K8s
```

---

## Key Reminders for Claude Code

1. **Each phase is independent.** Do not import from other phase directories. Copy and adapt.
2. **Always implement ALL feature levels** (Basic + Intermediate + Advanced) unless explicitly told to skip.
3. **Recurring tasks are a first-class feature**, not an afterthought. Design the data model to support them from the start.
4. **Use environment variables** for all config (DB URLs, API keys, ports). Never hardcode.
5. **README.md per phase** — include setup instructions, architecture diagram (mermaid), API docs, and how to run tests.
6. **Keep the UI functional, not fancy.** Tailwind utility classes, clean layout, no custom CSS unless necessary. Focus on UX over aesthetics.
7. **FastAPI backend must have OpenAPI docs** — auto-generated at `/docs` (Swagger) and `/redoc`.
8. **Database migrations are mandatory** in Phase 2+ — never modify the DB schema manually.
9. **Health check endpoints** (`/health`) on all services for K8s probes.
10. **When in doubt, keep it simple.** This is a hackathon — working software beats perfect architecture.
