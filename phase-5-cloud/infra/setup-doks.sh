#!/usr/bin/env bash
# setup-doks.sh — Manual DigitalOcean Kubernetes (DOKS) cluster setup
# Prerequisites: doctl CLI authenticated, kubectl installed

set -euo pipefail

CLUSTER_NAME="${CLUSTER_NAME:-todo-app-doks}"
REGION="${REGION:-nyc1}"
NODE_SIZE="${NODE_SIZE:-s-2vcpu-4gb}"
NODE_COUNT="${NODE_COUNT:-2}"
K8S_VERSION="${K8S_VERSION:-1.28.2-do.0}"

echo "=== Creating DOKS cluster: ${CLUSTER_NAME} ==="
echo "Region: ${REGION}, Nodes: ${NODE_COUNT} x ${NODE_SIZE}"

doctl kubernetes cluster create "${CLUSTER_NAME}" \
  --region "${REGION}" \
  --version "${K8S_VERSION}" \
  --size "${NODE_SIZE}" \
  --count "${NODE_COUNT}" \
  --wait

echo "=== Fetching kubeconfig ==="
doctl kubernetes cluster kubeconfig save "${CLUSTER_NAME}"

echo "=== Verifying cluster ==="
kubectl get nodes
kubectl cluster-info

echo "=== DOKS cluster setup complete ==="
echo "Next steps:"
echo "  1. Run scripts/setup-dapr.sh to install Dapr"
echo "  2. Run scripts/setup-kafka.sh to deploy Kafka"
echo "  3. Run scripts/deploy-doks.sh to deploy the application"
