#!/usr/bin/env python3
"""
Simple ML Service for Smart Triage Kiosk System
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
import random

app = FastAPI(title="Smart Triage ML Service", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Smart Triage ML Service Running", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "ml"}

@app.post("/api/v1/triage/assess")
def assess_patient(patient_data: dict):
    """Mock triage assessment using ML"""
    
    # Mock ML prediction
    symptoms_severity = random.randint(1, 10)
    vital_signs_score = random.randint(1, 10)
    age_factor = random.randint(1, 5)
    
    total_score = symptoms_severity + vital_signs_score + age_factor
    
    if total_score >= 20:
        priority = "critical"
        wait_time = 0
    elif total_score >= 15:
        priority = "urgent"
        wait_time = 15
    elif total_score >= 10:
        priority = "semi-urgent"
        wait_time = 60
    else:
        priority = "non-urgent"
        wait_time = 120
    
    return {
        "triage_score": total_score,
        "priority": priority,
        "estimated_wait_time": wait_time,
        "confidence": random.uniform(0.8, 0.95),
        "recommendations": [
            f"Priority level: {priority}",
            f"Estimated wait time: {wait_time} minutes",
            "Monitor vital signs" if priority in ["critical", "urgent"] else "Standard monitoring"
        ]
    }

@app.post("/api/v1/vitals/analyze")
def analyze_vitals(vitals_data: dict):
    """Analyze vital signs"""
    
    return {
        "analysis": "Normal ranges",
        "alerts": [],
        "trends": "Stable",
        "recommendations": ["Continue monitoring", "No immediate action required"]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
