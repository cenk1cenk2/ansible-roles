#!/bin/bash
# Wrapper script to run Molecule tests for load_vars plugin
# This script handles environment setup and runs Molecule tests

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Molecule Test Runner for load_vars Plugin${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""

# Check if Podman is available
if ! command -v podman &> /dev/null; then
    echo -e "${RED}ERROR: Podman is not installed or not in PATH${NC}"
    echo "Please install Podman: https://podman.io/getting-started/installation"
    exit 1
fi

echo -e "${GREEN}✓${NC} Podman is available: $(podman --version)"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: Python 3 is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Python is available: $(python3 --version)"

# Check if Molecule is installed
if ! python3 -c "import molecule" &> /dev/null; then
    echo -e "${YELLOW}WARNING: Molecule is not installed${NC}"
    echo "Installing Molecule and dependencies..."
    pip install --user molecule molecule-podman ansible-core ansible-lint
else
    echo -e "${GREEN}✓${NC} Molecule is installed: $(python3 -c "import molecule; print(molecule.__version__)")"
fi

# Navigate to the collection directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo ""
echo -e "${GREEN}Current directory:${NC} $(pwd)"
echo ""

# Parse command line arguments
MOLECULE_COMMAND="${1:-test}"
MOLECULE_ARGS="${@:2}"

echo -e "${YELLOW}Running: molecule ${MOLECULE_COMMAND} ${MOLECULE_ARGS}${NC}"
echo ""

# Run Molecule
if molecule "${MOLECULE_COMMAND}" ${MOLECULE_ARGS}; then
    echo ""
    echo -e "${GREEN}=========================================${NC}"
    echo -e "${GREEN}✓ Molecule tests completed successfully!${NC}"
    echo -e "${GREEN}=========================================${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}=========================================${NC}"
    echo -e "${RED}✗ Molecule tests failed${NC}"
    echo -e "${RED}=========================================${NC}"
    exit 1
fi
