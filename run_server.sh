#!/bin/bash
# Snappr API MCP Server Runner (uvx version)
# This script sets up the environment and runs the MCP server using uvx

set -e  # Exit on any error

# Colors for output (only shown during setup, not when running)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Snappr MCP Server with uvx...${NC}" >&2

# Navigate to the script directory
cd "$(dirname "$0")"
echo -e "${GREEN}📁 Working directory: $(pwd)${NC}" >&2

# Check if uv/uvx is installed
if ! command -v uvx >/dev/null 2>&1; then
    echo -e "${RED}❌ Error: 'uvx' is not installed${NC}" >&2
    echo -e "${YELLOW}💡 Install uv (which includes uvx) with: curl -LsSf https://astral.sh/uv/install.sh | sh${NC}" >&2
    exit 1
fi

echo -e "${GREEN}✅ uvx found: $(uvx --version 2>/dev/null || echo 'uvx available')${NC}" >&2

# Load environment variables
if [ -f .env ]; then
    echo -e "${GREEN}📋 Loading environment variables from .env${NC}" >&2
    set -a
    source .env >/dev/null 2>&1
    set +a
    echo -e "${GREEN}✅ Environment variables loaded${NC}" >&2
else
    echo -e "${YELLOW}⚠️  No .env file found${NC}" >&2
fi

# Validate required environment variables
if [ -z "$SNAPPR_API_KEY" ] || [ "$SNAPPR_API_KEY" = "your_snappr_api_key_here" ]; then
    echo -e "${RED}❌ Error: SNAPPR_API_KEY not set in .env file${NC}" >&2
    echo -e "${YELLOW}💡 Please edit .env and set your actual Snappr API key${NC}" >&2
    exit 1
fi

# Show configuration (to stderr, so it doesn't interfere with MCP JSON)
echo -e "${GREEN}🔧 Snappr API Configuration:${NC}" >&2
echo -e "${GREEN}   🔑 API Key: ${SNAPPR_API_KEY:0:15}...${NC}" >&2
if [ "$SNAPPR_USE_SANDBOX" = "true" ]; then
    echo -e "${GREEN}   🌍 Environment: Sandbox${NC}" >&2
else
    echo -e "${GREEN}   🌍 Environment: Production${NC}" >&2
fi

echo -e "${GREEN}🚀 Starting MCP Server with uvx...${NC}" >&2

# Run the MCP server using uvx
# uvx will automatically handle the virtual environment and dependencies
exec uvx --from . snappr-mcp