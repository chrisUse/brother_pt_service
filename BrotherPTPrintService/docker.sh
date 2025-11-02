#!/bin/bash

# Simple Docker Runner für Brother PT Service
# Handles Docker permissions automatically

set -e

# Check if we need sudo for docker
if ! docker ps >/dev/null 2>&1; then
    echo "🔒 Using sudo for Docker commands..."
    DOCKER="sudo docker"
    DOCKER_COMPOSE="sudo docker compose"
else
    DOCKER="docker"
    DOCKER_COMPOSE="docker compose"
fi

case "${1:-start}" in
    "start")
        echo "🚀 Starting Brother PT Service..."
        mkdir -p labels
        $DOCKER_COMPOSE up -d --build
        sleep 3
        echo "✅ Service started!"
        echo "📖 Docs: http://localhost:8000/docs"
        ;;
    
    "stop")
        echo "⏹️ Stopping Brother PT Service..."
        $DOCKER_COMPOSE down
        echo "✅ Service stopped!"
        ;;
    
    "logs")
        echo "📋 Service Logs:"
        $DOCKER_COMPOSE logs -f
        ;;
    
    "status")
        echo "📊 Service Status:"
        $DOCKER_COMPOSE ps
        echo ""
        if curl -s http://localhost:8000/status >/dev/null 2>&1; then
            echo "🟢 API is responding"
            curl -s http://localhost:8000/status | python3 -m json.tool 2>/dev/null || echo "API data available"
        else
            echo "🔴 API not responding"
        fi
        ;;
    
    "build")
        echo "🏗️ Rebuilding containers..."
        $DOCKER_COMPOSE build --no-cache
        echo "✅ Build complete!"
        ;;
    
    "clean")
        echo "🧹 Cleaning up..."
        $DOCKER_COMPOSE down -v --rmi all
        $DOCKER system prune -f
        echo "✅ Cleanup complete!"
        ;;
    
    "test")
        echo "🧪 Testing API..."
        if ! curl -s http://localhost:8000/status >/dev/null 2>&1; then
            echo "❌ Service not running. Start with: ./docker.sh start"
            exit 1
        fi
        
        echo "Testing Cable Label..."
        curl -X POST http://localhost:8000/print/cable \
            -H 'Content-Type: application/json' \
            -d '{"cable_type":"TEST-CABLE","voltage":"PoE","destination":"Test"}' 2>/dev/null \
            && echo "✅ Cable test OK" || echo "❌ Cable test failed"
        ;;
    
    *)
        echo "Brother PT Docker Helper"
        echo "======================="
        echo "Usage: ./docker.sh [command]"
        echo ""
        echo "Commands:"
        echo "  start   - Start service (default)"
        echo "  stop    - Stop service"
        echo "  logs    - Show logs"
        echo "  status  - Show status"
        echo "  build   - Rebuild containers"
        echo "  clean   - Clean up"
        echo "  test    - Test API"
        echo ""
        echo "Examples:"
        echo "  ./docker.sh start"
        echo "  ./docker.sh logs"
        echo "  ./docker.sh status"
        ;;
esac