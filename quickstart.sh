#!/bin/bash
set -e

echo "🚀 Starting DYGSOM Fraud API..."

if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ .env created"
fi

echo "🐳 Starting Docker services..."
docker compose up -d

echo "⏳ Waiting for services..."
sleep 10

echo "✅ Services started!"
echo ""
echo "📍 URLs:"
echo "   API:    http://localhost:3000"
echo "   Health: http://localhost:3000/health"
echo "   Docs:   http://localhost:3000/docs"
