#!/bin/bash

# Script to extract Docker image from tar.gz, retag with custom prefix, and push
# Usage: ./docker-retag-push.sh [tar.gz-file] [new-prefix] [original-image-name]
# If no arguments provided, script will prompt for interactive input

set -e

# Default values
DEFAULT_REPO_PREFIX="defaultrepo"

# Function to display usage
usage() {
    echo "Usage: $0 [tar.gz-file] [new-prefix] [original-image-name]"
    echo ""
    echo "Arguments (all optional - will prompt if not provided):"
    echo "  tar.gz-file         Path to the Docker image tar.gz file"
    echo "  new-prefix          New registry/prefix for the image (default: $DEFAULT_REPO_PREFIX)"
    echo "  original-image-name Optional: Original image name if different from tar.gz filename"
    echo ""
    echo "Examples:"
    echo "  $0                                              # Interactive mode"
    echo "  $0 calculaud-be-v1.0.0.tar.gz                  # Uses default prefix 'eyalg'"
    echo "  $0 calculaud-be-v1.0.0.tar.gz myregistry       # Custom prefix"
    echo "  $0 app-v2.1.0.tar.gz localhost:5000/myapp original-app-name"
    echo ""
    exit 1
}

# Function to prompt for input with default value
prompt_with_default() {
    local prompt="$1"
    local default="$2"
    local result
    
    if [ -n "$default" ]; then
        read -p "$prompt [$default]: " result
        echo "${result:-$default}"
    else
        read -p "$prompt: " result
        echo "$result"
    fi
}

# Function to get available tar.gz files in current directory
list_tar_gz_files() {
    local files=(*.tar.gz)
    if [ -e "${files[0]}" ]; then
        echo "Available tar.gz files:"
        for i in "${!files[@]}"; do
            echo "  $((i+1)). ${files[i]}"
        done
        echo ""
    fi
}

# Interactive parameter collection
if [ $# -eq 0 ]; then
    echo "=== Docker Image Retag and Push Script ==="
    echo "Interactive mode - you'll be prompted for each parameter"
    echo ""
    
    # Show available tar.gz files
    list_tar_gz_files
    
    # Get tar.gz file
    TAR_GZ_FILE=$(prompt_with_default "Enter path to tar.gz file" "")
    while [ ! -f "$TAR_GZ_FILE" ]; do
        echo "Error: File '$TAR_GZ_FILE' not found"
        TAR_GZ_FILE=$(prompt_with_default "Enter path to tar.gz file" "")
    done
    
    # Extract image name from filename for default prefix suggestion
    BASENAME=$(basename "$TAR_GZ_FILE" .tar.gz)
    if [[ $BASENAME =~ ^(.+)-(v[0-9]+\.[0-9]+\.[0-9]+.*)$ ]]; then
        IMAGE_NAME="${BASH_REMATCH[1]}"
        DEFAULT_FULL_PREFIX="$DEFAULT_REPO_PREFIX/$IMAGE_NAME"
    else
        DEFAULT_FULL_PREFIX="$DEFAULT_REPO_PREFIX"
    fi
    
    # Get new prefix
    NEW_PREFIX=$(prompt_with_default "Enter new registry/prefix" "$DEFAULT_FULL_PREFIX")
    
    # Get original image name (optional)
    ORIGINAL_IMAGE_NAME=$(prompt_with_default "Enter original image name (optional)" "")
    
elif [ $# -eq 1 ]; then
    TAR_GZ_FILE="$1"
    
    # Extract image name for default prefix
    BASENAME=$(basename "$TAR_GZ_FILE" .tar.gz)
    if [[ $BASENAME =~ ^(.+)-(v[0-9]+\.[0-9]+\.[0-9]+.*)$ ]]; then
        IMAGE_NAME="${BASH_REMATCH[1]}"
        NEW_PREFIX="$DEFAULT_REPO_PREFIX/$IMAGE_NAME"
    else
        NEW_PREFIX="$DEFAULT_REPO_PREFIX"
    fi
    
    ORIGINAL_IMAGE_NAME=""
    
elif [ $# -eq 2 ]; then
    TAR_GZ_FILE="$1"
    NEW_PREFIX="$2"
    ORIGINAL_IMAGE_NAME=""
    
else
    TAR_GZ_FILE="$1"
    NEW_PREFIX="$2"
    ORIGINAL_IMAGE_NAME="$3"
fi

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