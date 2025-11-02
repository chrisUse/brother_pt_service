#!/bin/# Detect Docker Compose command and permissions
DOCKER_SUDO=""
if ! docker ps >/dev/null 2>&1; then
    echo "⚠️ Docker Permission Problem - verwende sudo"
    DOCKER_SUDO="sudo"
fi

if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="$DOCKER_SUDO docker-compose"
elif $DOCKER_SUDO docker compose version &> /dev/null 2>&1; then
    COMPOSE_CMD="$DOCKER_SUDO docker compose"
else
    echo "❌ Docker Compose ist nicht verfügbar!"
    echo "💡 Installation: sudo apt install docker-compose-plugin"
    echo "💡 Docker Permission: sudo usermod -aG docker \$USER && newgrp docker"
    exit 1
fiother PT-E550W Docker Management Script
# Pure Docker-native approach - no Makefile needed!

set -e  # Exit on any error

# Detect Docker Compose command
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo "❌ Docker Compose ist nicht verfügbar!"
    echo "� Installation: sudo apt install docker-compose-plugin"
    exit 1
fi

# Helper function
show_usage() {
    echo "�🐳 Brother PT-E550W Docker Management"
    echo "====================================="
    echo ""
    echo "USAGE: ./deploy.sh [COMMAND]"
    echo ""
    echo "COMMANDS:"
    echo "  start         - Start the service (default)"
    echo "  stop          - Stop the service"  
    echo "  restart       - Restart the service"
    echo "  status        - Show service status"
    echo "  logs          - Show service logs"
    echo "  build         - Rebuild containers"
    echo "  clean         - Clean up containers and images"
    echo "  test          - Run API tests"
    echo "  shell         - Open container shell"
    echo ""
    echo "EXAMPLES:"
    echo "  ./deploy.sh                    # Start service"
    echo "  ./deploy.sh logs               # Show logs"
    echo "  ./deploy.sh test               # Test API"
    echo ""
}

# Check Docker availability
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker ist nicht installiert!"
        echo "💡 Installation: curl -fsSL https://get.docker.com | sh"
        exit 1
    fi
}

# Start service
start_service() {
    echo "🚀 Starting Brother PT-E550W Service..."
    
    # Create directories
    mkdir -p ./labels
    
    # Docker Compose up (builds automatically if needed)
    echo "▶️ Starting services (auto-build if needed)..."
    $COMPOSE_CMD up -d --build
    
    # Wait for service to be ready
    echo "⏳ Waiting for service to be ready..."
    sleep 5
    
    # Check if service is responding
    if curl -s http://localhost:8000/status > /dev/null 2>&1; then
        echo ""
        echo "✅ Brother PT-E550W API erfolgreich gestartet!"
        show_endpoints
    else
        echo "⚠️ Service gestartet, aber noch nicht bereit. Logs prüfen:"
        $COMPOSE_CMD logs --tail=10 brother-label-api
    fi
}

# Stop service
stop_service() {
    echo "⏹️ Stopping Brother PT-E550W Service..."
    $COMPOSE_CMD down
    echo "✅ Service gestoppt!"
}

# Show service status
show_status() {
    echo "📊 Brother PT-E550W Service Status:"
    echo "=================================="
    $COMPOSE_CMD ps
    echo ""
    
    # Try health check
    if curl -s http://localhost:8000/status > /dev/null 2>&1; then
        echo "🟢 API Health Check:"
        curl -s http://localhost:8000/status | python3 -m json.tool
    else
        echo "🔴 API nicht erreichbar"
    fi
}

# Show logs
show_logs() {
    echo "� Service Logs:"
    echo "================"
    $COMPOSE_CMD logs -f --tail=50
}

# Build containers
build_service() {
    echo "🏗️ Building Brother PT-E550W Service..."
    echo "📥 Brother PT library wird aus GitHub geclont..."
    $COMPOSE_CMD build --no-cache
    echo "✅ Build completed!"
}

# Clean up
clean_service() {
    echo "🧹 Cleaning up Docker containers and images..."
    $COMPOSE_CMD down -v --rmi all
    docker system prune -f
    echo "✅ Cleanup completed!"
}

# Run tests
test_service() {
    echo "🧪 Testing Brother PT-E550W API..."
    echo "================================="
    
    # Check if service is running
    if ! curl -s http://localhost:8000/status > /dev/null 2>&1; then
        echo "❌ Service ist nicht erreichbar. Starten Sie zuerst mit: ./deploy.sh start"
        exit 1
    fi
    
    echo "1. 📊 Service Status:"
    curl -s http://localhost:8000/status | python3 -m json.tool
    echo ""
    
    echo "2. 🔌 Test Cable Label:"
    curl -X POST http://localhost:8000/print/cable \
        -H 'Content-Type: application/json' \
        -d '{"cable_type":"TEST-CAT6","voltage":"PoE","destination":"Test Port"}' \
        | python3 -m json.tool
    echo ""
    
    echo "3. 💻 Test Device Label:"
    curl -X POST http://localhost:8000/print/device \
        -H 'Content-Type: application/json' \
        -d '{"device_name":"TEST-SW-01","ip_address":"192.168.1.100"}' \
        | python3 -m json.tool
    echo ""
    
    echo "4. ⚠️ Test Warning Label:"
    curl -X POST http://localhost:8000/print/warning \
        -H 'Content-Type: application/json' \
        -d '{"warning_text":"TEST WARNING","voltage":"230V","icon":"⚡"}' \
        | python3 -m json.tool
}

# Open container shell
open_shell() {
    echo "� Opening container shell..."
    $COMPOSE_CMD exec brother-label-api /bin/bash
}

# Show endpoints
show_endpoints() {
    echo ""
    echo "🌐 API Endpunkte:"
    echo "   - Service Info: http://localhost:8000/"
    echo "   - API Docs:     http://localhost:8000/docs"
    echo "   - API Status:   http://localhost:8000/status"
    echo "   - Nginx Proxy:  http://localhost/ (falls aktiviert)"
    echo ""
    echo "🔌 Schnell-Kommandos:"
    echo "   - Status:  ./deploy.sh status"
    echo "   - Logs:    ./deploy.sh logs"
    echo "   - Test:    ./deploy.sh test" 
    echo "   - Stop:    ./deploy.sh stop"
    echo ""
    echo "🏷️ API Beispiele:"
    echo "# Kabel-Label"
    echo "curl -X POST http://localhost:8000/print/cable \\"
    echo "  -H 'Content-Type: application/json' \\"
    echo "  -d '{\"cable_type\":\"CAT6\",\"voltage\":\"PoE\",\"destination\":\"Switch Port 12\"}'"
    echo ""
}

# Main logic
main() {
    check_docker
    
    case "${1:-start}" in
        "start"|"")
            start_service
            ;;
        "stop")
            stop_service
            ;;
        "restart")
            stop_service
            sleep 2
            start_service
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs
            ;;
        "build")
            build_service
            ;;
        "clean")
            clean_service
            ;;
        "test")
            test_service
            ;;
        "shell")
            open_shell
            ;;
        "help"|"-h"|"--help")
            show_usage
            ;;
        *)
            echo "❌ Unbekannter Befehl: $1"
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"