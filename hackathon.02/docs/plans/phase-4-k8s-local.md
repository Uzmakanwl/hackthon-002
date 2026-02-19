# Phase 4: Local Kubernetes Deployment — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Containerize the Phase 2 full-stack todo app with Docker, deploy to a local Minikube Kubernetes cluster using Helm charts, with ingress, autoscaling, and health checks.

**Architecture:** Multi-stage Docker builds for backend (Python) and frontend (Next.js → Nginx). A Helm chart defines all K8s resources: Deployments (2 replicas each), Services, Ingress, ConfigMap, Secret, and HPA. Scripts automate Minikube setup and deployment.

**Tech Stack:** Docker, Minikube, Helm 3, kubectl, NGINX Ingress Controller, PostgreSQL (or Neon DB)

---

## Task 1: Backend — App Code (Adapted from Phase 2)

**Files:**
- Create: All backend files under `phase-4-k8s-local/backend/`

**Step 1: Copy Phase 2 backend**

Copy the entire backend from Phase 2's plan. Each phase is independent. Ensure:
- `app/main.py` has `/health` endpoint
- All CRUD, service, and router code is in place
- `.env.example` exists

**Step 2: Verify with tests**

Run: `cd phase-4-k8s-local/backend && python -m pytest -v`
Expected: All PASS

**Step 3: Commit**

```bash
git add phase-4-k8s-local/backend/
git commit -m "phase-4: feat: add backend app code (adapted from phase-2)"
```

---

## Task 2: Frontend — App Code (Adapted from Phase 2)

**Files:**
- Create: All frontend files under `phase-4-k8s-local/frontend/`

**Step 1: Copy Phase 2 frontend**

Copy all frontend code. Ensure next.config.js supports `output: "standalone"` for Docker:

```javascript
// next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
};

module.exports = nextConfig;
```

**Step 2: Verify build**

Run: `cd phase-4-k8s-local/frontend && npm install && npm run build`
Expected: Build succeeds

**Step 3: Commit**

```bash
git add phase-4-k8s-local/frontend/
git commit -m "phase-4: feat: add frontend app code (adapted from phase-2)"
```

---

## Task 3: Docker — Backend Dockerfile

**Files:**
- Create: `phase-4-k8s-local/docker/Dockerfile.backend`

**Step 1: Write Dockerfile.backend**

```dockerfile
# phase-4-k8s-local/docker/Dockerfile.backend
# Multi-stage build for FastAPI backend

# --- Build stage ---
FROM python:3.12-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# --- Runtime stage ---
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Step 2: Test Docker build**

Run: `cd phase-4-k8s-local && docker build -f docker/Dockerfile.backend -t todo-backend:latest ./backend`
Expected: Build succeeds

**Step 3: Commit**

```bash
git add phase-4-k8s-local/docker/Dockerfile.backend
git commit -m "phase-4: feat: add multi-stage Docker build for backend"
```

---

## Task 4: Docker — Frontend Dockerfile

**Files:**
- Create: `phase-4-k8s-local/docker/Dockerfile.frontend`
- Create: `phase-4-k8s-local/docker/nginx.conf`

**Step 1: Write Dockerfile.frontend**

```dockerfile
# phase-4-k8s-local/docker/Dockerfile.frontend
# Multi-stage build for Next.js frontend

# --- Build stage ---
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# Build-time env var for API URL (overridable)
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

RUN npm run build

# --- Runtime stage ---
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

# Create non-root user
RUN addgroup --system --gid 1001 nodejs \
    && adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
```

**Step 2: Write nginx.conf (fallback for static export)**

```nginx
# phase-4-k8s-local/docker/nginx.conf
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Health check
    location /nginx-health {
        return 200 'ok';
        add_header Content-Type text/plain;
    }
}
```

**Step 3: Test Docker build**

Run: `cd phase-4-k8s-local && docker build -f docker/Dockerfile.frontend -t todo-frontend:latest ./frontend`
Expected: Build succeeds

**Step 4: Commit**

```bash
git add phase-4-k8s-local/docker/Dockerfile.frontend phase-4-k8s-local/docker/nginx.conf
git commit -m "phase-4: feat: add multi-stage Docker build for frontend"
```

---

## Task 5: Docker Compose — Local Development

**Files:**
- Create: `phase-4-k8s-local/docker/docker-compose.yml`

**Step 1: Write docker-compose.yml**

```yaml
# phase-4-k8s-local/docker/docker-compose.yml
version: '3.8'

services:
  backend:
    build:
      context: ../backend
      dockerfile: ../docker/Dockerfile.backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://todouser:todopass@postgres:5432/tododb
      - CORS_ORIGINS=http://localhost:3000
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 5s
      retries: 3

  frontend:
    build:
      context: ../frontend
      dockerfile: ../docker/Dockerfile.frontend
      args:
        NEXT_PUBLIC_API_URL: http://localhost:8000
    ports:
      - "3000:3000"
    depends_on:
      - backend

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

volumes:
  pgdata:
```

**Step 2: Test compose up**

Run: `cd phase-4-k8s-local/docker && docker compose up --build -d`
Verify: `curl http://localhost:8000/health` returns `{"status": "ok"}`
Verify: `curl http://localhost:3000` returns HTML

**Step 3: Commit**

```bash
git add phase-4-k8s-local/docker/docker-compose.yml
git commit -m "phase-4: feat: add docker-compose for local development"
```

---

## Task 6: Helm Chart — Chart.yaml and values.yaml

**Files:**
- Create: `phase-4-k8s-local/k8s/helm/todo-app/Chart.yaml`
- Create: `phase-4-k8s-local/k8s/helm/todo-app/values.yaml`

**Step 1: Write Chart.yaml**

```yaml
# k8s/helm/todo-app/Chart.yaml
apiVersion: v2
name: todo-app
description: Hackathon Todo App — Full-stack deployment with backend and frontend
type: application
version: 0.1.0
appVersion: "1.0.0"
```

**Step 2: Write values.yaml**

```yaml
# k8s/helm/todo-app/values.yaml
backend:
  image:
    repository: todo-backend
    tag: latest
    pullPolicy: IfNotPresent
  replicas: 2
  port: 8000
  resources:
    requests:
      cpu: 100m
      memory: 128Mi
    limits:
      cpu: 500m
      memory: 512Mi

frontend:
  image:
    repository: todo-frontend
    tag: latest
    pullPolicy: IfNotPresent
  replicas: 2
  port: 3000
  resources:
    requests:
      cpu: 50m
      memory: 64Mi
    limits:
      cpu: 200m
      memory: 256Mi

ingress:
  enabled: true
  className: nginx
  host: todo.local

database:
  url: ""  # Overridden by secret

hpa:
  enabled: true
  minReplicas: 2
  maxReplicas: 5
  targetCPUUtilization: 70
```

**Step 3: Commit**

```bash
git add phase-4-k8s-local/k8s/helm/todo-app/Chart.yaml
git add phase-4-k8s-local/k8s/helm/todo-app/values.yaml
git commit -m "phase-4: feat: add Helm chart definition and values"
```

---

## Task 7: Helm Chart — Templates (Deployments, Services)

**Files:**
- Create: `phase-4-k8s-local/k8s/helm/todo-app/templates/_helpers.tpl`
- Create: `phase-4-k8s-local/k8s/helm/todo-app/templates/backend-deployment.yaml`
- Create: `phase-4-k8s-local/k8s/helm/todo-app/templates/backend-service.yaml`
- Create: `phase-4-k8s-local/k8s/helm/todo-app/templates/frontend-deployment.yaml`
- Create: `phase-4-k8s-local/k8s/helm/todo-app/templates/frontend-service.yaml`

**Step 1: Write _helpers.tpl**

```yaml
{{/* Expand the name of the chart */}}
{{- define "todo-app.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/* Create a default fully qualified app name */}}
{{- define "todo-app.fullname" -}}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/* Common labels */}}
{{- define "todo-app.labels" -}}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}
```

**Step 2: Write backend-deployment.yaml**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "todo-app.fullname" . }}-backend
  labels:
    {{- include "todo-app.labels" . | nindent 4 }}
    app.kubernetes.io/component: backend
spec:
  replicas: {{ .Values.backend.replicas }}
  selector:
    matchLabels:
      app.kubernetes.io/component: backend
  template:
    metadata:
      labels:
        app.kubernetes.io/component: backend
    spec:
      containers:
        - name: backend
          image: "{{ .Values.backend.image.repository }}:{{ .Values.backend.image.tag }}"
          imagePullPolicy: {{ .Values.backend.image.pullPolicy }}
          ports:
            - containerPort: {{ .Values.backend.port }}
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: {{ include "todo-app.fullname" . }}-secret
                  key: database-url
            - name: CORS_ORIGINS
              valueFrom:
                configMapKeyRef:
                  name: {{ include "todo-app.fullname" . }}-config
                  key: cors-origins
          livenessProbe:
            httpGet:
              path: /health
              port: {{ .Values.backend.port }}
            initialDelaySeconds: 15
            periodSeconds: 20
          readinessProbe:
            httpGet:
              path: /health
              port: {{ .Values.backend.port }}
            initialDelaySeconds: 5
            periodSeconds: 10
          resources:
            {{- toYaml .Values.backend.resources | nindent 12 }}
```

**Step 3: Write backend-service.yaml**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "todo-app.fullname" . }}-backend
  labels:
    {{- include "todo-app.labels" . | nindent 4 }}
    app.kubernetes.io/component: backend
spec:
  type: ClusterIP
  ports:
    - port: {{ .Values.backend.port }}
      targetPort: {{ .Values.backend.port }}
      protocol: TCP
  selector:
    app.kubernetes.io/component: backend
```

**Step 4: Write frontend-deployment.yaml and frontend-service.yaml**

Similar structure to backend, using frontend values. Frontend service exposes port 3000.

**Step 5: Verify Helm template renders**

Run: `cd phase-4-k8s-local && helm template test k8s/helm/todo-app/`
Expected: Valid YAML output with all resources

**Step 6: Commit**

```bash
git add phase-4-k8s-local/k8s/helm/todo-app/templates/
git commit -m "phase-4: feat: add Helm templates for backend and frontend deployments + services"
```

---

## Task 8: Helm Chart — ConfigMap, Secret, Ingress, HPA

**Files:**
- Create: `phase-4-k8s-local/k8s/helm/todo-app/templates/configmap.yaml`
- Create: `phase-4-k8s-local/k8s/helm/todo-app/templates/secret.yaml`
- Create: `phase-4-k8s-local/k8s/helm/todo-app/templates/ingress.yaml`
- Create: `phase-4-k8s-local/k8s/helm/todo-app/templates/hpa.yaml`

**Step 1: Write configmap.yaml**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "todo-app.fullname" . }}-config
  labels:
    {{- include "todo-app.labels" . | nindent 4 }}
data:
  cors-origins: "http://{{ .Values.ingress.host }}"
```

**Step 2: Write secret.yaml**

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "todo-app.fullname" . }}-secret
  labels:
    {{- include "todo-app.labels" . | nindent 4 }}
type: Opaque
data:
  database-url: {{ .Values.database.url | b64enc | quote }}
```

**Step 3: Write ingress.yaml**

```yaml
{{- if .Values.ingress.enabled }}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ include "todo-app.fullname" . }}-ingress
  labels:
    {{- include "todo-app.labels" . | nindent 4 }}
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: {{ .Values.ingress.className }}
  rules:
    - host: {{ .Values.ingress.host }}
      http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: {{ include "todo-app.fullname" . }}-backend
                port:
                  number: {{ .Values.backend.port }}
          - path: /
            pathType: Prefix
            backend:
              service:
                name: {{ include "todo-app.fullname" . }}-frontend
                port:
                  number: {{ .Values.frontend.port }}
{{- end }}
```

**Step 4: Write hpa.yaml**

```yaml
{{- if .Values.hpa.enabled }}
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{ include "todo-app.fullname" . }}-backend-hpa
  labels:
    {{- include "todo-app.labels" . | nindent 4 }}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{ include "todo-app.fullname" . }}-backend
  minReplicas: {{ .Values.hpa.minReplicas }}
  maxReplicas: {{ .Values.hpa.maxReplicas }}
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: {{ .Values.hpa.targetCPUUtilization }}
{{- end }}
```

**Step 5: Verify full Helm template**

Run: `helm template test phase-4-k8s-local/k8s/helm/todo-app/ --set database.url="postgresql://user:pass@host/db"`
Expected: Valid YAML with all 8 resources

**Step 6: Commit**

```bash
git add phase-4-k8s-local/k8s/helm/todo-app/templates/
git commit -m "phase-4: feat: add ConfigMap, Secret, Ingress, and HPA templates"
```

---

## Task 9: Scripts — Minikube Setup and Deploy

**Files:**
- Create: `phase-4-k8s-local/scripts/setup-minikube.sh`
- Create: `phase-4-k8s-local/scripts/deploy.sh`

**Step 1: Write setup-minikube.sh**

```bash
#!/bin/bash
set -euo pipefail

echo "=== Setting up Minikube for Todo App ==="

# Start minikube if not running
if ! minikube status | grep -q "Running"; then
    echo "Starting Minikube..."
    minikube start --driver=docker --cpus=2 --memory=4096
fi

# Enable required addons
echo "Enabling addons..."
minikube addons enable ingress
minikube addons enable metrics-server
minikube addons enable dashboard

# Verify
echo "Verifying cluster..."
kubectl cluster-info
kubectl get nodes

echo ""
echo "=== Minikube is ready! ==="
echo "Dashboard: minikube dashboard"
echo "IP: $(minikube ip)"
```

**Step 2: Write deploy.sh**

```bash
#!/bin/bash
set -euo pipefail

echo "=== Deploying Todo App to Minikube ==="

# Point Docker to Minikube's daemon
echo "Configuring Docker to use Minikube..."
eval $(minikube docker-env)

# Build images
echo "Building backend image..."
docker build -f ../docker/Dockerfile.backend -t todo-backend:latest ../backend

echo "Building frontend image..."
docker build -f ../docker/Dockerfile.frontend -t todo-frontend:latest ../frontend \
    --build-arg NEXT_PUBLIC_API_URL=http://todo.local/api

# Deploy with Helm
echo "Deploying with Helm..."
helm upgrade --install todo-app ../k8s/helm/todo-app/ \
    --set database.url="postgresql://todouser:todopass@postgres:5432/tododb" \
    --wait --timeout 120s

# Verify deployment
echo "Verifying pods..."
kubectl get pods -l "app.kubernetes.io/managed-by=Helm"
kubectl get services
kubectl get ingress

echo ""
echo "=== Deployment complete! ==="
echo "Add to /etc/hosts: $(minikube ip) todo.local"
echo "Access: http://todo.local"
```

**Step 3: Make scripts executable**

Run: `chmod +x phase-4-k8s-local/scripts/*.sh`

**Step 4: Commit**

```bash
git add phase-4-k8s-local/scripts/
git commit -m "phase-4: feat: add Minikube setup and Helm deploy scripts"
```

---

## Task 10: Raw Manifests (Fallback)

**Files:**
- Create: `phase-4-k8s-local/k8s/manifests/namespace.yaml`

**Step 1: Write namespace.yaml**

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: todo-app
  labels:
    app: todo-app
```

**Step 2: Commit**

```bash
git add phase-4-k8s-local/k8s/manifests/
git commit -m "phase-4: chore: add raw K8s namespace manifest"
```

---

## Task 11: README and Final Polish

**Files:**
- Create: `phase-4-k8s-local/README.md`

**Step 1: Write comprehensive README**

Cover:
- Architecture diagram (Mermaid: Ingress → Frontend/Backend Pods → PostgreSQL, with HPA)
- Prerequisites (Docker, Minikube, Helm, kubectl)
- Docker setup (docker-compose for local dev)
- Minikube setup (scripts/setup-minikube.sh)
- Deployment (scripts/deploy.sh)
- Helm values reference
- kubectl-ai and kagent documentation
- Troubleshooting (common issues)
- How to access (hosts file setup)

**Step 2: End-to-end verification**

Run setup + deploy scripts, verify app is accessible at http://todo.local

**Step 3: Commit**

```bash
git add phase-4-k8s-local/README.md
git commit -m "phase-4: docs: add README with Docker, Minikube, and Helm instructions"
```

---

## Summary

| Task | What |
|------|------|
| 1 | Backend app code (from Phase 2) |
| 2 | Frontend app code (from Phase 2) |
| 3 | Backend Dockerfile (multi-stage) |
| 4 | Frontend Dockerfile (multi-stage) + nginx.conf |
| 5 | Docker Compose (local dev) |
| 6 | Helm Chart.yaml + values.yaml |
| 7 | Helm templates: Deployments + Services |
| 8 | Helm templates: ConfigMap, Secret, Ingress, HPA |
| 9 | Minikube setup + deploy scripts |
| 10 | Raw K8s manifests (fallback) |
| 11 | README + final polish |

**Total: 11 tasks focused on containerization and orchestration.**
