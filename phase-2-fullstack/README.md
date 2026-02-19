# Phase 2 -- Full-Stack Todo Web Application

A full-featured task management web application built with **Next.js 14** (App Router) on the frontend and **FastAPI + SQLModel** on the backend, backed by **PostgreSQL** (Neon DB serverless). Supports full CRUD, search, filtering, sorting, recurring tasks, due dates, reminders, and a responsive UI.

---

## Architecture

```mermaid
graph LR
    Browser["Browser (User)"]
    subgraph Frontend ["Frontend - Next.js 14"]
        AppRouter["App Router Pages"]
        Components["React Components"]
        Hooks["Custom Hooks"]
        APIClient["API Client (lib/api.ts)"]
        AppRouter --> Components
        Components --> Hooks
        Hooks --> APIClient
    end
    subgraph Backend ["Backend - FastAPI"]
        Router["Routers (tasks.py)"]
        Service["Services (task_service, recurrence_service)"]
        ORM["SQLModel ORM"]
        Router --> Service
        Service --> ORM
    end
    subgraph Database ["Database"]
        DB[("PostgreSQL / SQLite")]
    end

    Browser -->|HTTP| AppRouter
    APIClient -->|REST API| Router
    ORM --> DB
```

---

## Features

### Basic (Core CRUD)
- Add tasks with title, description, priority, and tags
- View all tasks in a responsive list
- View single task details
- Update any task field (partial updates supported)
- Delete tasks by ID
- Toggle task completion status

### Intermediate (Organization and Usability)
- Priority levels: high, medium, low
- Free-form tags/categories
- Keyword search across title and description (debounced input)
- Filter by status, priority, and tag
- Sort by due date, priority, created date, or title (ascending/descending)
- Combined filter + sort + search in a single query

### Advanced (Intelligent Features)
- Recurring tasks with rules: daily, weekly, monthly, yearly
- Auto-creation of the next occurrence when a recurring task is completed
- Due dates with date/time input
- Reminder timestamps for future notification support
- Overdue task detection

---

## Tech Stack

| Layer      | Technology                                      |
|------------|------------------------------------------------|
| Frontend   | Next.js 14 (App Router), TypeScript, Tailwind CSS |
| Backend    | FastAPI, Python 3.12+                           |
| ORM        | SQLModel (SQLAlchemy + Pydantic)                |
| Migrations | Alembic                                         |
| Database   | PostgreSQL (Neon DB) / SQLite (testing)         |
| Testing    | pytest, httpx                                   |

---

## Backend Setup

```bash
cd phase-2-fullstack/backend

# Create and activate virtual environment
python -m venv .venv
# source .venv/bin/activate        # Linux / macOS
.\.venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt
```

Create a `.env` file in the `backend/` directory:

```env
DATABASE_URL=postgresql://user:password@host.neon.tech/tododb?sslmode=require
CORS_ORIGINS=http://localhost:3000
```

Run database migrations and start the server:

```bash
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

API documentation is auto-generated:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## Frontend Setup

```bash
cd phase-2-fullstack/frontend

# Install dependencies
npm install
```

Create a `.env.local` file in the `frontend/` directory:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Start the development server:

```bash
npm run dev
```

Open http://localhost:3000 in your browser.

---

## API Documentation

### Endpoints

| Method | Path                       | Description                 | Success | Error     |
|--------|----------------------------|-----------------------------|---------|-----------|
| POST   | `/api/tasks`               | Create a new task           | 201     | 422       |
| GET    | `/api/tasks`               | List tasks (filter/sort/search) | 200 | --        |
| GET    | `/api/tasks/{id}`          | Get a single task           | 200     | 404       |
| PATCH  | `/api/tasks/{id}`          | Partially update a task     | 200     | 404, 422  |
| DELETE | `/api/tasks/{id}`          | Delete a task               | 204     | 404       |
| POST   | `/api/tasks/{id}/complete` | Toggle completion status    | 200     | 404       |
| GET    | `/health`                  | Health check                | 200     | --        |

### Query Parameters (GET /api/tasks)

| Parameter    | Type   | Description                                        |
|-------------|--------|----------------------------------------------------|
| `status`    | string | Filter by status: `pending`, `in_progress`, `completed` |
| `priority`  | string | Filter by priority: `low`, `medium`, `high`         |
| `tag`       | string | Filter by tag (exact match within tags list)         |
| `search`    | string | Keyword search in title and description              |
| `sort_by`   | string | Sort field: `due_date`, `priority`, `created_at`, `title` |
| `sort_order`| string | Sort direction: `asc` (default), `desc`              |

**Example:** `GET /api/tasks?status=pending&priority=high&search=meeting&sort_by=due_date&sort_order=asc&tag=work`

---

## Environment Variables

### Backend (`backend/.env`)

| Variable       | Required | Description                              | Example                                      |
|---------------|----------|------------------------------------------|----------------------------------------------|
| `DATABASE_URL`| Yes      | PostgreSQL connection string (Neon DB)   | `postgresql://user:pass@host.neon.tech/tododb` |
| `CORS_ORIGINS`| No       | Allowed CORS origins (comma-separated)   | `http://localhost:3000`                       |

### Frontend (`frontend/.env.local`)

| Variable               | Required | Description              | Example                   |
|-----------------------|----------|--------------------------|---------------------------|
| `NEXT_PUBLIC_API_URL` | Yes      | Backend API base URL     | `http://localhost:8000`   |

---

## Testing

### Backend

All 41 tests cover CRUD operations, filtering, sorting, search, completion toggling, recurrence logic, model validation, and health check.

```bash
cd phase-2-fullstack/backend
python -m pytest tests/ -v
```

Tests use an in-memory SQLite database, so no external database is required.

### Frontend

Verify the frontend compiles without errors:

```bash
cd phase-2-fullstack/frontend
npm run build
```

---

## File Structure

```
phase-2-fullstack/
├── README.md
├── backend/
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │       └── 22a0173aa4c7_create_task_table.py
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app entry, CORS, health check
│   │   ├── config.py               # Settings from environment variables
│   │   ├── db.py                   # Engine, session, create_db_and_tables
│   │   ├── models.py               # Task SQLModel, TaskStatus/TaskPriority enums
│   │   ├── schemas.py              # Pydantic request/response schemas
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   └── tasks.py            # REST API endpoints
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── task_service.py      # CRUD, filter, sort, search, toggle
│   │       └── recurrence_service.py # Next occurrence calculation
│   └── tests/
│       ├── __init__.py
│       ├── test_db.py               # Config and DB tests
│       ├── test_models.py           # Model creation and enum tests
│       ├── test_task_service.py     # Service layer unit tests
│       └── test_tasks_api.py        # API integration tests (httpx)
└── frontend/
    ├── package.json
    ├── tsconfig.json
    ├── next.config.js
    ├── tailwind.config.ts
    ├── postcss.config.js
    ├── src/
    │   ├── app/
    │   │   ├── globals.css          # Tailwind base styles
    │   │   ├── layout.tsx           # Root layout
    │   │   └── page.tsx             # Main page (task list + form)
    │   ├── components/
    │   │   ├── FilterBar.tsx        # Status, priority, tag filters + sort
    │   │   ├── SearchInput.tsx      # Debounced search input
    │   │   ├── TaskCard.tsx         # Single task display card
    │   │   ├── TaskForm.tsx         # Create/edit task form
    │   │   └── TaskList.tsx         # Task list container
    │   ├── hooks/
    │   │   ├── useDebounce.ts       # Debounce hook for search
    │   │   └── useTasks.ts          # Task data fetching and state
    │   ├── lib/
    │   │   └── api.ts               # Centralized API client
    │   └── types/
    │       └── task.ts              # TypeScript interfaces
    └── next-env.d.ts
```

---

## Data Model

The `Task` entity supports the full feature set:

| Field             | Type                                  | Description                                |
|------------------|---------------------------------------|--------------------------------------------|
| `id`             | UUID                                  | Unique identifier (auto-generated)          |
| `title`          | string (max 200)                      | Task title (required)                       |
| `description`    | string (max 2000)                     | Optional description                        |
| `status`         | enum: pending, in_progress, completed | Current status                              |
| `priority`       | enum: low, medium, high               | Priority level                              |
| `tags`           | JSON array of strings                 | Free-form labels                            |
| `due_date`       | datetime (optional)                   | When the task is due                        |
| `reminder_at`    | datetime (optional)                   | When to send a reminder                     |
| `is_recurring`   | boolean                               | Whether the task repeats                    |
| `recurrence_rule`| string (optional)                     | Rule: daily, weekly, monthly, yearly        |
| `next_occurrence`| datetime (optional)                   | Auto-calculated next due date               |
| `created_at`     | datetime                              | Auto-set on creation                        |
| `updated_at`     | datetime                              | Auto-set on modification                    |
| `completed_at`   | datetime (optional)                   | Set when status changes to completed        |
