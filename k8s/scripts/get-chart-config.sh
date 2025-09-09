#!/bin/bash
# Extract configuration values from Helm Chart.yaml
# Usage: ./get-chart-config.sh [repository|version|image]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHART_FILE="$SCRIPT_DIR/../helm/calculaud-be/Chart.yaml"
VALUES_FILE="$SCRIPT_DIR/../helm/calculaud-be/values.yaml"

if [[ ! -f "$CHART_FILE" ]]; then
    echo "Error: Chart.yaml not found at $CHART_FILE" >&2
    exit 1
fi

if [[ ! -f "$VALUES_FILE" ]]; then
    echo "Error: values.yaml not found at $VALUES_FILE" >&2
    exit 1
fi

# Function to extract YAML value
get_yaml_value() {
    local file="$1"
    local key="$2"
    
    # Simple YAML parser - handles basic key: value pairs
    grep "^${key}:" "$file" | head -1 | sed 's/^[^:]*:[[:space:]]*//' | sed 's/^["'\'']//' | sed 's/["'\'']$//'
}

case "${1:-}" in
    repository)
        get_yaml_value "$VALUES_FILE" "  repository"
        ;;
    version|appVersion)
        get_yaml_value "$CHART_FILE" "appVersion"
        ;;
    image)
        REPOSITORY=$(get_yaml_value "$VALUES_FILE" "  repository")
        VERSION=$(get_yaml_value "$CHART_FILE" "appVersion")
        echo "${REPOSITORY}:${VERSION}"
        ;;
    tag)
        # Check if custom tag is set in values, otherwise use appVersion
        TAG=$(get_yaml_value "$VALUES_FILE" "  tag")
        if [[ -z "$TAG" || "$TAG" == '""' ]]; then
            get_yaml_value "$CHART_FILE" "appVersion"
        else
            echo "$TAG"
        fi
        ;;
    chart-version)
        get_yaml_value "$CHART_FILE" "version"
        ;;
    *)
        echo "Usage: $0 [repository|version|image|tag|chart-version]"
        echo ""
        echo "Extract configuration from Chart.yaml and values.yaml:"
        echo "  repository    - Docker image repository"
        echo "  version       - Application version (appVersion)"
        echo "  image         - Full image name (repository:version)"
        echo "  tag           - Image tag (custom tag or appVersion)"
        echo "  chart-version - Helm chart version"
        exit 1
        ;;
esac