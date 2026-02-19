#!/usr/bin/env bash
# deploy-doks.sh — Deploy the Todo app to DigitalOcean DOKS
set -euo pipefail

REGISTRY="${REGISTRY:-registry.digitalocean.com/todo-app}"
NAMESPACE="${NAMESPACE:-todo}"
RELEASE_NAME="${RELEASE_NAME:-todo-app}"
CHART_DIR="$(dirname "$0")/../k8s/helm/todo-app"

echo "=== Building and pushing Docker images ==="
docker build -t "${REGISTRY}/todo-backend:latest" -f docker/Dockerfile.backend backend/
docker build -t "${REGISTRY}/todo-frontend:latest" -f docker/Dockerfile.frontend frontend/
docker push "${REGISTRY}/todo-backend:latest"
docker push "${REGISTRY}/todo-frontend:latest"

echo "=== Creating namespace: ${NAMESPACE} ==="
kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -

echo "=== Applying Dapr components ==="
kubectl apply -f "$(dirname "$0")/../k8s/dapr-components/" -n "${NAMESPACE}"

echo "=== Deploying with Helm ==="
helm upgrade --install "${RELEASE_NAME}" "${CHART_DIR}" \
  --namespace "${NAMESPACE}" \
  --set backend.image="${REGISTRY}/todo-backend:latest" \
  --set frontend.image="${REGISTRY}/todo-frontend:latest" \
  --set backend.env.DATABASE_URL="${DATABASE_URL}" \
  --wait --timeout 180s

echo "=== Verifying deployment ==="
kubectl get pods -n "${NAMESPACE}"
kubectl get svc -n "${NAMESPACE}"
kubectl get ingress -n "${NAMESPACE}"

echo "=== Deployment complete ==="
echo "Access the app at: http://todo.local (update /etc/hosts if needed)"
