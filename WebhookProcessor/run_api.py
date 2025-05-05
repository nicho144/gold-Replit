import uvicorn

if __name__ == "__main__":
    # Run the FastAPI app at port 8000
    uvicorn.run("api_main:app", host="0.0.0.0", port=8000, reload=True)