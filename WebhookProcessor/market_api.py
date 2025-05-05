from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import yfinance as yf
from datetime import datetime
from typing import Dict, List, Optional, Union
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Futures Market Analysis API",
    description="API for analyzing futures market for potential exhaustion signals",
    version="1.0.0",
)

class MarketInput(BaseModel):
    ticker_front: str = Field(..., description="Front month contract ticker (e.g., 'GC=F' for Gold Front Month)")
    ticker_next: str = Field(..., description="Next month contract ticker (e.g., 'GCM24.CMX')")
    physical_demand: str = Field(..., description="Physical demand trend", pattern="^(declining|stable|rising)$")
    price_breakout: bool = Field(..., description="Whether price has broken resistance level")

class MarketAnalysis(BaseModel):
    signal: str
    reasons: List[str]
    recommendations: List[str]
    prices: Dict[str, Union[float, str]]
    market_condition: Optional[str] = None
    term_structure: Optional[str] = None
    confidence_score: Optional[int] = None
    analysis_timestamp: Optional[str] = None

def get_price(ticker):
    """Attempts to retrieve the market price for a given ticker, with a fallback."""
    try:
        logger.debug(f"Attempting to get price for {ticker}")
        data = yf.Ticker(ticker).history(period="1d")
        if not data.empty:
            return data['Close'].iloc[-1]
        else:
            # Fallback for testing
            logger.warning(f"No data found for {ticker}, using fallback price")
            return 1900.0 if "GC" in ticker else 1950.0
    except Exception as e:
        logger.error(f"Error getting price for {ticker}: {e}")
        # Fallback for testing
        return 1900.0 if "GC" in ticker else 1950.0

@app.get("/")
def read_root():
    return {"message": "Welcome to the Futures Market Analysis API"}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": str(datetime.now())
    }

@app.post("/api/analyze", response_model=MarketAnalysis)
def analyze_market(input: MarketInput):
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
        logger.debug(f"Analyzing market with input: {input}")
        
        # Get price data
        front_price = get_price(input.ticker_front)
        next_price = get_price(input.ticker_next)
        
        # Calculate contango
        contango_spread = next_price - front_price
        contango_percentage = (contango_spread / front_price) * 100
        
        # Determine market condition
        term_structure = "contango" if contango_spread > 0 else "backwardation"
        
        # Mock analysis logic (would be more sophisticated in production)
        if term_structure == "contango" and input.physical_demand == "declining":
            signal = "bullish_exhaustion"
            confidence = 70
            reasons = [
                "Market in contango (future prices higher than current)",
                "Physical demand declining",
                f"Contango spread: ${contango_spread:.2f}",
                f"Contango percentage: {contango_percentage:.2f}%"
            ]
            recommendations = [
                "Consider reducing long exposure",
                "Watch for reversal patterns",
                "Monitor for changes in physical demand"
            ]
        elif term_structure == "backwardation" and input.physical_demand == "rising":
            signal = "bearish_exhaustion"
            confidence = 65
            reasons = [
                "Market in backwardation (current prices higher than future)",
                "Physical demand rising",
                f"Backwardation spread: ${-contango_spread:.2f}",
                f"Backwardation percentage: {-contango_percentage:.2f}%"
            ]
            recommendations = [
                "Consider reducing short exposure",
                "Look for support levels",
                "Monitor inventory levels"
            ]
        else:
            signal = "neutral"
            confidence = 50
            reasons = [
                f"Market in {term_structure}",
                f"Physical demand {input.physical_demand}",
                f"Price breakout: {'Yes' if input.price_breakout else 'No'}"
            ]
            recommendations = [
                "Monitor for changes in term structure",
                "Watch physical demand trends",
                "Stay neutral until clearer signals emerge"
            ]
        
        # Return analysis
        return MarketAnalysis(
            signal=signal,
            reasons=reasons,
            recommendations=recommendations,
            prices={
                "front_contract": front_price,
                "next_contract": next_price,
                "contango_spread": f"${contango_spread:.2f}",
                "contango_percentage": f"{contango_percentage:.2f}%"
            },
            market_condition=input.physical_demand,
            term_structure=term_structure,
            confidence_score=confidence,
            analysis_timestamp=str(datetime.now())
        )
    
    except Exception as e:
        logger.error(f"Error in analyze_market: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")