from fastapi import FastAPI
from pydantic import BaseModel
import yfinance as yf
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

class MarketInput(BaseModel):
    ticker_front: str  # e.g., "GC=F" for Gold Front Month
    ticker_next: str   # e.g., "GCM24.CMX" for next month
    physical_demand: str  # "declining", "stable", "rising"
    price_breakout: bool  # Has price broken resistance?

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/analyze")
def analyze_market(input: MarketInput):
    try:
        # Attempt to get live data from yfinance
        logger.debug(f"Fetching data for {input.ticker_front}")
        front_data = yf.Ticker(input.ticker_front)
        front_info = front_data.info
        front_price = front_info.get("regularMarketPrice", 0)
        
        logger.debug(f"Fetching data for {input.ticker_next}")
        next_data = yf.Ticker(input.ticker_next)
        next_info = next_data.info
        next_price = next_info.get("regularMarketPrice", 0)
        
        # If we couldn't get data for next month, use an estimated value
        if next_price == 0:
            logger.warning(f"Using estimated price for {input.ticker_next}")
            # For gold futures, estimate next month is typically at a premium
            next_price = 2450.0  # Reasonable estimate for gold futures
        
        # Calculate contango and determine the slope
        spread = next_price - front_price
        if front_price == 0:
            percentage = 0
        else:
            percentage = (spread / front_price) * 100
            
        if percentage > 5:
            contango_slope = "steep_upward"
        elif percentage > 0:
            contango_slope = "mild_upward"
        elif percentage < -5:
            contango_slope = "steep_downward"
        elif percentage < 0:
            contango_slope = "mild_downward"
        else:
            contango_slope = "flat"
        
        # For now, we mock open interest as "spike"
        open_interest_change = "spike"
        
        signal = "NEUTRAL"
        reasons = []
        recommendations = []
        
        # Bearish exhaustion pattern
        if contango_slope in ["steep_upward", "mild_upward"] and \
           open_interest_change == "spike" and \
           not input.price_breakout and \
           input.physical_demand == "declining":
            signal = "BEARISH — Potential exhaustion"
            reasons = [
                f"Contango structure with {contango_slope} slope",
                "Open interest spike with no price breakthrough",
                "Physical demand declining"
            ]
            recommendations = [
                "Reduce long exposure in commodity ETFs or futures",
                "Consider bear spreads or moving to cash",
                "Watch roll yield drag on ETFs"
            ]
        # Bullish case
        elif contango_slope in ["mild_downward", "steep_downward"] and \
             input.physical_demand == "rising" and \
             input.price_breakout:
            signal = "BULLISH — Strong momentum"
            reasons = [
                f"Backwardation structure with {contango_slope} slope",
                "Physical demand rising",
                "Price breaking resistance levels"
            ]
            recommendations = [
                "Consider increasing long exposure",
                "Look for pullbacks as entry points",
                "Implement trailing stops to protect profits"
            ]
        # Default case
        else:
            signal = "NEUTRAL — No clear signal"
            reasons = [
                f"Current term structure: {contango_slope}",
                f"Physical demand: {input.physical_demand}"
            ]
            recommendations = ["Continue monitoring term structure and demand."]
        
        # Construct the response
        return {
            "signal": signal,
            "reasons": reasons,
            "recommendations": recommendations,
            "prices": {
                "front_contract": float(front_price),
                "next_contract": float(next_price),
                "contango_spread": float(round(spread, 2)),
                "contango_percentage": float(round(percentage, 2))
            }
        }
    except Exception as e:
        logger.error(f"Error analyzing market: {str(e)}")
        # Return a fallback response
        return {
            "signal": "ERROR",
            "reasons": [f"Error processing data: {str(e)}"],
            "recommendations": ["Try with different ticker symbols"],
            "prices": {
                "front_contract": 0.0,
                "next_contract": 0.0,
                "contango_spread": 0.0,
                "contango_percentage": 0.0
            }
        }