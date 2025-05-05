#!/usr/bin/env python3
"""
Directly run FastAPI application without relying on workflow configurations
This script is needed to avoid conflicts with Flask when using the default main.py
"""
import sys
import os
import importlib.util
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Ensure we can import our modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    # Explicitly import fastapi_main module
    spec = importlib.util.spec_from_file_location("fastapi_main", os.path.join(current_dir, "fastapi_main.py"))
    fastapi_main = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fastapi_main)
    
    # Get the FastAPI app
    app = fastapi_main.app
    logger.info("Successfully imported FastAPI app from fastapi_main.py")
    
    # Run the app
    if __name__ == "__main__":
        import uvicorn
        logger.info("Starting FastAPI server on port 8000")
        uvicorn.run(app, host="0.0.0.0", port=8000)
        
except Exception as e:
    logger.error(f"Error loading FastAPI app: {e}")
    sys.exit(1)