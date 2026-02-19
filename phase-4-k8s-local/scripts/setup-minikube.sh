#!/bin/bash
set -euo pipefail

echo "=== Setting up Minikube for Todo App ==="

# Start minikube if not running
if ! minikube status 2>/dev/null | grep -q "Running"; then
    echo "Starting Minikube..."
    minikube start --driver=docker --cpus=2 --memory=4096
else
    echo "Minikube is already running."
fi

# Enable required addons
echo "Enabling addons..."
minikube addons enable ingress
minikube addons enable metrics-server
minikube addons enable dashboard

# Wait for ingress controller to be ready
echo "Waiting for ingress controller..."
kubectl wait --namespace ingress-nginx \
    --for=condition=ready pod \
    --selector=app.kubernetes.io/component=controller \
    --timeout=120s 2>/dev/null || echo "Ingress controller may still be starting..."

# Verify
echo ""
echo "Verifying cluster..."
kubectl cluster-info
kubectl get nodes

MINIKUBE_IP=$(minikube ip)
echo ""
echo "=== Minikube is ready! ==="
echo "Dashboard:  minikube dashboard"
echo "Minikube IP: $MINIKUBE_IP"
echo ""
echo "Add to /etc/hosts (or C:\\Windows\\System32\\drivers\\etc\\hosts on Windows):"
echo "  $MINIKUBE_IP todo.local"
