#!/usr/bin/env bash
# setup-kafka.sh — Deploy Kafka on Kubernetes using Strimzi operator
set -euo pipefail

NAMESPACE="${NAMESPACE:-kafka}"
STRIMZI_VERSION="${STRIMZI_VERSION:-0.38.0}"

echo "=== Installing Strimzi Kafka Operator ==="
kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f "https://strimzi.io/install/latest?namespace=${NAMESPACE}" -n "${NAMESPACE}"

echo "=== Waiting for Strimzi operator to be ready ==="
kubectl wait --for=condition=Ready pod -l name=strimzi-cluster-operator -n "${NAMESPACE}" --timeout=300s

echo "=== Creating Kafka cluster ==="
cat <<'EOF' | kubectl apply -n "${NAMESPACE}" -f -
apiVersion: kafka.strimzi.io/v1beta2
kind: Kafka
metadata:
  name: todo-kafka
spec:
  kafka:
    version: 3.6.0
    replicas: 1
    listeners:
      - name: plain
        port: 9092
        type: internal
        tls: false
    config:
      offsets.topic.replication.factor: 1
      transaction.state.log.replication.factor: 1
      transaction.state.log.min.isr: 1
    storage:
      type: ephemeral
  zookeeper:
    replicas: 1
    storage:
      type: ephemeral
EOF

echo "=== Waiting for Kafka cluster to be ready ==="
kubectl wait kafka/todo-kafka --for=condition=Ready -n "${NAMESPACE}" --timeout=300s

echo "=== Creating Kafka topics ==="
cat <<'EOF' | kubectl apply -n "${NAMESPACE}" -f -
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: task-events
  labels:
    strimzi.io/cluster: todo-kafka
spec:
  partitions: 3
  replicas: 1
EOF

echo "=== Kafka setup complete ==="
echo "Broker address: todo-kafka-kafka-bootstrap.${NAMESPACE}:9092"
