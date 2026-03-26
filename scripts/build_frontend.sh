#!/bin/bash
# Twitter Bot v2.0 - Frontend Build Script

set -e

# Change to frontend directory
cd "$(dirname "$0")/../frontend"

# Check for node_modules
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Build for production
echo "Building Twitter Bot frontend for production..."
npm run build

echo ""
echo "=== Build Complete ==="
echo "Production files are in: frontend/dist/"
echo "These will be served by the FastAPI backend automatically."
