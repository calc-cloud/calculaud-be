#!/bin/bash

# Script to extract Docker image from tar.gz, retag with custom prefix, and push
# Usage: ./docker-retag-push.sh <tar.gz-file> <new-prefix> [original-image-name]

set -e

# Function to display usage
usage() {
    echo "Usage: $0 <tar.gz-file> <new-prefix> [original-image-name]"
    echo ""
    echo "Arguments:"
    echo "  tar.gz-file         Path to the Docker image tar.gz file"
    echo "  new-prefix          New registry/prefix for the image (e.g., myregistry/myproject)"
    echo "  original-image-name Optional: Original image name if different from tar.gz filename"
    echo ""
    echo "Examples:"
    echo "  $0 calculaud-be-v1.0.0.tar.gz myregistry/calculaud-be"
    echo "  $0 app-v2.1.0.tar.gz localhost:5000/myapp original-app-name"
    echo ""
    exit 1
}

# Check if required arguments are provided
if [ $# -lt 2 ]; then
    echo "Error: Missing required arguments"
    usage
fi

TAR_GZ_FILE="$1"
NEW_PREFIX="$2"
ORIGINAL_IMAGE_NAME="$3"

# Check if tar.gz file exists
if [ ! -f "$TAR_GZ_FILE" ]; then
    echo "Error: File '$TAR_GZ_FILE' not found"
    exit 1
fi

# Extract version from filename if original image name not provided
if [ -z "$ORIGINAL_IMAGE_NAME" ]; then
    # Extract base name and version from tar.gz filename
    # e.g., calculaud-be-v1.0.0.tar.gz -> calculaud-be, v1.0.0
    BASENAME=$(basename "$TAR_GZ_FILE" .tar.gz)
    if [[ $BASENAME =~ ^(.+)-(v[0-9]+\.[0-9]+\.[0-9]+.*)$ ]]; then
        ORIGINAL_IMAGE_NAME="${BASH_REMATCH[1]}"
        VERSION="${BASH_REMATCH[2]}"
    else
        echo "Error: Cannot extract version from filename '$BASENAME'"
        echo "Please provide the original image name as the third argument"
        exit 1
    fi
else
    # Extract version from filename
    BASENAME=$(basename "$TAR_GZ_FILE" .tar.gz)
    if [[ $BASENAME =~ (v[0-9]+\.[0-9]+\.[0-9]+.*)$ ]]; then
        VERSION="${BASH_REMATCH[1]}"
    else
        echo "Error: Cannot extract version from filename '$BASENAME'"
        exit 1
    fi
fi

echo "=== Docker Image Retag and Push Script ==="
echo "Source file: $TAR_GZ_FILE"
echo "Original image: $ORIGINAL_IMAGE_NAME"
echo "Version: $VERSION"
echo "New prefix: $NEW_PREFIX"
echo ""

# Step 1: Extract the tar.gz file
echo "Step 1: Extracting $TAR_GZ_FILE..."
TAR_FILE="${TAR_GZ_FILE%.gz}"
gunzip -c "$TAR_GZ_FILE" > "$TAR_FILE"

if [ ! -f "$TAR_FILE" ]; then
    echo "Error: Failed to extract $TAR_FILE"
    exit 1
fi

echo "✓ Extracted to $TAR_FILE"

# Step 2: Load the Docker image
echo ""
echo "Step 2: Loading Docker image from $TAR_FILE..."
LOAD_OUTPUT=$(docker load < "$TAR_FILE")
echo "$LOAD_OUTPUT"

# Extract the loaded image name from docker load output
LOADED_IMAGE=$(echo "$LOAD_OUTPUT" | grep "Loaded image:" | sed 's/Loaded image: //')

if [ -z "$LOADED_IMAGE" ]; then
    echo "Error: Could not determine loaded image name"
    exit 1
fi

echo "✓ Loaded image: $LOADED_IMAGE"

# Step 3: Tag the image with new prefix
echo ""
echo "Step 3: Tagging image with new prefix..."

# Create new image name with custom prefix
NEW_IMAGE_NAME="$NEW_PREFIX:$VERSION"
NEW_IMAGE_LATEST="$NEW_PREFIX:latest"

echo "Tagging as: $NEW_IMAGE_NAME"
docker tag "$LOADED_IMAGE" "$NEW_IMAGE_NAME"

echo "Tagging as: $NEW_IMAGE_LATEST"
docker tag "$LOADED_IMAGE" "$NEW_IMAGE_LATEST"

echo "✓ Tagged successfully"

# Step 4: Push the images
echo ""
echo "Step 4: Pushing images to registry..."

echo "Pushing $NEW_IMAGE_NAME..."
docker push "$NEW_IMAGE_NAME"

echo "Pushing $NEW_IMAGE_LATEST..."
docker push "$NEW_IMAGE_LATEST"

echo "✓ Push completed successfully"

# Step 5: Cleanup
echo ""
echo "Step 5: Cleaning up temporary files..."
rm -f "$TAR_FILE"
echo "✓ Removed $TAR_FILE"

# Optional: Remove loaded image to save space
read -p "Remove loaded image '$LOADED_IMAGE' to save space? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker rmi "$LOADED_IMAGE" 2>/dev/null || echo "Image already removed or in use"
    echo "✓ Cleaned up loaded image"
fi

echo ""
echo "=== Script completed successfully! ==="
echo "Images pushed:"
echo "  - $NEW_IMAGE_NAME"
echo "  - $NEW_IMAGE_LATEST"
echo ""
echo "You can now use these images with:"
echo "  docker pull $NEW_IMAGE_NAME"
echo "  docker pull $NEW_IMAGE_LATEST"