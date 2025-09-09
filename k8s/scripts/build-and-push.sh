#!/bin/bash
# Docker Build and Push Script for Calculaud Backend
# Builds for AMD64 architecture and pushes to registry

set -e

# Get script directory for relative paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Get default values from Chart.yaml
DEFAULT_REPOSITORY=$("$SCRIPT_DIR/get-chart-config.sh" repository 2>/dev/null || echo "calculaud/calculaud-be")
DEFAULT_VERSION=$("$SCRIPT_DIR/get-chart-config.sh" version 2>/dev/null || echo "latest")

# Defaults
REPOSITORY="$DEFAULT_REPOSITORY"
VERSION="$DEFAULT_VERSION"
REGISTRY=""
DRY_RUN=false
PUSH_LATEST=true
CUSTOM_BUILD_ARGS=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -r|--repository)
            REPOSITORY="$2"
            shift 2
            ;;
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        --registry)
            REGISTRY="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --no-latest)
            PUSH_LATEST=false
            shift
            ;;
        --build-arg)
            CUSTOM_BUILD_ARGS="$CUSTOM_BUILD_ARGS --build-arg $2"
            shift 2
            ;;
        -h|--help)
            cat << EOF
Usage: $0 [OPTIONS]

Build and push Docker image for Calculaud Backend (AMD64 only)

Options:
  -r, --repository REPO    Docker repository [default: from Chart.yaml]
  -v, --version VERSION    Image version tag [default: from Chart.yaml]
  --registry REGISTRY      Registry prefix (e.g., myregistry.com/org)
  --dry-run               Build but don't push to registry
  --no-latest             Don't tag and push 'latest'
  --build-arg ARG=VALUE   Additional build arguments
  -h, --help              Show this help

Examples:
  $0                                    # Build and push using Chart.yaml defaults
  $0 --version 2.0.1                   # Build with custom version
  $0 --registry myregistry.com/org     # Push to custom registry
  $0 --dry-run                         # Build only, no push
  $0 --build-arg CUSTOM_VAR=value      # Pass custom build args
EOF
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Build full image names
if [[ -n "$REGISTRY" ]]; then
    FULL_REPOSITORY="$REGISTRY/$REPOSITORY"
else
    FULL_REPOSITORY="$REPOSITORY"
fi

VERSION_TAG="$FULL_REPOSITORY:$VERSION"
LATEST_TAG="$FULL_REPOSITORY:latest"

echo "🐳 Docker Build and Push Script"
echo "Repository: $FULL_REPOSITORY"
echo "Version: $VERSION"
echo "Dry Run: $DRY_RUN"
echo "Push Latest: $PUSH_LATEST"
echo ""

# Validation
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed or not in PATH"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Error: Docker daemon is not running"
    exit 1
fi

# Navigate to project root
cd "$PROJECT_ROOT"

# Build image
echo "🏗️ Building Docker image..."
echo "Tag: $VERSION_TAG"

docker build \
    --platform linux/amd64 \
    --build-arg VERSION="$VERSION" \
    $CUSTOM_BUILD_ARGS \
    -t "$VERSION_TAG" \
    .

echo "✅ Build completed successfully"

# Tag with latest if requested
if [[ "$PUSH_LATEST" == "true" ]]; then
    echo "🏷️ Tagging as latest..."
    docker tag "$VERSION_TAG" "$LATEST_TAG"
    echo "✅ Tagged as latest"
fi

# Exit early if dry run
if [[ "$DRY_RUN" == "true" ]]; then
    echo "🚫 Dry run mode - skipping push"
    echo "Built images:"
    docker images --filter "reference=$FULL_REPOSITORY" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
    exit 0
fi

# Push images
echo "📤 Pushing images to registry..."

# Push version tag
echo "Pushing $VERSION_TAG..."
if docker push "$VERSION_TAG"; then
    echo "✅ Successfully pushed $VERSION_TAG"
else
    echo "❌ Failed to push $VERSION_TAG"
    exit 1
fi

# Push latest tag if enabled
if [[ "$PUSH_LATEST" == "true" ]]; then
    echo "Pushing $LATEST_TAG..."
    if docker push "$LATEST_TAG"; then
        echo "✅ Successfully pushed $LATEST_TAG"
    else
        echo "❌ Failed to push $LATEST_TAG"
        exit 1
    fi
fi

echo ""
echo "🎉 Build and push completed successfully!"
echo "Images pushed:"
echo "  - $VERSION_TAG"
if [[ "$PUSH_LATEST" == "true" ]]; then
    echo "  - $LATEST_TAG"
fi