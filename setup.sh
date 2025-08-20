#!/bin/bash

# Smart Triage Kiosk System - Complete Setup Script
# This script sets up the entire development environment

set -e

echo "🏥 Setting up Smart Triage Kiosk System..."
echo "========================================"

# Check if required tools are installed
check_dependencies() {
    echo "📋 Checking system dependencies..."
    
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python 3.8+ is required but not installed"
        exit 1
    fi
    
    if ! command -v node &> /dev/null; then
        echo "❌ Node.js 18+ is required but not installed"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker is required but not installed"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ Docker Compose is required but not installed"
        exit 1
    fi
    
    echo "✅ System dependencies verified"
}

# Setup Python virtual environment and backend
setup_backend() {
    echo "🐍 Setting up Python backend..."
    
    cd backend
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        echo "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install dependencies
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        echo "Creating backend .env file..."
        cat > .env << EOL
# Database
DATABASE_URL=postgresql://triware:triware@localhost:5432/triware
REDIS_URL=redis://localhost:6379
TEST_DATABASE_URL=sqlite:///./test.db

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# MLflow
MLFLOW_TRACKING_URI=http://localhost:5000

# API Settings
API_V1_STR=/api/v1
PROJECT_NAME=Smart Triage Kiosk
VERSION=1.0.0

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:3000","https://localhost:3000","http://localhost","https://localhost"]

# Healthcare Settings
HIPAA_COMPLIANT=true
FHIR_BASE_URL=http://localhost:8080/fhir

# Device Integration
BLUETOOTH_ENABLED=true
DEVICE_TIMEOUT=30

# Monitoring
SENTRY_DSN=
LOG_LEVEL=INFO
EOL
    fi
    
    echo "✅ Backend setup complete"
    cd ..
}

# Setup Node.js frontend
setup_frontend() {
    echo "⚛️  Setting up React frontend..."
    
    cd frontend
    
    # Install dependencies
    echo "Installing Node.js dependencies..."
    npm install
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        echo "Creating frontend .env file..."
        cat > .env << EOL
# API Configuration
REACT_APP_API_BASE_URL=http://localhost:8000/api/v1
REACT_APP_WS_URL=ws://localhost:8000/ws

# Feature Flags
REACT_APP_ENABLE_VOICE=true
REACT_APP_ENABLE_CAMERA=true
REACT_APP_ENABLE_BLUETOOTH=true
REACT_APP_ENABLE_OFFLINE=true

# PWA Settings
REACT_APP_APP_NAME=Smart Triage Kiosk
REACT_APP_THEME_COLOR=#1976d2

# Development
REACT_APP_DEBUG=true
GENERATE_SOURCEMAP=true
DISABLE_ESLINT_PLUGIN=false
EOL
    fi
    
    echo "✅ Frontend setup complete"
    cd ..
}

# Setup ML service
setup_ml_service() {
    echo "🤖 Setting up ML service..."
    
    cd ml
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        echo "Creating ML service virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Create .env file
    if [ ! -f ".env" ]; then
        echo "Creating ML service .env file..."
        cat > .env << EOL
# ML Service Configuration
ML_SERVICE_PORT=8001
MODEL_PATH=./models
MLFLOW_TRACKING_URI=http://localhost:5000

# Model Settings
TRIAGE_MODEL=xgboost_triage_v1.pkl
RISK_THRESHOLD=0.7
BATCH_SIZE=32

# Inference Settings
MAX_CONCURRENT_REQUESTS=10
TIMEOUT_SECONDS=30
EOL
    fi
    
    echo "✅ ML service setup complete"
    cd ..
}

# Initialize database
init_database() {
    echo "🗄️  Initializing database..."
    
    cd backend
    source venv/bin/activate
    
    # Create database migration
    echo "Creating database migration..."
    alembic revision --autogenerate -m "Initial migration"
    
    # Apply migration
    echo "Applying database migration..."
    alembic upgrade head
    
    echo "✅ Database initialized"
    cd ..
}

# Setup Docker services
setup_docker() {
    echo "🐳 Setting up Docker services..."
    
    # Pull required images
    docker-compose pull
    
    # Build custom images
    docker-compose build
    
    echo "✅ Docker setup complete"
}

# Create development scripts
create_scripts() {
    echo "📝 Creating development scripts..."
    
    # Backend development script
    cat > run_backend.sh << 'EOF'
#!/bin/bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
EOF
    
    # Frontend development script
    cat > run_frontend.sh << 'EOF'
#!/bin/bash
cd frontend
npm start
EOF
    
    # ML service development script
    cat > run_ml_service.sh << 'EOF'
#!/bin/bash
cd ml
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8001
EOF
    
    # Full system development script
    cat > run_dev.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting Smart Triage Kiosk System in development mode..."

# Start services in background
docker-compose up -d postgres redis mlflow minio prometheus grafana

# Wait for services to be ready
sleep 10

# Start backend
cd backend && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Start ML service
cd ml && source venv/bin/activate && uvicorn main:app --reload --host 0.0.0.0 --port 8001 &
ML_PID=$!

# Start frontend
cd frontend && npm start &
FRONTEND_PID=$!

echo "🎉 System started!"
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8000"
echo "ML Service: http://localhost:8001"
echo "API Docs: http://localhost:8000/docs"
echo "MLflow: http://localhost:5000"
echo "Grafana: http://localhost:3001"

# Wait for Ctrl+C
trap 'kill $BACKEND_PID $ML_PID $FRONTEND_PID; docker-compose down; exit' INT
wait
EOF
    
    # Production deployment script
    cat > deploy_prod.sh << 'EOF'
#!/bin/bash
echo "🚢 Deploying Smart Triage Kiosk System to production..."

# Build production images
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# Deploy with rolling update
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

echo "🎉 Production deployment complete!"
echo "Monitor at: http://localhost:3001 (Grafana)"
EOF
    
    # Make scripts executable
    chmod +x run_backend.sh run_frontend.sh run_ml_service.sh run_dev.sh deploy_prod.sh
    
    echo "✅ Development scripts created"
}

# Create production configuration
create_prod_config() {
    echo "🏭 Creating production configuration..."
    
    cat > docker-compose.prod.yml << 'EOF'
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    environment:
      - NODE_ENV=production
    
  backend:
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=WARNING
      - DATABASE_URL=postgresql://triware:${POSTGRES_PASSWORD}@postgres:5432/triware
    
  ml-service:
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=WARNING
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/ssl/certs:ro
    depends_on:
      - frontend
      - backend
      - ml-service
    
  postgres:
    environment:
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data_prod:/var/lib/postgresql/data
    
volumes:
  postgres_data_prod:
EOF
    
    echo "✅ Production configuration created"
}

# Create health check script
create_health_check() {
    echo "🩺 Creating health check script..."
    
    cat > health_check.sh << 'EOF'
#!/bin/bash
echo "🔍 Smart Triage System Health Check"
echo "=================================="

# Check backend
echo -n "Backend API: "
if curl -sf http://localhost:8000/health > /dev/null; then
    echo "✅ HEALTHY"
else
    echo "❌ UNHEALTHY"
fi

# Check ML service
echo -n "ML Service: "
if curl -sf http://localhost:8001/health > /dev/null; then
    echo "✅ HEALTHY"
else
    echo "❌ UNHEALTHY"
fi

# Check frontend
echo -n "Frontend: "
if curl -sf http://localhost:3000 > /dev/null; then
    echo "✅ HEALTHY"
else
    echo "❌ UNHEALTHY"
fi

# Check database
echo -n "Database: "
if docker-compose exec -T postgres pg_isready -U triware > /dev/null 2>&1; then
    echo "✅ HEALTHY"
else
    echo "❌ UNHEALTHY"
fi

# Check Redis
echo -n "Redis: "
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ HEALTHY"
else
    echo "❌ UNHEALTHY"
fi

echo ""
echo "📊 System Status:"
docker-compose ps
EOF
    
    chmod +x health_check.sh
    
    echo "✅ Health check script created"
}

# Main setup function
main() {
    echo "Starting Smart Triage Kiosk System setup..."
    echo ""
    
    check_dependencies
    echo ""
    
    setup_backend
    echo ""
    
    setup_frontend
    echo ""
    
    setup_ml_service
    echo ""
    
    setup_docker
    echo ""
    
    create_scripts
    echo ""
    
    create_prod_config
    echo ""
    
    create_health_check
    echo ""
    
    # Start core services
    echo "🚀 Starting core services..."
    docker-compose up -d postgres redis mlflow minio
    
    # Wait for services
    echo "⏳ Waiting for services to start..."
    sleep 15
    
    # Initialize database
    init_database
    echo ""
    
    echo "🎉 Setup complete!"
    echo ""
    echo "Next steps:"
    echo "1. Run './run_dev.sh' to start the development environment"
    echo "2. Visit http://localhost:3000 to access the application"
    echo "3. API documentation: http://localhost:8000/docs"
    echo "4. MLflow UI: http://localhost:5000"
    echo "5. Grafana monitoring: http://localhost:3001 (admin/admin)"
    echo ""
    echo "For production deployment, run './deploy_prod.sh'"
    echo "For system health checks, run './health_check.sh'"
}

# Run main function
main "$@"
