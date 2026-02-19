#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Deploying Todo App to Minikube ==="

# Verify minikube is running
if ! minikube status 2>/dev/null | grep -q "Running"; then
    echo "Error: Minikube is not running. Run setup-minikube.sh first."
    exit 1
fi

# Point Docker to Minikube's daemon
echo "Configuring Docker to use Minikube..."
eval $(minikube docker-env)

# Build images
echo ""
echo "Building backend image..."
docker build -f "$PROJECT_DIR/docker/Dockerfile.backend" -t todo-backend:latest "$PROJECT_DIR/backend"

echo ""
echo "Building frontend image..."
docker build -f "$PROJECT_DIR/docker/Dockerfile.frontend" -t todo-frontend:latest "$PROJECT_DIR/frontend"

# Deploy with Helm
echo ""
echo "Deploying with Helm..."
helm upgrade --install todo-app "$PROJECT_DIR/k8s/helm/todo-app/" \
    --wait --timeout 180s

# Verify deployment
echo ""
echo "Verifying pods..."
kubectl get pods -l "app.kubernetes.io/name=todo-app"

echo ""
echo "Services:"
kubectl get services -l "app.kubernetes.io/name=todo-app"

echo ""
echo "Ingress:"
kubectl get ingress

MINIKUBE_IP=$(minikube ip)
echo ""
echo "=== Deployment complete! ==="
echo "Ensure /etc/hosts has: $MINIKUBE_IP todo.local"
echo "Access the app at: http://todo.local"
echo ""
echo "Useful commands:"
echo "  kubectl get pods              — View pod status"
echo "  kubectl logs -f <pod-name>    — View pod logs"
echo "  minikube dashboard            — Open Kubernetes dashboard"
echo "  helm uninstall todo-app       — Remove deployment"
