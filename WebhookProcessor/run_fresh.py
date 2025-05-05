import uvicorn
from fresh_api import app

if __name__ == "__main__":
    # Run the FastAPI app on port 8001 to avoid conflicts
    uvicorn.run(app, host="0.0.0.0", port=8001)