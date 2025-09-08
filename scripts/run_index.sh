#!/bin/bash
# Index a folder using the search agent CLI

set -e

# Default values
FOLDER=""
FULL_REINDEX=false
PRIORITY="normal"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--folder)
            FOLDER="$2"
            shift 2
            ;;
        --full)
            FULL_REINDEX=true
            shift
            ;;
        -p|--priority)
            PRIORITY="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 -f|--folder FOLDER [--full] [-p|--priority PRIORITY]"
            echo ""
            echo "Options:"
            echo "  -f, --folder FOLDER     Folder to index (required)"
            echo "  --full                  Force full reindex"
            echo "  -p, --priority PRIORITY Indexing priority (low|normal|high)"
            echo "  -h, --help             Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate inputs
if [[ -z "$FOLDER" ]]; then
    echo "Error: Folder is required"
    echo "Use -h for help"
    exit 1
fi

if [[ ! -d "$FOLDER" ]]; then
    echo "Error: Folder does not exist: $FOLDER"
    exit 1
fi

# Activate virtual environment if it exists
if [[ -f "venv/bin/activate" ]]; then
    source venv/bin/activate
fi

# Run indexing
echo "Starting indexing of $FOLDER..."
echo "Full reindex: $FULL_REINDEX"
echo "Priority: $PRIORITY"
echo ""

ARGS=("index" "$FOLDER" "--priority" "$PRIORITY")

if [[ "$FULL_REINDEX" == "true" ]]; then
    ARGS+=("--full")
fi

python -m search_agent.cli "${ARGS[@]}"

echo ""
echo "Indexing completed successfully!"
