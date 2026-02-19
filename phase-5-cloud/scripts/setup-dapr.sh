#!/usr/bin/env bash
# setup-dapr.sh — Install Dapr on the Kubernetes cluster
set -euo pipefail

DAPR_VERSION="${DAPR_VERSION:-1.12}"
NAMESPACE="${NAMESPACE:-dapr-system}"

echo "=== Installing Dapr CLI (if not present) ==="
if ! command -v dapr &> /dev/null; then
  wget -q https://raw.githubusercontent.com/dapr/cli/master/install/install.sh -O - | /bin/bash
fi

echo "=== Installing Dapr on Kubernetes ==="
dapr init -k --runtime-version "${DAPR_VERSION}" --wait

echo "=== Verifying Dapr installation ==="
dapr status -k
kubectl get pods -n "${NAMESPACE}"

echo "=== Applying Dapr components ==="
kubectl apply -f "$(dirname "$0")/../k8s/dapr-components/"

echo "=== Dapr setup complete ==="
echo "Components installed:"
echo "  - pubsub (Kafka-backed)"
echo "  - statestore (Redis-backed)"
echo "  - subscription (task events)"
