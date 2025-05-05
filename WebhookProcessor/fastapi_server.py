from fastapi import FastAPI, HTTPException
from models import MarketInput, MarketAnalysis
from utils import analyze_futures_market
import uvicorn
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create a new FastAPI app
app = FastAPI(title="Futures Market Analysis API")

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/analyze", response_model=MarketAnalysis)
def analyze_market(input: MarketInput):
    """Analyze futures market for potential exhaustion signals"""
    try:
        logger.debug(f"Received analysis request for tickers: {input.ticker_front} and {input.ticker_next}")
        result = analyze_futures_market(input)
        return result
    except Exception as e:
        logger.error(f"Error analyzing market: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing market data: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)