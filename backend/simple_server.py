#!/usr/bin/env python3
"""
Simple Backend Server for Smart Triage Kiosk System
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="Smart Triage Kiosk API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Smart Triage Kiosk Backend Server Running", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "backend"}

@app.get("/api/v1/patients")
def get_patients():
    return {"patients": [], "message": "Patient API endpoint"}

@app.get("/api/v1/devices")
def get_devices():
    return {"devices": [], "message": "Device API endpoint"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
