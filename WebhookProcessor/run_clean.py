"""
Clean launcher for Futures Market API that avoids any Flask/other imports
"""
import os
import sys
import importlib.util
import subprocess

def run_clean_api():
    """
    Run the FastAPI server directly using subprocess to completely isolate
    it from any potential Flask imports or conflicts
    """
    # Get the full path to the clean_start.py file
    api_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clean_start.py")
    
    # Check if the file exists
    if not os.path.exists(api_file):
        print(f"Error: {api_file} not found")
        sys.exit(1)
    
    # Run the API using uvicorn directly
    print(f"Starting FastAPI server using {api_file}")
    command = ["uvicorn", "clean_start:app", "--host", "0.0.0.0", "--port", "8000"]
    
    # Execute the command
    try:
        subprocess.run(command)
    except Exception as e:
        print(f"Error running FastAPI server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_clean_api()