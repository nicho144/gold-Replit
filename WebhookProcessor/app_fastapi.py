"""
Dedicated FastAPI application for the Futures Market Analysis API
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional, Union
import uvicorn
import logging
from models import MarketInput, MarketAnalysis
from utils import analyze_futures_market

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Futures Market Analysis API",
    description="API for detecting potential market exhaustion signals based on term structure and market conditions",
    version="1.0.0"
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/analyze", response_model=MarketAnalysis)
async def analyze_market(input: MarketInput):
    """
    Analyze futures market for potential exhaustion signals
    
    Parameters:
    - ticker_front: Ticker symbol for front month contract (e.g., "GC=F" for Gold Front Month)
    - ticker_next: Ticker symbol for next month contract (e.g., "GCM24.CMX")
    - physical_demand: Current physical demand trend ("declining", "stable", "rising")
    - price_breakout: Boolean indicating if price has broken resistance
    
    Returns:
    - Market analysis with signal, reasons, recommendations, and price data
    """
    try:
        logger.debug(f"Received analysis request for tickers: {input.ticker_front} and {input.ticker_next}")
        result = analyze_futures_market(input)
        return result
    except Exception as e:
        logger.error(f"Error analyzing market: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing market data: {str(e)}")

# Only run the server when this file is executed directly
if __name__ == "__main__":
    uvicorn.run("app_fastapi:app", host="0.0.0.0", port=8000)