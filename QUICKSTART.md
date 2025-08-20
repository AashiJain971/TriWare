# 🚀 Quick Start Guide - Smart Triage Kiosk System

This guide will help you get the Smart Triage Kiosk System up and running in under 10 minutes.

## 📋 Prerequisites

Before starting, ensure you have:

- **Python 3.8+** (`python3 --version`)
- **Node.js 18+** (`node --version`)  
- **Docker & Docker Compose** (`docker --version && docker-compose --version`)
- **Git** (`git --version`)

### System Requirements
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 20GB free space
- **OS**: macOS, Linux, or Windows with WSL2
- **Network**: Internet connection for initial setup

## 🎯 One-Command Setup

The fastest way to get started:

```bash
# Clone and setup everything
git clone <repository-url>
cd TriWare
./setup.sh && ./run_dev.sh
```

That's it! The system will be available at:
- **Web App**: http://localhost:3000
- **Backend API**: http://localhost:8000/docs

## 📖 Step-by-Step Setup

If you prefer a manual approach or need to troubleshoot:

### 1. Clone Repository
```bash
git clone <repository-url>
cd TriWare
```

### 2. Start Infrastructure Services
```bash
# Start PostgreSQL, Redis, MLflow, and monitoring
docker-compose up -d postgres redis mlflow minio prometheus grafana

# Verify services are running
docker-compose ps
```

### 3. Backend Setup
```bash
cd backend

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Initialize database
alembic upgrade head

# Start backend API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. ML Service Setup
```bash
# In a new terminal
cd ml

# Create ML service environment
python3 -m venv venv
source venv/bin/activate

# Install ML dependencies
pip install -r requirements.txt

# Start ML service
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

### 5. Frontend Setup
```bash
# In a new terminal
cd frontend

# Install Node.js dependencies
npm install

# Start development server
npm start
```

## 🔍 Verification & Testing

### Health Checks
```bash
# Run system health check
./health_check.sh

# Manual verification
curl http://localhost:8000/health  # Backend
curl http://localhost:8001/health  # ML Service
curl http://localhost:3000         # Frontend
```

### Quick Test Flow
1. **Open Web App**: Visit http://localhost:3000
2. **Register Test Patient**: Use the patient registration form
3. **Device Discovery**: Try BLE device scanning
4. **Triage Assessment**: Complete a sample triage
5. **View Analytics**: Check the monitoring dashboard

## 🛠️ Development Tools

### API Documentation
- **Interactive Docs**: http://localhost:8000/docs (Swagger UI)
- **ReDoc**: http://localhost:8000/redoc (Alternative docs)
- **OpenAPI Schema**: http://localhost:8000/openapi.json

### Monitoring Dashboards
- **Grafana**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090
- **MLflow**: http://localhost:5000
- **MinIO**: http://localhost:9001 (minio/minio123)

### Development Commands
```bash
# Backend development
cd backend && source venv/bin/activate
uvicorn app.main:app --reload --log-level debug

# Frontend development with hot reload
cd frontend && npm start

# Run tests
cd backend && pytest tests/ -v
cd frontend && npm test
```

## 📱 Device Integration Testing

### Simulated Medical Devices
If you don't have physical BLE medical devices:

```bash
# Start device simulator
cd backend
python scripts/device_simulator.py --devices bp,oximeter,thermometer
```

### Real Device Setup
For actual BLE medical devices:

1. **Enable Bluetooth** on your system
2. **Put devices in pairing mode**
3. **Use device discovery** in the web interface
4. **Follow calibration prompts**

Supported devices:
- **Blood Pressure**: Omron, A&D Medical, Welch Allyn
- **Pulse Oximeters**: Nonin, Masimo, Contec  
- **Thermometers**: Braun, Omron, iHealth

## 🚨 Troubleshooting

### Common Issues

#### Services Won't Start
```bash
# Check if ports are in use
lsof -i :3000,8000,8001,5432,6379,5000

# Kill conflicting processes
sudo pkill -f "port 8000"

# Restart Docker services
docker-compose down && docker-compose up -d
```

#### Database Connection Errors
```bash
# Reset database
docker-compose down -v
docker-compose up -d postgres
cd backend && alembic upgrade head
```

#### BLE Device Issues
```bash
# Check Bluetooth status (Linux/Mac)
bluetoothctl show

# Reset Bluetooth (Mac)
sudo pkill bluetoothd

# Install BLE dependencies (Linux)
sudo apt-get install bluetooth bluez-utils
```

#### Python/Node Version Issues
```bash
# Use version managers
# Python: pyenv install 3.11
# Node: nvm install 18

# Or use Docker for development
docker-compose -f docker-compose.dev.yml up
```

### Performance Optimization

#### For Low-Memory Systems
```bash
# Reduce Docker memory usage
export COMPOSE_DOCKER_CLI_BUILD=1
export DOCKER_BUILDKIT=1

# Use SQLite instead of PostgreSQL
export DATABASE_URL=sqlite:///./app.db
```

#### For Slow Networks
```bash
# Use local package mirrors
pip install -i https://pypi.douban.com/simple/ -r requirements.txt
npm config set registry https://registry.npmmirror.com
```

## 🎯 Next Steps

Once everything is running:

1. **Explore the Interface**
   - Patient registration flow
   - Triage assessment process
   - Device management panel
   - Analytics dashboard

2. **Configure Your Environment**
   - Set up authentication
   - Configure device integrations
   - Customize clinical protocols
   - Set up monitoring alerts

3. **Production Deployment**
   - Review security settings
   - Configure SSL certificates
   - Set up backup procedures
   - Deploy to staging environment

## 📞 Need Help?

- **Documentation**: Check `/docs` folder for detailed guides
- **Issues**: Create GitHub issue for bugs
- **Questions**: Start a GitHub discussion
- **Security**: Email security@yourdomain.com

## 📚 Additional Resources

- [Architecture Overview](./docs/architecture.md)
- [API Reference](./docs/api.md) 
- [Device Integration Guide](./docs/devices.md)
- [Deployment Guide](./docs/deployment.md)
- [Security Best Practices](./docs/security.md)

---

**🎉 Welcome to Smart Triage! You're ready to revolutionize healthcare delivery.**
