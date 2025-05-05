#!/bin/bash
# Run the FastAPI server on port 8000

# Make sure all dependencies are installed
pip install fastapi uvicorn yfinance pydantic

# Run the FastAPI server
uvicorn fastapi_main:app --host=0.0.0.0 --port=8000