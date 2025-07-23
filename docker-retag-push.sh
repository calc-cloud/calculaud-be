#!/bin/bash

# Script to extract Docker image from tar.gz or zip file, retag with custom prefix, and push
# Usage: ./docker-retag-push.sh [tar.gz-file|zip-file] [new-prefix] [original-image-name]
# If no arguments provided, script will prompt for interactive input

# Note: removed 'set -e' to allow better error handling in interactive mode

# Default values
DEFAULT_REPO_PREFIX="defaultrepo"

# Colors for fancy output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Loading spinner function
show_spinner() {
    local message="$1"
    local duration="$2"
    local spinner_chars="⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    local delay=0.1
    local iterations=$((duration * 10))
    
    echo -n "${CYAN}${message}${NC} "
    for ((i=0; i<iterations; i++)); do
        printf "${YELLOW}%c${NC}" "${spinner_chars:$((i % ${#spinner_chars})):1}"
        sleep $delay
        printf "\b"
    done
    echo -e "${GREEN}✓${NC}"
}

# Real spinner that waits for command completion
show_spinner_with_command() {
    local message="$1"
    local command="$2"
    local spinner_chars="⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    local delay=0.1
    local spin=0
    
    echo -n "${CYAN}${message}${NC} "
    
    # Start the command in background and capture its PID
    eval "$command" &
    local cmd_pid=$!
    
    # Show spinner while command is running
    while kill -0 $cmd_pid 2>/dev/null; do
        printf "${YELLOW}%c${NC}" "${spinner_chars:$((spin % ${#spinner_chars})):1}"
        sleep $delay
        printf "\b"
        ((spin++))
    done
    
    # Wait for command to complete and get exit status
    wait $cmd_pid
    local exit_status=$?
    
    if [ $exit_status -eq 0 ]; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗${NC}"
        return $exit_status
    fi
}

# Cool welcome screen
show_welcome() {
    clear
    echo -e "${PURPLE}"
    echo "██████╗  █████╗ ███╗   ██╗    ██████╗ ███████╗██████╗ "
    echo "██╔══██╗██╔══██╗████╗  ██║    ██╔══██╗██╔════╝██╔══██╗"
    echo "██║  ██║███████║██╔██╗ ██║    ██║  ██║█████╗  ██████╔╝"
    echo "██║  ██║██╔══██║██║╚██╗██║    ██║  ██║██╔══╝  ██╔═══╝ "
    echo "██████╔╝██║  ██║██║ ╚████║    ██████╔╝███████╗██║     "
    echo "╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝    ╚═════╝ ╚══════╝╚═╝     "
    echo -e "${NC}"
    echo ""
    echo -e "${YELLOW}🚀 Docker Image Retag & Deploy Tool 🚀${NC}"
    echo -e "${CYAN}Made with ❤️  by Danorama Team${NC}"
    echo ""
    echo -e "${YELLOW}🌟 Welcome to Dan Dep - The Ultimate Docker Image Manager! 🌟${NC}"
    echo ""
    sleep 2
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
    # Show welcome screen
    show_welcome
    
    echo -e "${BLUE}🎯 Interactive Mode Activated! Let's get your Docker image deployed! 🎯${NC}"
    echo ""
    
    # Show available archive files
    echo -e "${CYAN}📁 Scanning for available files...${NC}"
    show_spinner "Looking for archives" 1
    list_archive_files
    
    # Get archive file
    echo -e "${YELLOW}🔍 Please select your Docker image archive:${NC}"
    ARCHIVE_FILE=$(prompt_for_file "📦 Enter path to archive file (.tar.gz or .zip)")
    while [ ! -f "$ARCHIVE_FILE" ]; do
        echo -e "${RED}❌ Error: File '$ARCHIVE_FILE' not found${NC}"
        ARCHIVE_FILE=$(prompt_for_file "📦 Enter path to archive file (.tar.gz or .zip)")
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
echo -e "${PURPLE}🚀 DAN DEP DEPLOYMENT STARTED 🚀${NC}"
echo ""
echo -e "${CYAN}📋 Deployment Summary:${NC}"
echo -e "   📁 Source file: ${YELLOW}$ARCHIVE_FILE${NC}"
echo -e "   📦 File type: ${YELLOW}$FILE_TYPE${NC}" 
echo -e "   🏷️  Original image: ${YELLOW}$ORIGINAL_IMAGE_NAME${NC}"
echo -e "   🔖 Version: ${YELLOW}$VERSION${NC}"
echo -e "   🎯 New prefix: ${YELLOW}$NEW_PREFIX${NC}"
echo ""

# Step 1: Extract the tar.gz file
echo -e "${BLUE}📦 Step 1: Extracting Docker Image Archive${NC}"
show_spinner "🔓 Extracting $TAR_GZ_FILE" 2
TAR_FILE="${TAR_GZ_FILE%.gz}"
gunzip -c "$TAR_GZ_FILE" > "$TAR_FILE"

if [ ! -f "$TAR_FILE" ]; then
    echo -e "${RED}❌ Error: Failed to extract $TAR_FILE${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Successfully extracted to $TAR_FILE${NC}"
echo ""

# Step 2: Load the Docker image
echo -e "${BLUE}🐳 Step 2: Loading Docker Image${NC}"
if ! show_spinner_with_command "📥 Loading Docker image from archive" "docker load < '$TAR_FILE' --quiet 2>/tmp/docker_load_output.txt"; then
    echo -e "${RED}❌ Error: Failed to load Docker image${NC}"
    LOAD_OUTPUT=$(cat /tmp/docker_load_output.txt 2>/dev/null || echo "No output captured")
    echo "$LOAD_OUTPUT"
    read -p "Press Enter to continue or Ctrl+C to exit..."
    rm -f /tmp/docker_load_output.txt
    exit 1
fi
LOAD_OUTPUT=$(cat /tmp/docker_load_output.txt)
rm -f /tmp/docker_load_output.txt
echo -e "${CYAN}📤 Docker load output:${NC}"
echo "$LOAD_OUTPUT"
echo ""

# Extract the loaded image name from docker load output
LOADED_IMAGE=$(echo "$LOAD_OUTPUT" | grep "Loaded image:" | sed 's/Loaded image: //')

if [ -z "$LOADED_IMAGE" ]; then
    echo -e "${RED}❌ Error: Could not determine loaded image name from output:${NC}"
    echo "$LOAD_OUTPUT"
    read -p "Press Enter to continue or Ctrl+C to exit..."
    exit 1
fi

echo -e "${GREEN}✅ Successfully loaded image: ${YELLOW}$LOADED_IMAGE${NC}"
echo ""

# Step 3: Tag the image with new prefix
echo -e "${BLUE}🏷️  Step 3: Retagging Docker Image${NC}"
show_spinner "🔍 Analyzing image structure" 1

# Extract original image name and tag from loaded image
if [[ "$LOADED_IMAGE" =~ ^(.*/)?([^:/]+):(.+)$ ]]; then
    ORIGINAL_REPO="${BASH_REMATCH[1]}"
    IMAGE_NAME="${BASH_REMATCH[2]}"
    IMAGE_TAG="${BASH_REMATCH[3]}"
    echo -e "${CYAN}🔎 Detected image components:${NC}"
    echo -e "   📂 Repository: ${YELLOW}${ORIGINAL_REPO:-"(none)"}${NC}"
    echo -e "   📦 Name: ${YELLOW}${IMAGE_NAME}${NC}"
    echo -e "   🔖 Tag: ${YELLOW}${IMAGE_TAG}${NC}"
elif [[ "$LOADED_IMAGE" =~ ^([^:/]+):(.+)$ ]]; then
    IMAGE_NAME="${BASH_REMATCH[1]}"
    IMAGE_TAG="${BASH_REMATCH[2]}"
    echo -e "${CYAN}🔎 Detected image components:${NC}"
    echo -e "   📦 Name: ${YELLOW}${IMAGE_NAME}${NC}"
    echo -e "   🔖 Tag: ${YELLOW}${IMAGE_TAG}${NC}"
else
    echo -e "${RED}❌ Error: Could not parse loaded image name: $LOADED_IMAGE${NC}"
    read -p "Press Enter to continue or Ctrl+C to exit..."
    exit 1
fi
echo ""

# Create new image name preserving original name and tag, only changing repository
NEW_IMAGE_NAME="$NEW_PREFIX/$IMAGE_NAME:$IMAGE_TAG"
NEW_IMAGE_LATEST="$NEW_PREFIX/$IMAGE_NAME:latest"

echo -e "${CYAN}🎯 Creating new tags:${NC}"
echo -e "   📋 ${YELLOW}$NEW_IMAGE_NAME${NC}"
echo -e "   📋 ${YELLOW}$NEW_IMAGE_LATEST${NC}"
echo ""

show_spinner "🏷️  Tagging as $NEW_IMAGE_NAME" 1
if ! docker tag "$LOADED_IMAGE" "$NEW_IMAGE_NAME" 2>&1; then
    echo -e "${RED}❌ Error: Failed to tag image as $NEW_IMAGE_NAME${NC}"
    read -p "Press Enter to continue or Ctrl+C to exit..."
    exit 1
fi

show_spinner "🏷️  Tagging as $NEW_IMAGE_LATEST" 1
if ! docker tag "$LOADED_IMAGE" "$NEW_IMAGE_LATEST" 2>&1; then
    echo -e "${RED}❌ Error: Failed to tag image as $NEW_IMAGE_LATEST${NC}"
    read -p "Press Enter to continue or Ctrl+C to exit..."
    exit 1
fi

echo -e "${GREEN}✅ Successfully tagged images${NC}"
echo ""

# Step 4: Push the images
echo -e "${BLUE}🚀 Step 4: Deploying to Registry${NC}"
echo -e "${CYAN}📤 Pushing images to registry...${NC}"
echo ""

if ! show_spinner_with_command "📡 Pushing $NEW_IMAGE_NAME" "docker push '$NEW_IMAGE_NAME' --progress=false >/dev/null 2>&1"; then
    echo -e "${RED}❌ Error: Failed to push $NEW_IMAGE_NAME${NC}"
    read -p "Press Enter to continue or Ctrl+C to exit..."
    exit 1
fi
echo -e "${GREEN}✅ Successfully pushed $NEW_IMAGE_NAME${NC}"
echo ""

if ! show_spinner_with_command "📡 Pushing $NEW_IMAGE_LATEST" "docker push '$NEW_IMAGE_LATEST' --progress=false >/dev/null 2>&1"; then
    echo -e "${RED}❌ Error: Failed to push $NEW_IMAGE_LATEST${NC}"
    read -p "Press Enter to continue or Ctrl+C to exit..."
    exit 1
fi
echo -e "${GREEN}✅ Successfully pushed $NEW_IMAGE_LATEST${NC}"
echo ""

echo -e "${GREEN}🎉 All images deployed successfully!${NC}"
echo ""

# Step 5: Cleanup
echo -e "${BLUE}🧹 Step 5: Cleaning Up${NC}"
show_spinner "🗑️  Removing temporary files" 1
rm -f "$TAR_FILE"
echo -e "${GREEN}✅ Removed temporary tar file${NC}"

# Cleanup temp directory if it was created for zip extraction
if [ -n "$TEMP_DIR" ] && [ -d "$TEMP_DIR" ]; then
    rm -rf "$TEMP_DIR"
    echo -e "${GREEN}✅ Removed temporary directory${NC}"
fi
echo ""

# Optional: Remove loaded image to save space
echo -e "${YELLOW}💾 Storage Management:${NC}"
read -p "🗑️  Remove loaded image '$LOADED_IMAGE' to save space? (y/N): " -n 1 -r
echo
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    show_spinner "🗑️  Cleaning up loaded image" 1
    docker rmi "$LOADED_IMAGE" 2>/dev/null || echo -e "${YELLOW}⚠️  Image already removed or in use${NC}"
    echo -e "${GREEN}✅ Cleanup completed${NC}"
else
    echo -e "${CYAN}ℹ️  Keeping loaded image for future use${NC}"
fi
echo ""

# Success celebration
echo -e "${PURPLE}🎉 DAN DEP SUCCESS! 🎉${NC}"
echo ""
echo -e "${GREEN}🚀 Deployment completed successfully!${NC}"
echo ""
echo -e "${CYAN}📦 Images deployed:${NC}"
echo -e "   🎯 ${YELLOW}$NEW_IMAGE_NAME${NC}"
echo -e "   🏷️  ${YELLOW}$NEW_IMAGE_LATEST${NC}"
echo ""
echo -e "${CYAN}🔧 Ready to use! Pull your images with:${NC}"
echo -e "   ${WHITE}docker pull $NEW_IMAGE_NAME${NC}"
echo -e "   ${WHITE}docker pull $NEW_IMAGE_LATEST${NC}"
echo ""
echo -e "${YELLOW}✨ Thank you for using Dan Dep by Danorama Team! ✨${NC}"
echo -e "${PURPLE}🌟 Happy Deploying! 🌟${NC}"