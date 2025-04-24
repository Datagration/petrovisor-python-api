#!/bin/bash
# generate_api_docs.sh - Generate API documentation for Docusaurus

# Configuration
PACKAGE_NAME="petrovisor"
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
ROOT_DIR=$(realpath "${SCRIPT_DIR}/..")
SOURCE_DIR="${ROOT_DIR}/petrovisor"
DOCS_DIR="${ROOT_DIR}/docs"
DOCS_API_DIR="${DOCS_DIR}/api"
WEBSITE_DIR="${ROOT_DIR}/website"
REQUIREMENTS_FILE="${SCRIPT_DIR}/requirements-docs.txt"
CONFIG_FILE="${SCRIPT_DIR}/config/docs_config.json"
FROM_INIT=1
SIDEBAR_POSITION=-1

echo "Root dir is: ${ROOT_DIR}"
echo "Script dir is: ${SCRIPT_DIR}"
echo "Source dir is: ${SOURCE_DIR}"
echo "Docs dir is: ${DOCS_API_DIR}"
echo "Website dir is: ${WEBSITE_DIR}"
echo "Requirements file is: ${REQUIREMENTS_FILE}"
echo "Config file is: ${CONFIG_FILE}"

# Function to calculate the last position based on existing folder count
calculate_last_position() {
    local docs_dir=$1
    local api_dir=$2
    local position=1
    
    # Count category folders in docs directory (folders with _category_.json)
    local folders=0
    for dir in "${docs_dir}"/*; do
        if [ -d "$dir" ] && [ -f "$dir/_category_.json" ] && [ "$(basename "$dir")" != "api" ]; then
            # Extract position from _category_.json
            local cat_pos=$(grep -o '"position":[^,}]*' "$dir/_category_.json" | cut -d':' -f2)
            if [ -n "$cat_pos" ] && [ "$cat_pos" -gt "$position" ]; then
                position=$cat_pos
            fi
            folders=$((folders+1))
        fi
    done
    
    # Add 1 to the highest position found
    position=$((position+1))
    
    # Print debug info to stderr instead of stdout
    echo "Found $folders category folders, setting API position to $position" >&2
    
    # Return only the position number
    echo $position
}

# Step 1: Make sure the config directory exists
mkdir -p "${DOCS_API_DIR}"

# Step 2: Clean up any existing API documentation to avoid stale files
echo "Cleaning up existing API documentation..."
rm -rf ${DOCS_API_DIR}/*

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed or not in PATH"
    exit 1
fi

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --package|-p)
            PACKAGE_NAME="$2"
            shift 2
            ;;
        --source-dir|-s)
            SOURCE_DIR="$2"
            shift 2
            ;;
        --docs-dir|-d)
            DOCS_API_DIR="$2"
            shift 2
            ;;
        --website-dir|-w)
            WEBSITE_DIR="$2"
            shift 2
            ;;
        --config|-c)
            CONFIG_FILE="$2"
            shift 2
            ;;
        --from-init|-i)
            FROM_INIT=1
            shift
            ;;
        --sidebar-position|-s)
            if [ "$2" = "last" ] || [ "$2" = "-1" ]; then
                # Calculate the last position
                SIDEBAR_POSITION=$(calculate_last_position "${DOCS_DIR}" "${DOCS_API_DIR}")
            else
                SIDEBAR_POSITION="$2"
            fi
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --package, -p NAME      Package name (default: petrovisor)"
            echo "  --source-dir, -s DIR    Source directory (default: ./petrovisor)"
            echo "  --docs-dir, -d DIR      Directory for documentation (default: ./docs/api)"
            echo "  --website-dir, -w DIR   Website directory (default: ./website)"
            echo "  --config, -c FILE       Path to documentation configuration JSON file"
            echo "  --from-init, -i         Import only modules defined in __init__.py"
            echo "  --sidebar-position, -s NUM  Sidebar position for API Reference category (default: 4)"
            echo "  --help, -h              Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# If SIDEBAR_POSITION is the default, check if "last" is preferred
if [ "$SIDEBAR_POSITION" = "-1" ] && [ -d "${DOCS_DIR}" ]; then
    # Count the number of top-level directories in DOCS_DIR
    DIR_COUNT=$(find "${DOCS_DIR}" -mindepth 1 -maxdepth 1 -type d -not -path "${DOCS_API_DIR}" | wc -l)
    # Place API at the end
    SIDEBAR_POSITION=$(calculate_last_position "${DOCS_DIR}" "${DOCS_API_DIR}")
    echo "Automatically placing API reference at the end (position: $SIDEBAR_POSITION)"
fi

# Step 3: Install dependencies
echo "Installing documentation dependencies..."
uv venv

# Use absolute path to ensure proper activation
source .venv/bin/activate

# Check if activation worked
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "Error: Virtual environment activation failed!"
    exit 1
else
    echo "Virtual environment activated: $VIRTUAL_ENV"
fi

source .venv/bin/activate
uv pip install -r "${REQUIREMENTS_FILE}"
uv pip install -e "${ROOT_DIR}"

if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies"
    exit 1
fi

# Step 4: Generate the API Markdown files
echo "Generating documentation for ${PACKAGE_NAME}..."
echo "Docs will be stored in: ${DOCS_API_DIR}"
echo "Using config file: ${CONFIG_FILE}"
echo "API Reference position: ${SIDEBAR_POSITION}"

# Build command with options - using an array for better formatting and argument handling
CMD=(
    "${SCRIPT_DIR}/generate_docs.py"
    "${SOURCE_DIR}"
    "${DOCS_API_DIR}"
    "--package" "${PACKAGE_NAME}"
    "--config" "${CONFIG_FILE}"
    "--sidebar-position" "${SIDEBAR_POSITION}"
)

# Add from-init option if specified
if [ ${FROM_INIT} -eq 1 ]; then
    CMD+=("--from-init")
    echo "Generating docs only for modules in __init__.py"
fi

# Execute the command
echo "Running: ${CMD[@]}"
uv run "${CMD[@]}"

# Check if the generation was successful
if [ $? -eq 0 ]; then
    echo "Documentation generated successfully!"
    echo ""
    echo "To preview the documentation, run: cd website && yarn start"
else
    echo "Error: Documentation generation failed"
    exit 1
fi
