#!/bin/bash
# Twitter Bot v2.0 - Backend Startup Script

set -e

# Change to backend directory
cd "$(dirname "$0")/../backend"

# Check for virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Install Playwright browsers if not already installed
echo "Checking Playwright browsers..."
playwright install chromium

# Check for .env file
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found. Copy .env.example and configure it."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "Created .env from .env.example - please configure it."
    fi
fi

# Start the backend
echo "Starting Twitter Bot backend..."

# Check for SSL certificates
if [ -f "ssl/cert.pem" ] && [ -f "ssl/key.pem" ]; then
    echo "Starting with HTTPS..."
    uvicorn main:app \
        --host 0.0.0.0 \
        --port 8080 \
        --ssl-keyfile ssl/key.pem \
        --ssl-certfile ssl/cert.pem
else
    echo "Starting with HTTP (development mode)..."
    uvicorn main:app \
        --host 0.0.0.0 \
        --port 8080 \
        --reload
fi
