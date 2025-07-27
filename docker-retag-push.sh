#!/bin/bash

# Script to extract Docker image from tar.gz or zip file, retag with custom prefix, and push
# Usage: ./docker-retag-push.sh [tar.gz-file|zip-file] [new-prefix] [original-image-name]
# If no arguments provided, script will prompt for interactive input

# Note: removed 'set -e' to allow better error handling in interactive mode

# Default values
DEFAULT_REPO_PREFIX="defaultrepo"

# Default folders to search for docker images (can be customized)
DEFAULT_FOLDERS=(
    "."
    "./builds"
    "./docker-images"
    "./releases"
)

# Colors for fancy output (disabled for Git Bash compatibility)
RED=''
GREEN=''
YELLOW=''
BLUE=''
PURPLE=''
CYAN=''
WHITE=''
NC='' # No Color

# Simple progress indicator (Git Bash compatible)
show_spinner() {
    local message="$1"
    echo "$message..."
}

# Simple command execution with progress (Git Bash compatible)
show_spinner_with_command() {
    local message="$1"
    local command="$2"
    
    echo "$message..."
    
    # Execute command and capture output
    if eval "$command"; then
        echo "✓ Success"
        return 0
    else
        echo "✗ Failed"
        return 1
    fi
}

# Simple welcome screen (Git Bash compatible)
show_welcome() {
    clear
    echo "==========================================="
    echo "     Docker Image Retag & Deploy Tool"
    echo "          Made by Danorama Team"
    echo "==========================================="
    echo ""
    echo "Welcome to Dan Dep - Docker Image Manager!"
    echo ""
    sleep 1
}

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

# Function to find the most recent archive file across default folders
find_most_recent_archive() {
    local most_recent_file=""
    local most_recent_time=0
    
    for folder in "${DEFAULT_FOLDERS[@]}"; do
        # Expand tilde and variables
        local expanded_folder
        expanded_folder=$(eval echo "$folder")
        
        # Skip if folder doesn't exist
        [ ! -d "$expanded_folder" ] && continue
        
        # Find .tar.gz files (Windows Git Bash compatible)
        for file in "$expanded_folder"/*.tar.gz; do
            if [ -f "$file" ]; then
                most_recent_file="$file"
            fi
        done
        
        # Find .zip files (Windows Git Bash compatible)
        for file in "$expanded_folder"/*.zip; do
            if [ -f "$file" ]; then
                most_recent_file="$file"
            fi
        done
    done
    
    echo "$most_recent_file"
}

# Function to get available archive files across default folders
list_archive_files() {
    local found_files=false
    local file_count=0
    
    echo -e "${CYAN}🔍 Searching in default folders:${NC}"
    for folder in "${DEFAULT_FOLDERS[@]}"; do
        local expanded_folder
        expanded_folder=$(eval echo "$folder")
        
        # Skip if folder doesn't exist
        if [ ! -d "$expanded_folder" ]; then
            echo -e "   📁 ${YELLOW}$folder${NC} ${RED}(not found)${NC}"
            continue
        fi
        
        echo -e "   📁 ${YELLOW}$folder${NC}"
        
        # Check for .tar.gz files (Windows Git Bash compatible)
        local tar_files=()
        for file in "$expanded_folder"/*.tar.gz; do
            if [ -f "$file" ]; then
                tar_files+=("$file")
            fi
        done
        
        # Check for .zip files (Windows Git Bash compatible)
        local zip_files=()
        for file in "$expanded_folder"/*.zip; do
            if [ -f "$file" ]; then
                zip_files+=("$file")
            fi
        done
        
        if [ ${#tar_files[@]} -gt 0 ] || [ ${#zip_files[@]} -gt 0 ]; then
            found_files=true
            
            for file in "${tar_files[@]}"; do
                ((file_count++))
                echo -e "      $file_count. ${GREEN}$(basename "$file")${NC} ${CYAN}(.tar.gz)${NC}"
            done
            
            for file in "${zip_files[@]}"; do
                ((file_count++))
                echo -e "      $file_count. ${GREEN}$(basename "$file")${NC} ${CYAN}(.zip)${NC}"
            done
        fi
    done
    
    if [ "$found_files" = true ]; then
        echo ""
        
        # Show most recent file suggestion
        local most_recent
        most_recent=$(find_most_recent_archive)
        if [ -n "$most_recent" ]; then
            echo -e "${PURPLE}💡 Most recent file found:${NC}"
            local file_date
            file_date="$(date -r "$most_recent" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo 'Unknown')"
            echo -e "   🕐 ${GREEN}$(basename "$most_recent")${NC} ${YELLOW}($file_date)${NC}"
            echo -e "   📍 ${CYAN}$most_recent${NC}"
            echo ""
        fi
    else
        echo -e "${YELLOW}⚠️  No archive files found in default folders${NC}"
        echo ""
    fi
}

# Interactive parameter collection
if [ $# -eq 0 ]; then
    # Show welcome screen
    show_welcome
    
    echo -e "${BLUE}🎯 Interactive Mode Activated! Let's get your Docker image deployed! 🎯${NC}"
    echo ""
    
    # Show available archive files
    echo -e "${CYAN}📁 Scanning for available files...${NC}"
    show_spinner "Looking for archives" 1
    list_archive_files
    
    # Get archive file with most recent file as default
    echo -e "${YELLOW}🔍 Please select your Docker image archive:${NC}"
    
    # Get the most recent file as suggested default
    SUGGESTED_FILE=$(find_most_recent_archive)
    if [ -n "$SUGGESTED_FILE" ]; then
        echo -e "${PURPLE}💡 Press Enter to use the most recent file, or specify a different path:${NC}"
        ARCHIVE_FILE=$(prompt_with_default "📦 Archive file" "$SUGGESTED_FILE")
    else
        ARCHIVE_FILE=$(prompt_for_file "📦 Enter path to archive file (.tar.gz or .zip)")
    fi
    
    while [ ! -f "$ARCHIVE_FILE" ]; do
        echo -e "${RED}❌ Error: File '$ARCHIVE_FILE' not found${NC}"
        if [ -n "$SUGGESTED_FILE" ]; then
            ARCHIVE_FILE=$(prompt_with_default "📦 Archive file" "$SUGGESTED_FILE")
        else
            ARCHIVE_FILE=$(prompt_for_file "📦 Enter path to archive file (.tar.gz or .zip)")
        fi
    done
    echo -e "${GREEN}✅ Archive file selected: $ARCHIVE_FILE${NC}"
    echo ""
    
    # Get new registry prefix (repository only, image name will be preserved from loaded image)
    echo -e "${YELLOW}🏷️  Repository Configuration:${NC}"
    NEW_PREFIX=$(prompt_with_default "🎯 Enter new registry/prefix" "$DEFAULT_REPO_PREFIX")
    echo -e "${GREEN}✅ Repository prefix set: $NEW_PREFIX${NC}"
    echo ""
    
    # Get original image name (optional)
    echo -e "${YELLOW}⚙️  Advanced Options (optional):${NC}"
    ORIGINAL_IMAGE_NAME=$(prompt_with_default "🔧 Enter original image name (leave empty for auto-detect)" "")
    if [ -n "$ORIGINAL_IMAGE_NAME" ]; then
        echo -e "${GREEN}✅ Original image name: $ORIGINAL_IMAGE_NAME${NC}"
    else
        echo -e "${CYAN}🤖 Will auto-detect image name from loaded image${NC}"
    fi
    echo ""
    
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

echo ""
echo "=== DAN DEP DEPLOYMENT STARTED ==="
echo ""
echo "Deployment Summary:"
echo "   Source file: $ARCHIVE_FILE"
echo "   File type: $FILE_TYPE" 
echo "   Original image: $ORIGINAL_IMAGE_NAME"
echo "   Version: $VERSION"
echo "   New prefix: $NEW_PREFIX"
echo ""

# Step 1: Extract the tar.gz file
echo "Step 1: Extracting Docker Image Archive"
show_spinner "Extracting $TAR_GZ_FILE"
TAR_FILE="${TAR_GZ_FILE%.gz}"
gunzip -c "$TAR_GZ_FILE" > "$TAR_FILE"

if [ ! -f "$TAR_FILE" ]; then
    echo "Error: Failed to extract $TAR_FILE"
    exit 1
fi

echo "Successfully extracted to $TAR_FILE"
echo ""

# Step 2: Load the Docker image
echo "Step 2: Loading Docker Image"
show_spinner "Loading Docker image from archive"

# Verify Docker is running first
if ! docker info >/dev/null 2>&1; then
    echo "✗ Error: Docker is not running or not accessible"
    echo "Please start Docker Desktop and try again."
    read -p "Press Enter to continue or Ctrl+C to exit..."
    exit 1
fi

# Verify the tar file is readable
if [ ! -r "$TAR_FILE" ]; then
    echo "✗ Error: Cannot read tar file: $TAR_FILE"
    echo "File permissions or path issue."
    exit 1
fi

echo "Docker status: ✓ Running"
echo "Tar file: ✓ Accessible ($(du -h "$TAR_FILE" | cut -f1))"

# Execute docker load with verbose output
echo "Executing: docker load < \"$TAR_FILE\""
echo "This may take a few moments..."

# Use a more reliable approach for Windows Git Bash
LOAD_OUTPUT=""
if command -v winpty >/dev/null 2>&1; then
    # Windows Git Bash with winpty
    LOAD_OUTPUT=$(winpty docker load < "$TAR_FILE" 2>&1)
    LOAD_EXIT_CODE=$?
else
    # Standard execution
    LOAD_OUTPUT=$(docker load < "$TAR_FILE" 2>&1)
    LOAD_EXIT_CODE=$?
fi

if [ $LOAD_EXIT_CODE -eq 0 ]; then
    echo "✓ Docker load command succeeded"
else
    echo "✗ Docker load command failed (exit code: $LOAD_EXIT_CODE)"
    echo "Error output:"
    echo "$LOAD_OUTPUT"
    echo ""
    echo "Troubleshooting tips:"
    echo "1. Verify the tar.gz file is a valid Docker image export"
    echo "2. Check if Docker has enough disk space"
    echo "3. Try running: docker load < \"$TAR_FILE\" manually"
    echo ""
    read -p "Press Enter to continue or Ctrl+C to exit..."
    exit 1
fi

echo "Docker load output:"
echo "$LOAD_OUTPUT"
echo ""

# Extract the loaded image name from docker load output - try multiple patterns
LOADED_IMAGE=""

# Try different patterns for image extraction
if echo "$LOAD_OUTPUT" | grep -q "Loaded image:"; then
    LOADED_IMAGE=$(echo "$LOAD_OUTPUT" | grep "Loaded image:" | sed 's/.*Loaded image: *//' | tail -1)
elif echo "$LOAD_OUTPUT" | grep -q "sha256:"; then
    # Fallback: try to find image ID and get the tag
    IMAGE_ID=$(echo "$LOAD_OUTPUT" | grep "sha256:" | head -1 | awk '{print $1}')
    if [ -n "$IMAGE_ID" ]; then
        echo "Found image ID: $IMAGE_ID"
        echo "Attempting to find image tag..."
        LOADED_IMAGE=$(docker images --format "{{.Repository}}:{{.Tag}}" | head -1)
    fi
elif docker images --format "{{.Repository}}:{{.Tag}}" | grep -v "<none>" | head -1 >/dev/null 2>&1; then
    # Fallback: get the most recent image that's not <none>
    echo "Fallback: Looking for most recent loaded image..."
    LOADED_IMAGE=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep -v "<none>" | head -1)
fi

if [ -z "$LOADED_IMAGE" ]; then
    echo "Error: Could not determine loaded image name from output:"
    echo "Raw output:"
    echo "'$LOAD_OUTPUT'"
    echo ""
    echo "Available images:"
    docker images
    echo ""
    echo "Please check if the Docker archive file is valid."
    read -p "Press Enter to continue or Ctrl+C to exit..."
    exit 1
fi

echo "Successfully loaded image: $LOADED_IMAGE"
echo ""

# Step 3: Tag the image with new prefix
echo "Step 3: Retagging Docker Image"
show_spinner "Analyzing image structure"

# Extract original image name and tag from loaded image
if [[ "$LOADED_IMAGE" =~ ^(.*/)?([^:/]+):(.+)$ ]]; then
    ORIGINAL_REPO="${BASH_REMATCH[1]}"
    IMAGE_NAME="${BASH_REMATCH[2]}"
    IMAGE_TAG="${BASH_REMATCH[3]}"
    echo "Detected image components:"
    echo "   Repository: ${ORIGINAL_REPO:-"(none)"}"
    echo "   Name: ${IMAGE_NAME}"
    echo "   Tag: ${IMAGE_TAG}"
elif [[ "$LOADED_IMAGE" =~ ^([^:/]+):(.+)$ ]]; then
    IMAGE_NAME="${BASH_REMATCH[1]}"
    IMAGE_TAG="${BASH_REMATCH[2]}"
    echo "Detected image components:"
    echo "   Name: ${IMAGE_NAME}"
    echo "   Tag: ${IMAGE_TAG}"
else
    echo "Error: Could not parse loaded image name: $LOADED_IMAGE"
    read -p "Press Enter to continue or Ctrl+C to exit..."
    exit 1
fi
echo ""

# Create new image name preserving original name and tag, only changing repository
NEW_IMAGE_NAME="$NEW_PREFIX/$IMAGE_NAME:$IMAGE_TAG"
NEW_IMAGE_LATEST="$NEW_PREFIX/$IMAGE_NAME:latest"

echo "Creating new tags:"
echo "   $NEW_IMAGE_NAME"
echo "   $NEW_IMAGE_LATEST"
echo ""

show_spinner "Tagging as $NEW_IMAGE_NAME"
if ! docker tag "$LOADED_IMAGE" "$NEW_IMAGE_NAME" 2>&1; then
    echo "Error: Failed to tag image as $NEW_IMAGE_NAME"
    read -p "Press Enter to continue or Ctrl+C to exit..."
    exit 1
fi

show_spinner "Tagging as $NEW_IMAGE_LATEST"
if ! docker tag "$LOADED_IMAGE" "$NEW_IMAGE_LATEST" 2>&1; then
    echo "Error: Failed to tag image as $NEW_IMAGE_LATEST"
    read -p "Press Enter to continue or Ctrl+C to exit..."
    exit 1
fi

echo "Successfully tagged images"
echo ""

# Step 4: Push the images
echo "Step 4: Deploying to Registry"
echo "Pushing images to registry..."
echo ""

if ! show_spinner_with_command "Pushing $NEW_IMAGE_NAME" "docker push '$NEW_IMAGE_NAME' >/dev/null 2>&1"; then
    echo "Error: Failed to push $NEW_IMAGE_NAME"
    read -p "Press Enter to continue or Ctrl+C to exit..."
    exit 1
fi
echo "Successfully pushed $NEW_IMAGE_NAME"
echo ""

if ! show_spinner_with_command "Pushing $NEW_IMAGE_LATEST" "docker push '$NEW_IMAGE_LATEST' >/dev/null 2>&1"; then
    echo "Error: Failed to push $NEW_IMAGE_LATEST"
    read -p "Press Enter to continue or Ctrl+C to exit..."
    exit 1
fi
echo "Successfully pushed $NEW_IMAGE_LATEST"
echo ""

echo "All images deployed successfully!"
echo ""

# Step 5: Cleanup
echo "Step 5: Cleaning Up"
show_spinner "Removing temporary files"
rm -f "$TAR_FILE"
echo "Removed temporary tar file"

# Cleanup temp directory if it was created for zip extraction
if [ -n "$TEMP_DIR" ] && [ -d "$TEMP_DIR" ]; then
    rm -rf "$TEMP_DIR"
    echo "Removed temporary directory"
fi
echo ""

# Optional: Remove loaded image to save space
echo "Storage Management:"
read -p "Remove loaded image '$LOADED_IMAGE' to save space? (y/N): " -n 1 -r
echo
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    show_spinner "Cleaning up loaded image"
    docker rmi "$LOADED_IMAGE" 2>/dev/null || echo "Warning: Image already removed or in use"
    echo "Cleanup completed"
else
    echo "Keeping loaded image for future use"
fi
echo ""

# Success celebration
echo "=== DAN DEP SUCCESS! ==="
echo ""
echo "Deployment completed successfully!"
echo ""
echo "Images deployed:"
echo "   $NEW_IMAGE_NAME"
echo "   $NEW_IMAGE_LATEST"
echo ""
echo "Ready to use! Pull your images with:"
echo "   docker pull $NEW_IMAGE_NAME"
echo "   docker pull $NEW_IMAGE_LATEST"
echo ""
echo "Thank you for using Dan Dep by Danorama Team!"
echo "Happy Deploying!"