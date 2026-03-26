#!/bin/bash
# Twitter Bot v2.0 - Frontend Development Server Script

set -e

# Change to frontend directory
cd "$(dirname "$0")/../frontend"

# Check for node_modules
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Start development server
echo "Starting Twitter Bot frontend development server..."
npm run dev
