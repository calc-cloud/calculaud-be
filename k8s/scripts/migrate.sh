#!/bin/bash
set -e

# Defaults
NAMESPACE="calculaud"
IMAGE="calculaud/calculaud-be:latest"
COMMAND="upgrade"
REVISION="head"

# Parse args
while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--namespace) NAMESPACE="$2"; shift 2 ;;
        -i|--image) IMAGE="$2"; shift 2 ;;
        -c|--command) COMMAND="$2"; shift 2 ;;
        -r|--revision) REVISION="$2"; shift 2 ;;
        -h|--help)
            echo "Usage: $0 [-n namespace] [-i image] [-c command] [-r revision]"
            echo "  -c: upgrade (default), downgrade, current, history"
            exit 0 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# Build alembic command
case $COMMAND in
    upgrade|downgrade) ALEMBIC_CMD="alembic $COMMAND $REVISION" ;;
    current|history|heads) ALEMBIC_CMD="alembic $COMMAND" ;;
    *) echo "Invalid command: $COMMAND"; exit 1 ;;
esac

echo "Running migration: $ALEMBIC_CMD"

# Cleanup existing job
kubectl delete job calculaud-migration -n "$NAMESPACE" --ignore-not-found=true

# Run migration
kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: calculaud-migration
  namespace: $NAMESPACE
spec:
  ttlSecondsAfterFinished: 300
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: migrate
        image: $IMAGE
        command: ["/bin/sh", "-c", "cd /app && $ALEMBIC_CMD"]
        envFrom:
        - configMapRef:
            name: calculaud-be-config
        - secretRef:
            name: calculaud-be-secret
        resources:
          requests: { memory: "128Mi", cpu: "100m" }
          limits: { memory: "256Mi", cpu: "500m" }
EOF

# Wait and show logs
kubectl wait --for=condition=complete job/calculaud-migration -n "$NAMESPACE" --timeout=300s
kubectl logs job/calculaud-migration -n "$NAMESPACE"
echo "Migration completed!"