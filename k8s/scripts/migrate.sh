#!/bin/bash

# Database migration script for Calculaud Backend in Kubernetes
# Runs Alembic migrations using a Kubernetes Job

set -e

# Default values
NAMESPACE="calculaud"
IMAGE="calculaud/calculaud-be:latest"
JOB_NAME="calculaud-migration"
MIGRATION_COMMAND="upgrade"
TARGET_REVISION="head"
TIMEOUT="600s"
CLEANUP=true

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to display usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -n, --namespace NS       Kubernetes namespace [default: calculaud]"
    echo "  -i, --image IMAGE        Docker image to use [default: calculaud/calculaud-be:latest]"
    echo "  -j, --job-name NAME      Migration job name [default: calculaud-migration]"
    echo "  -c, --command CMD        Migration command (upgrade, downgrade, current, history) [default: upgrade]"
    echo "  -r, --revision REV       Target revision [default: head]"
    echo "  -t, --timeout DURATION   Job timeout [default: 600s]"
    echo "      --no-cleanup         Don't cleanup job after completion"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                              # Run upgrade to head"
    echo "  $0 -c current                   # Show current revision"
    echo "  $0 -c history                   # Show migration history"
    echo "  $0 -c downgrade -r -1           # Downgrade one revision"
    echo "  $0 -c upgrade -r abc123         # Upgrade to specific revision"
    exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -i|--image)
            IMAGE="$2"
            shift 2
            ;;
        -j|--job-name)
            JOB_NAME="$2"
            shift 2
            ;;
        -c|--command)
            MIGRATION_COMMAND="$2"
            shift 2
            ;;
        -r|--revision)
            TARGET_REVISION="$2"
            shift 2
            ;;
        -t|--timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --no-cleanup)
            CLEANUP=false
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option $1"
            usage
            ;;
    esac
done

# Validate migration command
if [[ ! "$MIGRATION_COMMAND" =~ ^(upgrade|downgrade|current|history|heads|show)$ ]]; then
    print_message $RED "Error: Invalid migration command. Must be one of: upgrade, downgrade, current, history, heads, show"
    exit 1
fi

# Check dependencies
check_dependencies() {
    print_message $BLUE "Checking dependencies..."
    
    if ! command -v kubectl &> /dev/null; then
        print_message $RED "Error: kubectl is not installed"
        exit 1
    fi
    
    print_message $GREEN "✓ Dependencies are installed"
}

# Check cluster connectivity
check_cluster() {
    print_message $BLUE "Checking Kubernetes cluster connectivity..."
    
    if ! kubectl cluster-info &> /dev/null; then
        print_message $RED "Error: Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    # Check if namespace exists
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        print_message $RED "Error: Namespace '$NAMESPACE' does not exist"
        exit 1
    fi
    
    print_message $GREEN "✓ Connected to cluster, namespace exists"
}

# Cleanup existing migration job
cleanup_job() {
    print_message $BLUE "Checking for existing migration job..."
    
    if kubectl get job "$JOB_NAME" -n "$NAMESPACE" &> /dev/null; then
        print_message $YELLOW "Cleaning up existing job: $JOB_NAME"
        kubectl delete job "$JOB_NAME" -n "$NAMESPACE" --ignore-not-found=true
        
        # Wait for job to be deleted
        while kubectl get job "$JOB_NAME" -n "$NAMESPACE" &> /dev/null; do
            print_message $YELLOW "Waiting for job cleanup..."
            sleep 2
        done
    fi
    
    print_message $GREEN "✓ Job cleanup completed"
}

# Create migration job
create_migration_job() {
    print_message $BLUE "Creating migration job..."
    
    # Build alembic command
    case $MIGRATION_COMMAND in
        upgrade|downgrade)
            ALEMBIC_CMD="alembic $MIGRATION_COMMAND $TARGET_REVISION"
            ;;
        current|history|heads)
            ALEMBIC_CMD="alembic $MIGRATION_COMMAND"
            ;;
        show)
            ALEMBIC_CMD="alembic show $TARGET_REVISION"
            ;;
    esac
    
    # Create job YAML
    cat << EOF | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: $JOB_NAME
  namespace: $NAMESPACE
  labels:
    app.kubernetes.io/name: calculaud-be
    app.kubernetes.io/component: migration
spec:
  ttlSecondsAfterFinished: 300
  template:
    metadata:
      labels:
        app.kubernetes.io/name: calculaud-be
        app.kubernetes.io/component: migration
    spec:
      restartPolicy: Never
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        runAsGroup: 1000
        fsGroup: 1000
      containers:
      - name: migrate
        image: $IMAGE
        command: ["/bin/sh", "-c"]
        args:
        - |
          echo "Starting database migration..."
          echo "Command: $ALEMBIC_CMD"
          cd /app
          $ALEMBIC_CMD
          echo "Migration completed successfully"
        env:
        # Database connection from secret
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: calculaud-be-secret
              key: DATABASE_URL
        # Other required environment variables
        - name: APP_NAME
          valueFrom:
            configMapKeyRef:
              name: calculaud-be-config
              key: APP_NAME
              optional: true
        - name: ENVIRONMENT
          valueFrom:
            configMapKeyRef:
              name: calculaud-be-config
              key: ENVIRONMENT
              optional: true
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "500m"
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          runAsNonRoot: true
          runAsUser: 1000
          capabilities:
            drop:
            - ALL
        volumeMounts:
        - name: tmp
          mountPath: /tmp
      volumes:
      - name: tmp
        emptyDir: {}
EOF
    
    print_message $GREEN "✓ Migration job created"
}

# Wait for job completion
wait_for_job() {
    print_message $BLUE "Waiting for migration job to complete (timeout: $TIMEOUT)..."
    
    # Wait for job to complete
    if kubectl wait --for=condition=complete job/"$JOB_NAME" -n "$NAMESPACE" --timeout="$TIMEOUT"; then
        print_message $GREEN "✓ Migration job completed successfully"
        return 0
    elif kubectl wait --for=condition=failed job/"$JOB_NAME" -n "$NAMESPACE" --timeout=10s; then
        print_message $RED "✗ Migration job failed"
        return 1
    else
        print_message $RED "✗ Migration job timed out"
        return 1
    fi
}

# Show job logs
show_logs() {
    print_message $BLUE "Migration job logs:"
    echo "----------------------------------------"
    
    # Get pod name for the job
    POD_NAME=$(kubectl get pods -n "$NAMESPACE" -l "job-name=$JOB_NAME" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
    
    if [[ -n "$POD_NAME" ]]; then
        kubectl logs "$POD_NAME" -n "$NAMESPACE" || true
    else
        print_message $YELLOW "No pod found for job $JOB_NAME"
    fi
    
    echo "----------------------------------------"
}

# Cleanup job after completion
cleanup_after_completion() {
    if [[ "$CLEANUP" == "true" ]]; then
        print_message $BLUE "Cleaning up migration job..."
        kubectl delete job "$JOB_NAME" -n "$NAMESPACE" --ignore-not-found=true
        print_message $GREEN "✓ Job cleanup completed"
    else
        print_message $YELLOW "Keeping migration job for inspection"
    fi
}

# Main execution
main() {
    print_message $GREEN "🗃️  Calculaud Database Migration Script"
    print_message $BLUE "Namespace: $NAMESPACE"
    print_message $BLUE "Image: $IMAGE"
    print_message $BLUE "Command: alembic $MIGRATION_COMMAND $TARGET_REVISION"
    echo ""
    
    check_dependencies
    check_cluster
    cleanup_job
    create_migration_job
    
    if wait_for_job; then
        show_logs
        print_message $GREEN "🎉 Database migration completed successfully!"
    else
        show_logs
        print_message $RED "❌ Database migration failed!"
        print_message $YELLOW "Check the logs above for details"
        
        # Don't cleanup on failure for debugging
        CLEANUP=false
    fi
    
    cleanup_after_completion
    
    if [[ "$CLEANUP" == "false" ]]; then
        print_message $YELLOW "To check job status: kubectl get job $JOB_NAME -n $NAMESPACE"
        print_message $YELLOW "To view logs: kubectl logs job/$JOB_NAME -n $NAMESPACE"
        print_message $YELLOW "To cleanup: kubectl delete job $JOB_NAME -n $NAMESPACE"
    fi
}

# Run main function
main "$@"