#!/bin/bash
set -e

echo "Ethos Full Stack Startup"
echo "========================"

if [ ! -f .env ]; then
    echo ".env not found. Creating from template..."
    cp .env.example .env
    echo "Edit .env with your API keys, then run again."
    exit 1
fi

API_KEY=$(grep OPEN_TERMINAL_API_KEY .env | cut -d= -f2)
if [ -z "$API_KEY" ] || [ "$API_KEY" = "your-random-secret-key-change-me" ]; then
    echo "Error: OPEN_TERMINAL_API_KEY not configured"
    echo "Edit .env and set a proper API key"
    exit 1
fi

for port in 8000 8080 3000; do
    if netstat -tulpn 2>/dev/null | grep -q ":$port "; then
        echo "Error: Port $port is already in use"
        exit 1
    fi
done

echo "Configuration OK"
echo

echo "Starting Docker services..."
docker-compose up -d

echo
echo "Waiting for services to be healthy..."
sleep 10

echo "Health checks:"

if curl -s http://localhost:8080/v1/models > /dev/null; then
    echo "  OK Ethos API: http://localhost:8080"
else
    echo "  FAIL Ethos API: NOT RESPONDING"
fi

if curl -s -H "Authorization: Bearer $API_KEY" http://localhost:8000/health > /dev/null; then
    echo "  OK Open Terminal: http://localhost:8000"
else
    echo "  FAIL Open Terminal: NOT RESPONDING"
fi

if curl -s http://localhost:3000 > /dev/null; then
    echo "  OK Ethos Frontend: http://localhost:3000"
else
    echo "  FAIL Ethos Frontend: NOT RESPONDING"
fi

echo
echo "Full stack ready"
echo "Open http://localhost:3000 in your browser"
echo
echo "Useful commands:"
echo "  docker-compose logs -f ethos-api"
echo "  docker-compose logs -f open-terminal"
echo "  docker-compose logs -f ethos-frontend"
echo "  docker-compose down"
