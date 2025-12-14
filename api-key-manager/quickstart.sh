#!/bin/bash

# API Key Management System - Quick Start Script
# Designed & Engineered by Mayank Sharma
# https://mayyanks.app

set -e

echo "🔐 API Key Management System - Quick Start"
echo "Designed & Engineered by Mayank Sharma"
echo "https://mayyanks.app"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please copy .env.example to .env and configure your settings:"
    echo "  cp .env.example .env"
    echo ""
    echo "Generate encryption key with:"
    echo "  python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
    exit 1
fi

echo "✅ Environment file found"

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt

echo "✅ Dependencies installed"

# Run server
echo ""
echo "🚀 Starting server on http://localhost:8000"
echo ""
echo "Available endpoints:"
echo "  - Health: http://localhost:8000/health"
echo "  - Dashboard: http://localhost:8000/"
echo "  - API Docs: http://localhost:8000/docs"
echo ""
echo "Test commands:"
echo "  # Register"
echo "  curl -X POST http://localhost:8000/api/v1/auth/register \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"email\":\"test@example.com\",\"username\":\"testuser\",\"password\":\"SecurePass123!\"}'"
echo ""
echo "  # Login"
echo "  curl -X POST http://localhost:8000/api/v1/auth/login \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"email\":\"test@example.com\",\"password\":\"SecurePass123!\"}'"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
