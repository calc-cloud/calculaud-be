#!/bin/bash

# Kubernetes deployment script for Calculaud Backend
# Supports deployment to different environments and clusters

set -e

# Default values
ENVIRONMENT="dev"
NAMESPACE="calculaud"
HELM_RELEASE_NAME="calculaud-be"
CHART_PATH="k8s/helm/calculaud-be"
VALUES_FILE=""
CONFIG_FILE=""
DRY_RUN=false
UPGRADE_TIMEOUT="600s"
CREATE_NAMESPACE=true
AUTO_PROCESS_CONFIG=true

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
    echo "  -e, --environment ENV    Environment to deploy to (dev, prod, eks, onprem) [default: dev]"
    echo "  -n, --namespace NS       Kubernetes namespace [default: calculaud]"
    echo "  -r, --release NAME       Helm release name [default: calculaud-be]"
    echo "  -c, --chart PATH         Path to Helm chart [default: k8s/helm/calculaud-be]"
    echo "  -f, --values FILE        Additional values file"
    echo "  -d, --dry-run           Perform a dry run without installing"
    echo "  -t, --timeout DURATION   Timeout for deployment [default: 600s]"
    echo "      --no-create-ns      Don't create namespace if it doesn't exist"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -e dev                    # Deploy to development"
    echo "  $0 -e prod -n calculaud-prod # Deploy to production"
    echo "  $0 -e eks                    # Deploy to AWS EKS"
    echo "  $0 -e onprem                 # Deploy to on-premises"
    echo "  $0 -d                        # Dry run deployment"
    echo "  $0 -f my-values.yaml         # Use custom values file"
    echo ""
    echo "For on-premises deployment, ensure external PostgreSQL and S3 storage are available"
    echo "  and update the values file with your specific configuration."
    exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -r|--release)
            HELM_RELEASE_NAME="$2"
            shift 2
            ;;
        -c|--chart)
            CHART_PATH="$2"
            shift 2
            ;;
        -f|--values)
            VALUES_FILE="$2"
            shift 2
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -t|--timeout)
            UPGRADE_TIMEOUT="$2"
            shift 2
            ;;
        --no-create-ns)
            CREATE_NAMESPACE=false
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

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|prod|eks|onprem)$ ]]; then
    print_message $RED "Error: Environment must be 'dev', 'prod', 'eks', or 'onprem'"
    exit 1
fi

# Check if required tools are installed
check_dependencies() {
    print_message $BLUE "Checking dependencies..."
    
    if ! command -v kubectl &> /dev/null; then
        print_message $RED "Error: kubectl is not installed"
        exit 1
    fi
    
    if ! command -v helm &> /dev/null; then
        print_message $RED "Error: helm is not installed"
        exit 1
    fi
    
    print_message $GREEN "✓ All dependencies are installed"
}

# Check kubectl context
check_context() {
    print_message $BLUE "Checking Kubernetes context..."
    
    CURRENT_CONTEXT=$(kubectl config current-context)
    print_message $YELLOW "Current context: $CURRENT_CONTEXT"
    
    # Verify cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        print_message $RED "Error: Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    print_message $GREEN "✓ Connected to Kubernetes cluster"
}

# Environment-specific checks and setup
environment_setup() {
    case $ENVIRONMENT in
        eks)
            print_message $BLUE "Setting up for AWS EKS deployment..."
            
            # Check AWS CLI
            if ! command -v aws &> /dev/null; then
                print_message $YELLOW "Warning: AWS CLI not found. Make sure you have proper AWS access configured."
            fi
            
            # Check for EKS-specific tools
            if command -v eksctl &> /dev/null; then
                print_message $GREEN "✓ eksctl found"
            else
                print_message $YELLOW "Warning: eksctl not found. Install for easier EKS management."
            fi
            
            # Verify EKS cluster context
            if kubectl config current-context | grep -q "arn:aws:eks"; then
                print_message $GREEN "✓ EKS cluster context detected"
            else
                print_message $YELLOW "Warning: Current context may not be an EKS cluster"
            fi
            ;;
        onprem)
            print_message $BLUE "Setting up for on-premises deployment..."
            
            # Check for common on-premises requirements
            if kubectl get storageclass &> /dev/null; then
                print_message $GREEN "✓ Storage classes available"
            else
                print_message $YELLOW "Warning: No storage classes found. You may need to configure persistent storage."
            fi
            
            # Check for ingress controller
            if kubectl get ingressclass &> /dev/null; then
                print_message $GREEN "✓ Ingress controller detected"
            else
                print_message $YELLOW "Warning: No ingress controller found. Consider installing nginx-ingress or using NodePort service."
            fi
            
            # Check for load balancer
            if kubectl get svc -A | grep -q "LoadBalancer"; then
                print_message $GREEN "✓ Load balancer service detected"
            else
                print_message $YELLOW "Warning: No LoadBalancer services found. Consider installing MetalLB for on-premises load balancing."
            fi
            
            # On-premises deployment uses external PostgreSQL and S3 storage
            print_message $GREEN "✓ On-premises deployment configured for external services"
            print_message $BLUE "Note: Ensure external PostgreSQL and S3-compatible storage are available"
            ;;
        dev|prod)
            print_message $BLUE "Setting up for $ENVIRONMENT environment..."
            ;;
    esac
}

# Create namespace if it doesn't exist
create_namespace() {
    if [[ "$CREATE_NAMESPACE" == "true" ]]; then
        print_message $BLUE "Checking namespace: $NAMESPACE"
        
        if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
            print_message $YELLOW "Creating namespace: $NAMESPACE"
            if [[ "$DRY_RUN" == "false" ]]; then
                kubectl create namespace "$NAMESPACE"
            fi
        fi
        
        print_message $GREEN "✓ Namespace ready: $NAMESPACE"
    fi
}

# Validate Helm chart
validate_chart() {
    print_message $BLUE "Validating Helm chart..."
    
    if [[ ! -d "$CHART_PATH" ]]; then
        print_message $RED "Error: Chart path does not exist: $CHART_PATH"
        exit 1
    fi
    
    if [[ ! -f "$CHART_PATH/Chart.yaml" ]]; then
        print_message $RED "Error: Chart.yaml not found in: $CHART_PATH"
        exit 1
    fi
    
    # Helm lint
    if ! helm lint "$CHART_PATH" &> /dev/null; then
        print_message $RED "Error: Helm chart failed validation"
        helm lint "$CHART_PATH"
        exit 1
    fi
    
    print_message $GREEN "✓ Helm chart is valid"
}

# Deploy application
deploy() {
    print_message $BLUE "Deploying Calculaud Backend..."
    
    # Build helm command
    HELM_CMD="helm upgrade --install"
    HELM_CMD="$HELM_CMD $HELM_RELEASE_NAME $CHART_PATH"
    HELM_CMD="$HELM_CMD --namespace $NAMESPACE"
    HELM_CMD="$HELM_CMD --timeout $UPGRADE_TIMEOUT"
    HELM_CMD="$HELM_CMD --wait"
    
    # Add environment-specific values file
    ENV_VALUES_FILE="$CHART_PATH/values-$ENVIRONMENT.yaml"
    if [[ -f "$ENV_VALUES_FILE" ]]; then
        HELM_CMD="$HELM_CMD -f $ENV_VALUES_FILE"
        print_message $YELLOW "Using environment values: $ENV_VALUES_FILE"
    fi
    
    # Add custom values file if provided
    if [[ -n "$VALUES_FILE" && -f "$VALUES_FILE" ]]; then
        HELM_CMD="$HELM_CMD -f $VALUES_FILE"
        print_message $YELLOW "Using custom values: $VALUES_FILE"
    fi
    
    # Add dry-run flag if requested
    if [[ "$DRY_RUN" == "true" ]]; then
        HELM_CMD="$HELM_CMD --dry-run"
        print_message $YELLOW "Performing dry run..."
    fi
    
    # Execute deployment
    print_message $BLUE "Executing: $HELM_CMD"
    
    if eval "$HELM_CMD"; then
        if [[ "$DRY_RUN" == "false" ]]; then
            print_message $GREEN "✓ Deployment successful!"
        else
            print_message $GREEN "✓ Dry run completed successfully!"
        fi
    else
        print_message $RED "✗ Deployment failed!"
        exit 1
    fi
}

# Show deployment status
show_status() {
    if [[ "$DRY_RUN" == "false" ]]; then
        print_message $BLUE "Checking deployment status..."
        
        # Show Helm release status
        helm status "$HELM_RELEASE_NAME" -n "$NAMESPACE"
        
        # Show pod status
        print_message $BLUE "Pod status:"
        kubectl get pods -n "$NAMESPACE" -l "app.kubernetes.io/name=calculaud-be"
        
        # Show service status
        print_message $BLUE "Service status:"
        kubectl get svc -n "$NAMESPACE" -l "app.kubernetes.io/name=calculaud-be"
        
        # Show ingress status (if enabled)
        if kubectl get ingress -n "$NAMESPACE" &> /dev/null; then
            print_message $BLUE "Ingress status:"
            kubectl get ingress -n "$NAMESPACE"
        fi
    fi
}

# Main execution
main() {
    print_message $GREEN "🚀 Calculaud Backend Deployment Script"
    print_message $BLUE "Environment: $ENVIRONMENT"
    print_message $BLUE "Namespace: $NAMESPACE"
    print_message $BLUE "Release: $HELM_RELEASE_NAME"
    echo ""
    
    check_dependencies
    check_context
    environment_setup
    create_namespace
    validate_chart
    deploy
    show_status
    
    if [[ "$DRY_RUN" == "false" ]]; then
        print_message $GREEN "🎉 Deployment completed successfully!"
        print_message $YELLOW "You can check the application status with:"
        print_message $YELLOW "  kubectl get pods -n $NAMESPACE"
        print_message $YELLOW "  kubectl logs -f deployment/calculaud-be -n $NAMESPACE"
    fi
}

# Run main function
main "$@"