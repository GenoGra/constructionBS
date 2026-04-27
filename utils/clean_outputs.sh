#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
RESULTS_DIR="$ROOT_DIR/results"

DRY_RUN=false

if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
    TEST_NAME="${2:-}"
    TOOL_NAME="${3:-}"
else
    TEST_NAME="${1:-}"
    TOOL_NAME="${2:-}"
fi

if [[ -z "${TEST_NAME:-}" || -z "${TOOL_NAME:-}" ]]; then
    echo "Usage:"
    echo "  ./utils/clean_outputs.sh TEST_NAME TOOL_NAME"
    echo "  ./utils/clean_outputs.sh --dry-run TEST_NAME TOOL_NAME"
    exit 1
fi

VALID_NAME_PATTERN='^[A-Za-z0-9_-]+$'
if [[ ! "$TEST_NAME" =~ $VALID_NAME_PATTERN ]]; then
    echo "Invalid TEST_NAME: $TEST_NAME"
    echo "Allowed characters: letters, numbers, underscore, hyphen"
    exit 1
fi

if [[ ! "$TOOL_NAME" =~ $VALID_NAME_PATTERN ]]; then
    echo "Invalid TOOL_NAME: $TOOL_NAME"
    echo "Allowed characters: letters, numbers, underscore, hyphen"
    exit 1
fi

TARGET_DIR="$RESULTS_DIR/$TEST_NAME/$TOOL_NAME"
OUTPUTS_DIR="$TARGET_DIR/outputs"
LOGS_DIR="$TARGET_DIR/logs"

require_safe_path() {
    local target_path="$1"
    local expected_prefix="$2"

    case "$target_path" in
        "$expected_prefix"/*) ;;
        *)
            echo "Refusing unsafe path outside expected directory: $target_path"
            exit 1
            ;;
    esac
}

require_safe_path "$TARGET_DIR" "$RESULTS_DIR"
require_safe_path "$OUTPUTS_DIR" "$RESULTS_DIR"
require_safe_path "$LOGS_DIR" "$RESULTS_DIR"

echo "Root directory: $ROOT_DIR"
echo "Target tool directory: $TARGET_DIR"
echo "Dry run: $DRY_RUN"
echo

echo "This script will clean the previous result for:"
echo "  Test: $TEST_NAME"
echo "  Tool: $TOOL_NAME"
echo

echo "Directories to clean:"
echo "  $OUTPUTS_DIR"
echo "  $LOGS_DIR"
echo

if [[ ! -d "$TARGET_DIR" ]]; then
    echo "Target directory does not exist: $TARGET_DIR"
    exit 1
fi

if [[ "$DRY_RUN" == true ]]; then
    echo "[DRY-RUN] rm -rf $OUTPUTS_DIR"
    echo "[DRY-RUN] rm -rf $LOGS_DIR"
    echo "[DRY-RUN] mkdir -p $OUTPUTS_DIR $LOGS_DIR"
    echo
    echo "No files were removed."
    exit 0
fi

read -r -p "Proceed with cleanup? [y/N] " CONFIRM
if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
    echo "Aborted."
    exit 0
fi

echo "[REMOVE] Previous outputs and logs"
rm -rf "$OUTPUTS_DIR"
rm -rf "$LOGS_DIR"

echo "[CREATE] Fresh output directories"
mkdir -p "$OUTPUTS_DIR"
mkdir -p "$LOGS_DIR"

echo
echo "Clean workspace ready for:"
echo "  $TARGET_DIR"
