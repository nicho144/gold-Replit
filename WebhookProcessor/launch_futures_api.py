#!/usr/bin/env python3
"""
Launcher for Futures Market Analysis API
This launcher ensures we're using a clean Python process
"""
import os
import sys
import subprocess

def main():
    # Get the path to the Python interpreter
    python_path = sys.executable
    
    # Get the current working directory
    cwd = os.getcwd()
    
    # Command to run uvicorn with our FastAPI app
    command = [
        python_path, 
        "-c", 
        "import uvicorn; uvicorn.run('futures_api:api', host='0.0.0.0', port=8000, reload=True)"
    ]
    
    # Print info
    print(f"Starting Futures Market Analysis API...")
    print(f"Using Python interpreter: {python_path}")
    print(f"Working directory: {cwd}")
    
    # Execute uvicorn with the API
    try:
        subprocess.run(command, check=True, cwd=cwd)
    except subprocess.CalledProcessError as e:
        print(f"Error starting API: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("API server stopped.")
        sys.exit(0)

if __name__ == "__main__":
    main()