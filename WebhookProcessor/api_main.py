from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yfinance as yf
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Futures Market Analysis API",
    description="API for detecting potential market exhaustion signals based on term structure and market conditions",
    version="1.0.0"
)

# Define the input model for receiving market data inputs
class MarketInput(BaseModel):
    ticker_front: str  # e.g., "GC=F" for Gold Front Month
    ticker_next: str   # e.g., "GCM24.CMX" for next month
    physical_demand: str  # "declining", "stable", "rising"
    price_breakout: bool  # Has price broken resistance?

# Fallback function for getting price data
def get_price(ticker):
    """Attempts to retrieve the market price for a given ticker, with a fallback."""
    try:
        # Fetch data from Yahoo Finance
        data = yf.Ticker(ticker).info
        price = data.get("regularMarketPrice", None)
        if price is None:
            raise ValueError(f"Price data for ticker {ticker} is unavailable.")
        return price
    except Exception as e:
        # If data fetching fails, log the error and return a default price
        logger.error(f"Error retrieving {ticker}: {str(e)}. Using fallback price.")
        return 1000  # Default fallback price (e.g., $1000 for Gold)

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/analyze")
def analyze_market(input: MarketInput):
    try:
        # Fetch market data for front and next contracts using fallback mechanism
        front_price = get_price(input.ticker_front)
        next_price = get_price(input.ticker_next)

        # Analyze the price difference (Contango Slope)
        price_diff = next_price - front_price
        percentage = (price_diff / front_price) * 100 if front_price > 0 else 0
        
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

        # For simplicity, mock the open interest change as "spike"
        open_interest_change = "spike"

        # Signal analysis based on the conditions
        signal = "NEUTRAL — No clear signal"
        reasons = []
        recommendations = []

        # Applying conditions to determine the market signal
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
            reasons = [
                f"Current term structure: {contango_slope}",
                f"Physical demand: {input.physical_demand}"
            ]
            recommendations = ["Continue monitoring term structure and demand."]

        return {
            "signal": signal,
            "reasons": reasons,
            "recommendations": recommendations,
            "prices": {
                "front_contract": float(front_price),
                "next_contract": float(next_price),
                "contango_spread": float(round(price_diff, 2)),
                "contango_percentage": float(round(percentage, 2))
            },
            "market_condition": "Uncertain",
            "term_structure": contango_slope,
            "confidence_score": 40,
            "analysis_timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        # If any issue occurs, raise an HTTP error with details
        logger.error(f"Error analyzing market: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))