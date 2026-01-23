#!/bin/bash

# Deploy script for production (VPS or server)

echo "Starting deploy..."

# Pull latest code
git pull origin main

# Build Docker images
docker-compose build

# Run migrations (if using Alembic)
# docker-compose run web alembic upgrade head

# Start services
docker-compose up -d

# Run tests in container
docker-compose exec web pytest tests/

echo "Deploy complete. App running on port 8000."