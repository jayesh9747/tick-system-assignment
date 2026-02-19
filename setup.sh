#!/bin/bash
# Setup script for Market Tick System

echo "=========================================="
echo "Market Tick System - Setup Script"
echo "=========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker Desktop first."
    echo "   Download from: https://www.docker.com/products/docker-desktop"
    exit 1
fi

echo "✅ Docker is installed"

# Check if user is in docker group
if groups | grep -q docker; then
    echo "✅ User is in docker group"
else
    echo "⚠️  User is NOT in docker group"
    echo ""
    echo "Please run the following commands to fix Docker permissions:"
    echo ""
    echo "    sudo usermod -aG docker $USER"
    echo "    newgrp docker"
    echo ""
    echo "Or if you prefer, log out and log back in for changes to take effect."
    echo ""
    echo "After fixing permissions, run this script again."
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo "❌ Docker daemon is not running. Please start Docker Desktop."
    exit 1
fi

echo "✅ Docker daemon is running"
echo ""

# Build containers
echo "🔨 Building Docker containers (this may take 5-10 minutes)..."
docker compose build

if [ $? -ne 0 ]; then
    echo "❌ Build failed. Please check the errors above."
    exit 1
fi

echo "✅ Docker containers built successfully"
echo ""

# Start services
echo "🚀 Starting all services..."
docker compose up -d

if [ $? -ne 0 ]; then
    echo "❌ Failed to start services. Please check the errors above."
    exit 1
fi

echo "✅ Services started successfully"
echo ""

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy (30 seconds)..."
sleep 30

# Check service status
echo ""
echo "📊 Service Status:"
docker compose ps

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Access Django Admin (superuser is auto-created):"
echo "   URL:      http://localhost:8000/admin"
echo "   Username: admin"
echo "   Password: changeme123"
echo ""
echo "2. Create a Broker in Admin:"
echo "   Type: BINANCE | Name: Binance Live | Api config: {}"
echo ""
echo "3. Add Scripts under that Broker:"
echo "   Bitcoin  → BTCUSDT"
echo "   Ethereum → ETHUSDT"
echo "   Pepe     → PEPEUSDT"
echo ""
echo "4. Start the tick producer:"
echo "   docker compose --profile producer up tick_producer"
echo ""
echo "Useful commands:"
echo "  - View all logs:      docker compose logs -f"
echo "  - View producer logs: docker compose logs -f tick_producer"
echo "  - Stop services:      docker compose down"
echo "  - Restart:            docker compose restart"
echo ""
