#!/bin/bash

# On-Premises Packaging Script for Calculaud Backend
# Creates a complete deployment package for air-gapped environments

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
PACKAGE_DIR="$PROJECT_ROOT/onprem-package"
OUTPUT_FILE="calculaud-onprem-$(date +%Y%m%d-%H%M%S).tar.gz"
TEMP_DIR=$(mktemp -d)

# Docker images to package (external services assumed to be already available)
DOCKER_IMAGES=(
    "calculaud/calculaud-be:latest"
)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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
    echo "  -o, --output FILE        Output filename [default: auto-generated with timestamp]"
    echo "  -d, --package-dir DIR    Package directory [default: ./onprem-package]"
    echo "  --skip-docker           Skip Docker image packaging"
    echo "  --skip-build            Skip building application Docker image"
    echo "  --include-data          Include sample data and seeds"
    echo "  --compress-level LEVEL  Compression level 1-9 [default: 6]"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                      Create package with default settings"
    echo "  $0 -o my-package.tar.gz Create package with custom name"
    echo "  $0 --skip-docker        Create package without Docker images"
    exit 1
}

# Parse command line arguments
SKIP_DOCKER=false
SKIP_BUILD=false
INCLUDE_DATA=false
COMPRESS_LEVEL=6

while [[ $# -gt 0 ]]; do
    case $1 in
        -o|--output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        -d|--package-dir)
            PACKAGE_DIR="$2"
            shift 2
            ;;
        --skip-docker)
            SKIP_DOCKER=true
            shift
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --include-data)
            INCLUDE_DATA=true
            shift
            ;;
        --compress-level)
            COMPRESS_LEVEL="$2"
            shift 2
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

# Cleanup function
cleanup() {
    print_message $BLUE "🧹 Cleaning up temporary files..."
    rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

# Check prerequisites
check_prerequisites() {
    print_message $BLUE "📋 Checking prerequisites..."
    
    if [[ "$SKIP_DOCKER" == "false" ]]; then
        if ! command -v docker &> /dev/null; then
            print_message $RED "Error: Docker is required for packaging images"
            print_message $YELLOW "Use --skip-docker to create package without Docker images"
            exit 1
        fi
    fi
    
    if ! command -v tar &> /dev/null; then
        print_message $RED "Error: tar is required for creating packages"
        exit 1
    fi
    
    print_message $GREEN "✅ Prerequisites check passed"
}

# Build application Docker image
build_docker_image() {
    if [[ "$SKIP_BUILD" == "true" ]]; then
        print_message $YELLOW "⏭️ Skipping Docker image build"
        return
    fi
    
    print_message $BLUE "🔨 Building Calculaud application Docker image..."
    cd "$PROJECT_ROOT"
    
    # Build with version tag
    VERSION=$(date +%Y%m%d-%H%M%S)
    docker build -t calculaud/calculaud-be:latest -t "calculaud/calculaud-be:$VERSION" \
        --build-arg VERSION="$VERSION" .
    
    print_message $GREEN "✅ Docker image built successfully"
}

# Package Docker images
package_docker_images() {
    if [[ "$SKIP_DOCKER" == "true" ]]; then
        print_message $YELLOW "⏭️ Skipping Docker image packaging"
        return
    fi
    
    print_message $BLUE "📦 Packaging Docker images..."
    
    local docker_dir="$PACKAGE_DIR/docker-images"
    mkdir -p "$docker_dir"
    
    for image in "${DOCKER_IMAGES[@]}"; do
        print_message $BLUE "  📦 Saving $image..."
        local filename=$(echo "$image" | sed 's/[/:.]/-/g')
        
        if docker inspect "$image" &>/dev/null; then
            docker save "$image" | gzip -"$COMPRESS_LEVEL" > "$docker_dir/${filename}.tar.gz"
            print_message $GREEN "  ✅ Saved $image"
        else
            print_message $YELLOW "  ⚠️ Image $image not found locally, pulling..."
            docker pull "$image"
            docker save "$image" | gzip -"$COMPRESS_LEVEL" > "$docker_dir/${filename}.tar.gz"
            print_message $GREEN "  ✅ Pulled and saved $image"
        fi
    done
    
    # Create image loading script
    cat > "$docker_dir/load-images.sh" << 'EOF'
#!/bin/bash
# Script to load all Docker images

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Loading Docker images..."

for image_file in "$SCRIPT_DIR"/*.tar.gz; do
    if [[ -f "$image_file" ]]; then
        echo "📦 Loading $(basename "$image_file")..."
        gunzip -c "$image_file" | docker load
    fi
done

echo "✅ All Docker images loaded successfully"
echo ""
echo "📋 Loaded images:"
docker images --filter "label=calculaud" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
EOF
    
    chmod +x "$docker_dir/load-images.sh"
    print_message $GREEN "✅ Docker images packaged successfully"
}

# Copy application files
copy_application_files() {
    print_message $BLUE "📄 Copying application files..."
    
    # Create application directory
    local app_dir="$PACKAGE_DIR/app"
    mkdir -p "$app_dir"
    
    # Copy essential application files
    cp -r "$PROJECT_ROOT/app" "$app_dir/"
    cp -r "$PROJECT_ROOT/alembic" "$app_dir/"
    cp -r "$PROJECT_ROOT/tests" "$app_dir/"
    cp "$PROJECT_ROOT/requirements.txt" "$app_dir/"
    cp "$PROJECT_ROOT/Dockerfile" "$app_dir/"
    cp "$PROJECT_ROOT/alembic.ini" "$app_dir/"
    cp "$PROJECT_ROOT/pytest.ini" "$app_dir/"
    cp "$PROJECT_ROOT/main.py" "$app_dir/" 2>/dev/null || true
    
    # Copy README and documentation
    cp "$PROJECT_ROOT/README.md" "$app_dir/" 2>/dev/null || true
    cp "$PROJECT_ROOT/CLAUDE.md" "$app_dir/" 2>/dev/null || true
    
    print_message $GREEN "✅ Application files copied"
}

# Copy Kubernetes files
copy_kubernetes_files() {
    print_message $BLUE "🎛️ Copying Kubernetes files..."
    
    # Copy entire k8s directory
    cp -r "$PROJECT_ROOT/k8s" "$PACKAGE_DIR/"
    
    # Make scripts executable
    chmod +x "$PACKAGE_DIR/k8s/scripts"/*.sh
    
    print_message $GREEN "✅ Kubernetes files copied"
}

# Copy configuration files
copy_config_files() {
    print_message $BLUE "⚙️ Copying configuration files..."
    
    # Copy configuration templates and examples
    local config_dir="$PACKAGE_DIR/config"
    mkdir -p "$config_dir"
    
    # Copy Kubernetes ConfigMap and Secret templates
    if [[ -d "$PROJECT_ROOT/k8s/config" ]]; then
        cp -r "$PROJECT_ROOT/k8s/config"/* "$config_dir/"
        print_message $BLUE "  ✅ ConfigMap and Secret templates copied"
    fi
    
    # Copy any other configuration files
    if [[ -f "$PROJECT_ROOT/config.yaml.example" ]]; then
        cp "$PROJECT_ROOT/config.yaml.example" "$config_dir/"
    fi
    
    # Make configuration scripts executable
    chmod +x "$config_dir"/*.sh 2>/dev/null || true
    
    print_message $GREEN "✅ Configuration files copied"
}

# Create configuration files
create_config_files() {
    print_message $BLUE "⚙️ Creating configuration files..."
    
    local config_dir="$PACKAGE_DIR/config"
    mkdir -p "$config_dir"
    
    # Create Nginx configuration
    cat > "$config_dir/nginx.conf" << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server calculaud-app:8000;
    }
    
    server {
        listen 80;
        server_name _;
        
        client_max_body_size 512M;
        
        location / {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        location /health {
            proxy_pass http://backend/health;
            access_log off;
        }
    }
}
EOF
    
    # Create Prometheus configuration
    cat > "$config_dir/prometheus.yml" << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'calculaud-app'
    static_configs:
      - targets: ['calculaud-app:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']
    metrics_path: '/metrics'
    scrape_interval: 60s

  - job_name: 's3-storage'
    static_configs:
      - targets: ['your-s3-service:443']
    metrics_path: '/metrics'
    scrape_interval: 60s
EOF
    
    print_message $GREEN "✅ Configuration files created"
}

# Include sample data
include_sample_data() {
    if [[ "$INCLUDE_DATA" == "false" ]]; then
        print_message $YELLOW "⏭️ Skipping sample data"
        return
    fi
    
    print_message $BLUE "📊 Including sample data..."
    
    local data_dir="$PACKAGE_DIR/data"
    mkdir -p "$data_dir"
    
    # Copy seed data if it exists
    if [[ -f "$PROJECT_ROOT/seeds/sample_data.sql" ]]; then
        cp "$PROJECT_ROOT/seeds"/*.sql "$data_dir/"
    fi
    
    # Create sample environment file
    cat > "$data_dir/.env.sample" << 'EOF'
# Sample environment configuration for testing
POSTGRES_PASSWORD=TestPassword123!
MINIO_ACCESS_KEY=testuser
MINIO_SECRET_KEY=TestSecret123!
GRAFANA_PASSWORD=admin123
LOG_LEVEL=DEBUG
EOF
    
    print_message $GREEN "✅ Sample data included"
}

# Create deployment documentation
create_documentation() {
    print_message $BLUE "📚 Creating deployment documentation..."
    
    local docs_dir="$PACKAGE_DIR/docs"
    mkdir -p "$docs_dir"
    
    cat > "$docs_dir/DEPLOYMENT_GUIDE.md" << 'EOF'
# Calculaud Backend - On-Premises Deployment Guide

## Quick Start

### Prerequisites
- Kubernetes cluster (1.24+) with kubectl configured
- Helm 3.8+
- Docker (for loading images)
- At least 8GB RAM and 50GB disk space

### Option 1: Automated Installation (Recommended)

1. **Run Automated Installer**:
   ```bash
   ./install.sh
   ```

   This will:
   - Check prerequisites (kubectl, helm, docker)
   - Load Docker images into the cluster
   - Deploy to Kubernetes with Helm
   - Run database migrations
   - Show access information

### Option 2: Manual Kubernetes Deployment

1. **Load Docker Images**:
   ```bash
   cd docker-images
   ./load-images.sh
   ```

2. **Configure Application**:
   ```bash
   cd config
   # Copy and customize configuration templates
   cp configmap-template.yaml configmap.yaml
   cp secret-template.yaml secret.yaml
   
   # Edit configuration files with your values
   nano configmap.yaml  # Non-sensitive configuration
   nano secret.yaml     # Passwords and keys (never commit this!)
   
   # Apply configuration to Kubernetes
   ./apply-config.sh -n calculaud
   ```

3. **Deploy with Helm**:
   ```bash
   cd k8s
   ./scripts/deploy.sh -e onprem -n calculaud
   ```

4. **Run Migrations**:
   ```bash
   ./scripts/migrate.sh -n calculaud
   ```

## Access Points

- **Application**: Via NodePort, LoadBalancer, or port-forward
- **API Documentation**: {application-url}/docs
- **S3 Storage**: External service (configuration required)

## Troubleshooting

### Common Issues

1. **Port Conflicts**: Modify ports in docker-compose.onprem.yml
2. **Insufficient Resources**: Reduce replica counts in configuration
3. **Network Issues**: Check firewall and proxy settings

### Support

Check the logs for detailed error information:
```bash
kubectl logs -f deployment/calculaud-be -n calculaud
```

For PostgreSQL logs:
```bash
kubectl logs -f deployment/postgres -n calculaud
```
EOF
    
    print_message $GREEN "✅ Documentation created"
}

# Create installation script
create_installer() {
    print_message $BLUE "🚀 Creating installation script..."
    
    cat > "$PACKAGE_DIR/install.sh" << 'EOF'
#!/bin/bash

# Calculaud On-Premises Installation Script
# Automated Kubernetes deployment for air-gapped environments

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAMESPACE="calculaud"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_message $GREEN "🚀 Calculaud Backend - On-Premises Kubernetes Installer"
echo ""

# Check required tools
if ! command -v kubectl &> /dev/null; then
    print_message $RED "Error: kubectl is required but not installed"
    exit 1
fi

if ! command -v helm &> /dev/null; then
    print_message $RED "Error: Helm is required but not installed"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    print_message $RED "Error: Docker is required for loading images"
    exit 1
fi

print_message $GREEN "✅ Required tools are available"

# Check Kubernetes connectivity
if ! kubectl cluster-info &> /dev/null; then
    print_message $RED "Error: Cannot connect to Kubernetes cluster"
    print_message $YELLOW "Please ensure kubectl is configured and cluster is accessible"
    exit 1
fi

print_message $GREEN "✅ Kubernetes cluster is accessible"

# Load Docker images if available
if [[ -d "$SCRIPT_DIR/docker-images" ]]; then
    print_message $BLUE "📦 Loading Docker images..."
    cd "$SCRIPT_DIR/docker-images"
    ./load-images.sh
    cd "$SCRIPT_DIR"
else
    print_message $YELLOW "⚠️ Docker images directory not found, assuming images are available in cluster"
fi

# Apply configuration (ConfigMaps and Secrets)
if [[ -d "$SCRIPT_DIR/config" ]]; then
    print_message $BLUE "⚙️ Setting up configuration..."
    cd "$SCRIPT_DIR/config"
    
    # Check if configuration files exist, if not copy from templates
    if [[ ! -f "configmap.yaml" && -f "configmap-template.yaml" ]]; then
        print_message $YELLOW "Creating configmap.yaml from template..."
        cp configmap-template.yaml configmap.yaml
        print_message $YELLOW "⚠️ Please customize config/configmap.yaml with your specific values"
    fi
    
    if [[ ! -f "secret.yaml" && -f "secret-template.yaml" ]]; then
        print_message $YELLOW "Creating secret.yaml from template..."
        cp secret-template.yaml secret.yaml
        print_message $YELLOW "⚠️ Please customize config/secret.yaml with your passwords and keys"
    fi
    
    # Apply configuration if it exists
    if [[ -f "configmap.yaml" && -f "secret.yaml" ]]; then
        ./apply-config.sh -n "$NAMESPACE"
    else
        print_message $YELLOW "Configuration files not found, skipping configuration setup"
        print_message $YELLOW "You can set up configuration later by running config/apply-config.sh"
    fi
    
    cd "$SCRIPT_DIR"
fi

# Deploy to Kubernetes
print_message $BLUE "🚀 Deploying Calculaud to Kubernetes..."
cd "$SCRIPT_DIR/k8s"
./scripts/deploy.sh -e onprem -n "$NAMESPACE"

# Wait for deployment to be ready
print_message $BLUE "⏳ Waiting for deployment to be ready..."
kubectl wait --for=condition=available deployment/calculaud-be -n "$NAMESPACE" --timeout=300s

# Run migrations
print_message $BLUE "🔄 Running database migrations..."
./scripts/migrate.sh -n "$NAMESPACE"

# Show final status
print_message $BLUE "📊 Final deployment status:"
kubectl get pods,svc,ingress -n "$NAMESPACE"

# Show access information
SERVICE_TYPE=$(kubectl get svc calculaud-be -n "$NAMESPACE" -o jsonpath='{.spec.type}')
if [[ "$SERVICE_TYPE" == "NodePort" ]]; then
    NODE_PORT=$(kubectl get svc calculaud-be -n "$NAMESPACE" -o jsonpath='{.spec.ports[0].nodePort}')
    NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
    print_message $GREEN "🎉 Installation completed successfully!"
    print_message $BLUE "Access your application at: http://$NODE_IP:$NODE_PORT"
    print_message $BLUE "API documentation at: http://$NODE_IP:$NODE_PORT/docs"
elif [[ "$SERVICE_TYPE" == "LoadBalancer" ]]; then
    print_message $GREEN "🎉 Installation completed successfully!"
    print_message $BLUE "Waiting for LoadBalancer IP assignment..."
    kubectl get svc calculaud-be -n "$NAMESPACE"
    print_message $BLUE "API documentation available at /docs endpoint"
else
    print_message $GREEN "🎉 Installation completed successfully!"
    print_message $BLUE "Use port-forward to access: kubectl port-forward svc/calculaud-be 8000:80 -n $NAMESPACE"
    print_message $BLUE "Then access at: http://localhost:8000"
fi
EOF
    
    chmod +x "$PACKAGE_DIR/install.sh"
    
    print_message $GREEN "✅ Installation script created"
}

# Create package manifest
create_manifest() {
    print_message $BLUE "📋 Creating package manifest..."
    
    local manifest_file="$PACKAGE_DIR/PACKAGE_MANIFEST.txt"
    
    cat > "$manifest_file" << EOF
Calculaud Backend On-Premises Package
=====================================

Package Information:
- Created: $(date)
- Version: $(date +%Y%m%d-%H%M%S)
- Size: $(du -sh "$PACKAGE_DIR" | cut -f1) 2>/dev/null || echo "Calculating..."

Contents:
├── app/                    # Application source code
├── k8s/                    # Kubernetes Helm charts
├── config/                 # Configuration files
├── docs/                   # Deployment documentation
├── docker-images/          # Docker images (if included)
$(if [[ "$INCLUDE_DATA" == "true" ]]; then echo "├── data/                   # Sample data and configurations"; fi)
├── docker-compose.onprem.yml      # Docker Compose configuration
├── .env.onprem.template    # Environment template
├── docker-compose.scripts.sh      # Deployment scripts
├── install.sh              # Automated installer
└── PACKAGE_MANIFEST.txt    # This file

Docker Images Included:
EOF
    
    if [[ "$SKIP_DOCKER" == "false" ]]; then
        for image in "${DOCKER_IMAGES[@]}"; do
            echo "- $image" >> "$manifest_file"
        done
    else
        echo "- Docker images not included (--skip-docker used)" >> "$manifest_file"
    fi
    
    cat >> "$manifest_file" << EOF

Deployment Options:
1. Docker Compose (Simple): ./install.sh
2. Kubernetes: See docs/DEPLOYMENT_GUIDE.md

System Requirements:
- CPU: 2+ cores
- RAM: 4+ GB (application only)
- Storage: 20+ GB (application only)
- OS: Linux with Docker support
- External PostgreSQL database
- External S3-compatible storage

For support and documentation, see:
- docs/DEPLOYMENT_GUIDE.md
- k8s/README.md
EOF
    
    print_message $GREEN "✅ Package manifest created"
}

# Create final package
create_final_package() {
    print_message $BLUE "📦 Creating final package archive..."
    
    cd "$(dirname "$PACKAGE_DIR")"
    
    # Create compressed archive
    tar -czf "$OUTPUT_FILE" -C "$PACKAGE_DIR" .
    
    local file_size=$(du -sh "$OUTPUT_FILE" | cut -f1)
    print_message $GREEN "✅ Package created: $OUTPUT_FILE ($file_size)"
    
    # Generate checksums
    if command -v sha256sum &> /dev/null; then
        sha256sum "$OUTPUT_FILE" > "$OUTPUT_FILE.sha256"
        print_message $GREEN "✅ SHA256 checksum: $OUTPUT_FILE.sha256"
    elif command -v shasum &> /dev/null; then
        shasum -a 256 "$OUTPUT_FILE" > "$OUTPUT_FILE.sha256"
        print_message $GREEN "✅ SHA256 checksum: $OUTPUT_FILE.sha256"
    fi
}

# Main execution
main() {
    print_message $GREEN "🏗️ Calculaud On-Premises Package Builder"
    print_message $BLUE "Output: $OUTPUT_FILE"
    print_message $BLUE "Package directory: $PACKAGE_DIR"
    echo ""
    
    check_prerequisites
    
    # Clean and create package directory
    rm -rf "$PACKAGE_DIR"
    mkdir -p "$PACKAGE_DIR"
    
    build_docker_image
    package_docker_images
    copy_application_files
    copy_kubernetes_files
    copy_config_files
    create_config_files
    include_sample_data
    create_documentation
    create_installer
    create_manifest
    create_final_package
    
    # Cleanup package directory
    rm -rf "$PACKAGE_DIR"
    
    print_message $GREEN "🎉 On-premises package created successfully!"
    print_message $BLUE "Package: $OUTPUT_FILE"
    print_message $YELLOW "Transfer this file to your on-premises environment and run:"
    print_message $YELLOW "  tar -xzf $OUTPUT_FILE && cd $(basename "$OUTPUT_FILE" .tar.gz) && ./install.sh"
}

# Run main function
main "$@"