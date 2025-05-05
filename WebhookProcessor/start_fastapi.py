#!/usr/bin/env python3
"""
Simple launcher script for FastAPI
"""
import uvicorn

if __name__ == "__main__":
    print("Starting FastAPI server on port 8000")
    uvicorn.run("fresh_fastapi_main:app", host="0.0.0.0", port=8000)