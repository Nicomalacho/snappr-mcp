#!/bin/bash
# Snappr API MCP Server Runner

# Navigate to the script directory
cd "$(dirname "$0")"

# Use uv to run with proper environment
uv run app.py