#!/bin/bash
# Production monitoring script for Amazon Pay Rate Job Monitor

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

API_URL="http://localhost:8000"
CONTAINER_NAME="amazon-pay-rate-monitor"

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  Amazon Pay Rate Job Monitor   ${NC}"
    echo -e "${BLUE}       Production Status        ${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""
}

check_container() {
    echo -e "${BLUE}📦 Container Status:${NC}"
    if docker ps | grep -q $CONTAINER_NAME; then
        echo -e "   ${GREEN}✅ Container is running${NC}"
        return 0
    else
        echo -e "   ${RED}❌ Container is not running${NC}"
        return 1
    fi
}

check_api_health() {
    echo -e "${BLUE}🔍 API Health Check:${NC}"
    if curl -s -f "$API_URL/health" > /dev/null; then
        echo -e "   ${GREEN}✅ API is healthy${NC}"
        return 0
    else
        echo -e "   ${RED}❌ API health check failed${NC}"
        return 1
    fi
}

show_api_status() {
    echo -e "${BLUE}📊 API Status:${NC}"
    status=$(curl -s "$API_URL/status" || echo '{"error": "API not available"}')
    echo "$status" | python3 -m json.tool 2>/dev/null || echo "   API not responding"
}

show_recent_logs() {
    echo -e "${BLUE}📝 Recent Logs (last 10 lines):${NC}"
    docker-compose logs --tail=10 $CONTAINER_NAME 2>/dev/null || echo "   No logs available"
}

show_resource_usage() {
    echo -e "${BLUE}💻 Resource Usage:${NC}"
    if docker ps | grep -q $CONTAINER_NAME; then
        docker stats --no-stream --format "table {{.Container}}\\t{{.CPUPerc}}\\t{{.MemUsage}}\\t{{.NetIO}}" $CONTAINER_NAME
    else
        echo "   Container not running"
    fi
}

show_job_count() {
    echo -e "${BLUE}💼 Job Statistics:${NC}"
    jobs=$(curl -s "$API_URL/jobs" 2>/dev/null || echo '{"jobs": []}')
    job_count=$(echo "$jobs" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('jobs', [])))" 2>/dev/null || echo "0")
    echo "   Total Pay Rate Jobs Found: $job_count"
}

main() {
    print_header
    
    # Container check
    if check_container; then
        container_running=true
    else
        container_running=false
    fi
    
    echo ""
    
    # API health check
    if [ "$container_running" = true ]; then
        if check_api_health; then
            api_healthy=true
        else
            api_healthy=false
        fi
    else
        api_healthy=false
    fi
    
    echo ""
    
    # Show detailed status if API is healthy
    if [ "$api_healthy" = true ]; then
        show_api_status
        echo ""
        
        show_job_count
        echo ""
    fi
    
    # Show resource usage
    show_resource_usage
    echo ""
    
    # Show recent logs
    show_recent_logs
    echo ""
    
    # Summary
    echo -e "${BLUE}📋 Summary:${NC}"
    if [ "$container_running" = true ] && [ "$api_healthy" = true ]; then
        echo -e "   ${GREEN}✅ System is operating normally${NC}"
        echo "   🌐 API: $API_URL"
        echo "   📊 Status: $API_URL/status" 
        echo "   🔍 Health: $API_URL/health"
    elif [ "$container_running" = true ]; then
        echo -e "   ${YELLOW}⚠️ Container running but API unhealthy${NC}"
        echo "   Try: docker-compose restart"
    else
        echo -e "   ${RED}❌ System is down${NC}"
        echo "   Try: docker-compose up -d"
    fi
    
    echo ""
}

# Handle command line arguments
case "${1:-status}" in
    "status"|"")
        main
        ;;
    "logs")
        echo "📝 Live logs (Ctrl+C to exit):"
        docker-compose logs -f $CONTAINER_NAME
        ;;
    "restart")
        echo "🔄 Restarting service..."
        docker-compose restart
        echo "✅ Service restarted"
        ;;
    "stop")
        echo "🛑 Stopping service..."
        docker-compose down
        echo "✅ Service stopped"
        ;;
    "start")
        echo "▶️ Starting service..."
        docker-compose up -d
        echo "✅ Service started"
        ;;
    *)
        echo "Usage: $0 [status|logs|restart|stop|start]"
        echo ""
        echo "Commands:"
        echo "  status   - Show system status (default)"
        echo "  logs     - Show live logs"
        echo "  restart  - Restart the service"
        echo "  stop     - Stop the service"
        echo "  start    - Start the service"
        ;;
esac