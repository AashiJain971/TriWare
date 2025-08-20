# 🏥 Smart Triage Kiosk System

A comprehensive, AI-powered healthcare triage system designed for modern medical facilities with intelligent patient assessment, medical device integration, and clinical decision support. Built with HIPAA compliance, multilingual accessibility, and offline-first architecture.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![React](https://img.shields.io/badge/react-18.x-blue.svg)
![FastAPI](https://img.shields.io/badge/fastapi-0.104%2B-green.svg)

## 🚀 Features & Capabilities

### 🧠 AI-Powered Healthcare Intelligence
- **Machine Learning Triage Assessment** - XGBoost and PyTorch models for risk scoring
- **Clinical Decision Support** - Evidence-based protocols with real-time alerts
- **Predictive Analytics** - Early Warning Scores (NEWS, qSOFA, APACHE II)
- **Explainable AI** - SHAP/LIME integration for clinical transparency

### 🩺 Medical Device Integration
- **Bluetooth Low Energy (BLE) Support** - Automatic device discovery and pairing
- **Vital Signs Collection** - Blood pressure monitors, pulse oximeters, thermometers
- **Real-Time Data Streaming** - Live vital signs with quality validation
- **Device Calibration & QA** - Automated calibration procedures and drift detection

### 🌐 Universal Accessibility
- **Multilingual Interface** - English, Hindi, and extensible language support
- **Voice Guidance System** - Complete voice-driven navigation with TTS/STT
- **Accessibility Features** - Screen reader support, high contrast, large text modes
- **Touch & Gesture Controls** - Optimized for kiosk and tablet interfaces

### 🔒 Enterprise Security & Compliance
- **HIPAA Compliance** - End-to-end PHI encryption and audit logging
- **Role-Based Access Control** - Granular permissions and authentication
- **Data Loss Prevention** - Local data encryption with secure transmission
- **Clinical Audit Trail** - Comprehensive activity tracking and reporting

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   AI/ML Engine  │
│   (React PWA)   │◄──►│   (FastAPI)     │◄──►│   (Python ML)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Device Layer    │    │   Database      │    │   Queue System  │
│ (BLE Devices)   │    │ (PostgreSQL/    │    │   (Redis)       │
│                 │    │  SQLite)        │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Key Features

- **Multi-language Support**: English, Hindi, and local languages
- **Voice-Enabled Interface**: Speech-to-text and text-to-speech
- **AI-Powered Triage**: Hybrid ML models for accurate risk assessment
- **Device Integration**: BLE medical devices with auto-calibration
- **Offline-First**: Complete functionality without internet
- **Real-time Queue Management**: Dynamic load balancing
- **Clinical Decision Support**: Drug interactions, allergy alerts
- **HIPAA Compliant**: End-to-end encryption and audit logging

## 📁 Project Structure

```
TriWare/
├── backend/               # FastAPI backend service
├── frontend/              # React PWA frontend
├── mobile/                # React Native mobile app
├── ml/                    # Machine learning models
├── devices/               # Device integration layer
├── devops/                # Deployment configurations
├── docs/                  # Documentation
└── shared/                # Shared utilities and types
```

## 🛠️ Tech Stack

- **Frontend**: React 18, TypeScript, Material-UI, PWA
- **Backend**: FastAPI, PostgreSQL, Redis, Celery
- **AI/ML**: XGBoost, PyTorch, ONNX Runtime, MLflow
- **Devices**: Web Bluetooth API, GATT protocols
- **Deployment**: Docker, Kubernetes, GitHub Actions

## 📋 Requirements

- Node.js 18+
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose

## 🚀 Quick Start

```bash
# Clone and setup
git clone <repository>
cd TriWare

# Start with Docker Compose
docker-compose up -d

# Or manual setup
make setup
make dev
```

## 📊 Monitoring

- **Health Check**: `/health`
- **Metrics**: Prometheus at `:9090`
- **Logs**: ELK Stack
- **Tracing**: Jaeger

## 🔒 Security

- JWT authentication with role-based access
- End-to-end encryption for all communications
- HIPAA compliance with audit logging
- Regular security vulnerability assessments

## 📖 Documentation

- [API Documentation](./docs/api.md)
- [Frontend Guide](./docs/frontend.md)
- [ML Models](./docs/ml.md)
- [Device Integration](./docs/devices.md)
- [Deployment Guide](./docs/deployment.md)

## 🤝 Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for development guidelines.

## 📄 License

This project is licensed under the MIT License - see [LICENSE](./LICENSE) file.
