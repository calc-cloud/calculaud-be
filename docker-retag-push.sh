#!/bin/bash

# Script to extract Docker image from tar.gz or zip file, retag with custom prefix, and push
# Usage: ./docker-retag-push.sh [tar.gz-file|zip-file] [new-prefix] [original-image-name]
# If no arguments provided, script will prompt for interactive input

# Note: removed 'set -e' to allow better error handling in interactive mode

# Default values
DEFAULT_REPO_PREFIX="defaultrepo"

# Function to display usage
usage() {
    echo "Usage: $0 [file] [new-prefix] [original-image-name]"
    echo ""
    echo "Arguments (all optional - will prompt if not provided):"
    echo "  file                Path to Docker image file (.tar.gz or .zip containing .tar.gz)"
    echo "  new-prefix          New registry/prefix for the image (default: $DEFAULT_REPO_PREFIX)"
    echo "  original-image-name Optional: Original image name if different from filename"
    echo ""
    echo "Examples:"
    echo "  $0                                              # Interactive mode"
    echo "  $0 calculaud-be-v1.0.0.tar.gz                  # Uses default prefix"
    echo "  $0 calculaud-be-v1.0.0.zip                     # Zip file containing tar.gz"
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
        read -e -p "$prompt [$default]: " result
        echo "${result:-$default}"
    else
        read -e -p "$prompt: " result
        echo "$result"
    fi
}

# Function to prompt for file path with tab completion
prompt_for_file() {
    local prompt="$1"
    local result
    
    read -e -p "$prompt: " result
    echo "$result"
}

# Function to get available archive files in current directory
list_archive_files() {
    local tar_files=(*.tar.gz)
    local zip_files=(*.zip)
    local found_files=false
    
    if [ -e "${tar_files[0]}" ]; then
        echo "Available tar.gz files:"
        for i in "${!tar_files[@]}"; do
            echo "  $((i+1)). ${tar_files[i]}"
        done
        found_files=true
    fi
    
    if [ -e "${zip_files[0]}" ]; then
        echo "Available zip files:"
        for i in "${!zip_files[@]}"; do
            echo "  $((i+1)). ${zip_files[i]}"
        done
        found_files=true
    fi
    
    if [ "$found_files" = true ]; then
        echo ""
    fi
}

# Interactive parameter collection
if [ $# -eq 0 ]; then
    echo "=== Docker Image Retag and Push Script ==="
    echo "Interactive mode - you'll be prompted for each parameter"
    echo ""
    
    # Show available archive files
    list_archive_files
    
    # Get archive file
    ARCHIVE_FILE=$(prompt_for_file "Enter path to archive file (.tar.gz or .zip)")
    while [ ! -f "$ARCHIVE_FILE" ]; do
        echo "Error: File '$ARCHIVE_FILE' not found"
        ARCHIVE_FILE=$(prompt_for_file "Enter path to archive file (.tar.gz or .zip)")
    done
    
    # Get new registry prefix (repository only, image name will be preserved from loaded image)
    NEW_PREFIX=$(prompt_with_default "Enter new registry/prefix" "$DEFAULT_REPO_PREFIX")
    
    # Get original image name (optional)
    ORIGINAL_IMAGE_NAME=$(prompt_with_default "Enter original image name (optional)" "")
    
elif [ $# -eq 1 ]; then
    ARCHIVE_FILE="$1"
    NEW_PREFIX="$DEFAULT_REPO_PREFIX"
    ORIGINAL_IMAGE_NAME=""
    
elif [ $# -eq 2 ]; then
    ARCHIVE_FILE="$1"
    NEW_PREFIX="$2"
    ORIGINAL_IMAGE_NAME=""
    
else
    ARCHIVE_FILE="$1"
    NEW_PREFIX="$2"
    ORIGINAL_IMAGE_NAME="$3"
fi

# Check if archive file exists
if [ ! -f "$ARCHIVE_FILE" ]; then
    echo "Error: File '$ARCHIVE_FILE' not found"
    exit 1
fi

# Determine file type and handle accordingly
if [[ "$ARCHIVE_FILE" == *.tar.gz ]]; then
    TAR_GZ_FILE="$ARCHIVE_FILE"
    FILE_TYPE="tar.gz"
elif [[ "$ARCHIVE_FILE" == *.zip ]]; then
    FILE_TYPE="zip"
    # Extract tar.gz from zip file
    echo "Detected zip file, extracting..."
    TEMP_DIR=$(mktemp -d)
    unzip -q "$ARCHIVE_FILE" -d "$TEMP_DIR"
    
    # Find the tar.gz file in the extracted contents
    TAR_GZ_FILE=$(find "$TEMP_DIR" -name "*.tar.gz" | head -1)
    if [ -z "$TAR_GZ_FILE" ]; then
        echo "Error: No .tar.gz file found in zip archive"
        rm -rf "$TEMP_DIR"
        exit 1
    fi
    echo "Found tar.gz file: $(basename "$TAR_GZ_FILE")"
else
    echo "Error: Unsupported file type. Only .tar.gz and .zip files are supported."
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
echo "Source file: $ARCHIVE_FILE"
echo "File type: $FILE_TYPE"
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
LOAD_OUTPUT=$(docker load < "$TAR_FILE" 2>&1)
if [ $? -ne 0 ]; then
    echo "Error: Failed to load Docker image"
    echo "$LOAD_OUTPUT"
    read -p "Press Enter to continue or Ctrl+C to exit..."
    exit 1
fi
echo "$LOAD_OUTPUT"

# Extract the loaded image name from docker load output
LOADED_IMAGE=$(echo "$LOAD_OUTPUT" | grep "Loaded image:" | sed 's/Loaded image: //')

if [ -z "$LOADED_IMAGE" ]; then
    echo "Error: Could not determine loaded image name from output:"
    echo "$LOAD_OUTPUT"
    read -p "Press Enter to continue or Ctrl+C to exit..."
    exit 1
fi

echo "✓ Loaded image: $LOADED_IMAGE"

# Step 3: Tag the image with new prefix
echo ""
echo "Step 3: Tagging image with new prefix..."

# Extract original image name and tag from loaded image
if [[ "$LOADED_IMAGE" =~ ^(.*/)?([^:/]+):(.+)$ ]]; then
    ORIGINAL_REPO="${BASH_REMATCH[1]}"
    IMAGE_NAME="${BASH_REMATCH[2]}"
    IMAGE_TAG="${BASH_REMATCH[3]}"
    echo "Detected image components: repo='${ORIGINAL_REPO}', name='${IMAGE_NAME}', tag='${IMAGE_TAG}'"
elif [[ "$LOADED_IMAGE" =~ ^([^:/]+):(.+)$ ]]; then
    IMAGE_NAME="${BASH_REMATCH[1]}"
    IMAGE_TAG="${BASH_REMATCH[2]}"
    echo "Detected image components: name='${IMAGE_NAME}', tag='${IMAGE_TAG}'"
else
    echo "Error: Could not parse loaded image name: $LOADED_IMAGE"
    read -p "Press Enter to continue or Ctrl+C to exit..."
    exit 1
fi

# Create new image name preserving original name and tag, only changing repository
NEW_IMAGE_NAME="$NEW_PREFIX/$IMAGE_NAME:$IMAGE_TAG"
NEW_IMAGE_LATEST="$NEW_PREFIX/$IMAGE_NAME:latest"

echo "Tagging as: $NEW_IMAGE_NAME"
if ! docker tag "$LOADED_IMAGE" "$NEW_IMAGE_NAME" 2>&1; then
    echo "Error: Failed to tag image as $NEW_IMAGE_NAME"
    read -p "Press Enter to continue or Ctrl+C to exit..."
    exit 1
fi

echo "Tagging as: $NEW_IMAGE_LATEST"
if ! docker tag "$LOADED_IMAGE" "$NEW_IMAGE_LATEST" 2>&1; then
    echo "Error: Failed to tag image as $NEW_IMAGE_LATEST"
    read -p "Press Enter to continue or Ctrl+C to exit..."
    exit 1
fi

echo "✓ Tagged successfully"

# Step 4: Push the images
echo ""
echo "Step 4: Pushing images to registry..."

echo "Pushing $NEW_IMAGE_NAME..."
if ! docker push "$NEW_IMAGE_NAME" 2>&1; then
    echo "Error: Failed to push $NEW_IMAGE_NAME"
    read -p "Press Enter to continue or Ctrl+C to exit..."
    exit 1
fi

echo "Pushing $NEW_IMAGE_LATEST..."
if ! docker push "$NEW_IMAGE_LATEST" 2>&1; then
    echo "Error: Failed to push $NEW_IMAGE_LATEST"
    read -p "Press Enter to continue or Ctrl+C to exit..."
    exit 1
fi

echo "✓ Push completed successfully"

# Step 5: Cleanup
echo ""
echo "Step 5: Cleaning up temporary files..."
rm -f "$TAR_FILE"
echo "✓ Removed $TAR_FILE"

# Cleanup temp directory if it was created for zip extraction
if [ -n "$TEMP_DIR" ] && [ -d "$TEMP_DIR" ]; then
    rm -rf "$TEMP_DIR"
    echo "✓ Removed temp directory $TEMP_DIR"
fi

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