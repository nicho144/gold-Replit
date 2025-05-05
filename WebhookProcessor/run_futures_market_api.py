"""
Run the clean FastAPI server
This is a minimal launcher that avoids any Flask imports or conflicts
"""
import subprocess
import sys

print("Starting clean FastAPI server...")

try:
    # Use uvicorn directly to run the clean_start.py file
    result = subprocess.run(
        ["uvicorn", "clean_start:app", "--host", "0.0.0.0", "--port", "8000"],
        check=True
    )
    sys.exit(result.returncode)
except subprocess.CalledProcessError as e:
    print(f"Error running FastAPI server: {e}")
    sys.exit(e.returncode)
except Exception as e:
    print(f"Unexpected error: {e}")
    sys.exit(1)