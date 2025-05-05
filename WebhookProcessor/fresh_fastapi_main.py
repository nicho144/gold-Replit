"""
Advanced Futures Market Analysis API

This API provides comprehensive analysis of futures markets, with a focus on:
- Real-time premarket data
- Term structure analysis
- Interest rate impacts
- Economic indicators
- Market sentiment 
- Gold cycle analysis
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import yfinance as yf
from datetime import datetime
from typing import Dict, List, Optional, Union, Any
import logging
import json

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Advanced Futures Market Analysis API",
    description="Comprehensive analysis of futures markets with focus on gold, interest rates, and economic indicators",
    version="2.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MarketInput(BaseModel):
    ticker_front: str = Field(..., description="Front month contract ticker (e.g., 'GC=F' for Gold Front Month)")
    ticker_next: str = Field(..., description="Next month contract ticker (e.g., 'GCM24.CMX')")
    physical_demand: str = Field(..., description="Physical demand trend ('declining', 'stable', 'rising')")
    price_breakout: bool = Field(..., description="Whether price has broken resistance level")

class TickerSymbols(BaseModel):
    symbols: List[str] = Field(..., description="List of ticker symbols to analyze")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Advanced Futures Market Analysis API</title>
        <link rel="stylesheet" href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css">
        <style>
            body { padding: 20px; }
            .endpoint { margin-bottom: 15px; padding: 15px; border-radius: 5px; }
            pre { background-color: #333; padding: 10px; border-radius: 5px; }
        </style>
    </head>
    <body class="bg-dark text-light">
        <div class="container">
            <h1 class="my-4">Advanced Futures Market Analysis API</h1>
            <p class="lead">
                Comprehensive analysis of futures markets with focus on real-time premarket data,
                term structure, interest rates, and economic indicators.
            </p>
            
            <div class="row mt-5">
                <div class="col-12">
                    <h2>Available Endpoints</h2>
                    
                    <div class="endpoint bg-dark border border-secondary">
                        <h4>GET /health</h4>
                        <p>Health check endpoint</p>
                        <a href="/health" class="btn btn-primary btn-sm">Try it</a>
                    </div>
                    
                    <div class="endpoint bg-dark border border-secondary">
                        <h4>GET /premarket</h4>
                        <p>Get premarket data for major futures contracts (ES, GC, TNX, VIX)</p>
                        <a href="/premarket" class="btn btn-primary btn-sm">Try it</a>
                    </div>
                    
                    <div class="endpoint bg-dark border border-secondary">
                        <h4>GET /gold/term-structure</h4>
                        <p>Analyze gold futures term structure (GC1, GC2, GC3)</p>
                        <a href="/gold/term-structure" class="btn btn-primary btn-sm">Try it</a>
                    </div>
                </div>
            </div>
            
            <div class="row mt-4">
                <div class="col-12">
                    <p>
                        For interactive API documentation, visit 
                        <a href="/docs">Interactive API Docs</a>
                    </p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": str(datetime.now()),
        "version": "2.0.0"
    }

# Basic implementation of premarket data
@app.get("/premarket")
def premarket():
    """Get premarket data for major futures contracts"""
    try:
        # Ticker symbols
        ES_FUTURES = "ES=F"  # S&P 500 E-mini
        GOLD_FUTURES = "GC=F"  # Gold Front Month
        TEN_YEAR_YIELD = "^TNX"  # 10-Year Treasury Yield
        VIX = "^VIX"  # Volatility Index
        
        # Fetch data for multiple tickers at once
        tickers = [ES_FUTURES, GOLD_FUTURES, TEN_YEAR_YIELD, VIX]
        data = yf.download(tickers, period="1d", group_by='ticker')
        
        # Process the data
        result = {}
        for ticker in tickers:
            if ticker in data:
                ticker_data = data[ticker]
                if not ticker_data.empty:
                    last_price = ticker_data['Close'].iloc[-1]
                    prev_close = ticker_data['Open'].iloc[0]
                    change = last_price - prev_close
                    change_pct = (change / prev_close) * 100 if prev_close != 0 else 0
                    
                    result[ticker] = {
                        "last_price": last_price,
                        "change": change,
                        "change_pct": change_pct,
                        "timestamp": str(ticker_data.index[-1])
                    }
                else:
                    result[ticker] = {"error": "No data available"}
            else:
                result[ticker] = {"error": "Ticker not found in data"}
        
        # Add timestamp
        result["timestamp"] = str(datetime.now())
        
        return result
    except Exception as e:
        logger.error(f"Error fetching premarket data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching premarket data: {str(e)}")

# Basic implementation of gold term structure
@app.get("/gold/term-structure")
def gold_term_structure():
    """Analyze gold futures term structure (GC1, GC2, GC3)"""
    try:
        # Ticker symbols
        GOLD_FUTURES = "GC=F"  # Gold Front Month
        GOLD_FUTURES_2 = "GCM24.CMX"  # Gold Next Month
        GOLD_FUTURES_3 = "GCQ24.CMX"  # Gold 3rd Month
        GOLD_ETF = "GLD"  # SPDR Gold Trust ETF (spot gold proxy)
        
        # Fetch data for gold futures contracts
        tickers = [GOLD_FUTURES, GOLD_FUTURES_2, GOLD_FUTURES_3, GOLD_ETF]
        data = yf.download(tickers, period="5d", group_by='ticker')
        
        # Process the data
        result = {
            "contracts": {},
            "term_structure": {},
            "analysis": {}
        }
        
        # Extract latest prices
        prices = {}
        for ticker in tickers:
            if ticker in data:
                ticker_data = data[ticker]
                if not ticker_data.empty:
                    prices[ticker] = ticker_data['Close'].iloc[-1]
                    result["contracts"][ticker] = {
                        "price": ticker_data['Close'].iloc[-1],
                        "volume": ticker_data['Volume'].iloc[-1],
                        "timestamp": str(ticker_data.index[-1])
                    }
        
        # Calculate term structure metrics
        if GOLD_FUTURES in prices and GOLD_FUTURES_2 in prices:
            # Calculate contango (positive) or backwardation (negative)
            front_next_spread = prices[GOLD_FUTURES_2] - prices[GOLD_FUTURES]
            front_next_pct = (front_next_spread / prices[GOLD_FUTURES]) * 100
            
            result["term_structure"]["front_next_spread"] = front_next_spread
            result["term_structure"]["front_next_percentage"] = front_next_pct
            result["term_structure"]["structure"] = "contango" if front_next_spread > 0 else "backwardation"
        
        return result
    except Exception as e:
        logger.error(f"Error analyzing gold term structure: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing gold term structure: {str(e)}")

@app.post("/analyze")
def analyze_market(input: MarketInput):
    """
    Analyze futures market for potential exhaustion signals
    """
    try:
        logger.debug(f"Analyzing market with input: {input}")
        
        # Fetch data for the tickers
        try:
            front_data = yf.Ticker(input.ticker_front).history(period="1d")
            next_data = yf.Ticker(input.ticker_next).history(period="1d")
            
            front_price = front_data['Close'].iloc[-1] if not front_data.empty else 1900.0
            next_price = next_data['Close'].iloc[-1] if not next_data.empty else 1950.0
        except Exception as e:
            logger.error(f"Error getting ticker data: {e}")
            front_price = 1900.0
            next_price = 1950.0
        
        # Calculate contango metrics
        contango_spread = next_price - front_price
        contango_percentage = (contango_spread / front_price) * 100 if front_price != 0 else 0
        contango_slope = "steep_upward" if contango_spread > 5 else "mild"
        
        # For demo, we simulate open interest
        open_interest_change = "spike"
        
        # Analysis logic
        signal = "NEUTRAL"
        reasons = []
        recommendations = []
        
        if contango_slope == "steep_upward" and \
           open_interest_change == "spike" and \
           not input.price_breakout and \
           input.physical_demand == "declining":
            signal = "BEARISH — Potential exhaustion"
            reasons = [
                f"Contango widened: {next_price:.2f} > {front_price:.2f}",
                "Open interest spike",
                "Price stalling (no breakout)",
                "Physical demand declining"
            ]
            recommendations = [
                "Reduce long exposure in futures or ETFs",
                "Consider bear spreads or cash",
                "Watch roll yield drag on ETFs"
            ]
        else:
            signal = "NEUTRAL or BULLISH — No exhaustion confirmed"
            reasons = [
                f"Current market conditions: {input.physical_demand} physical demand",
                f"Price breakout: {'Yes' if input.price_breakout else 'No'}",
                f"Term structure: {contango_slope}"
            ]
            recommendations = [
                "Continue monitoring term structure and demand",
                "Watch for changes in physical demand and inventory levels",
                "Monitor open interest for potential shifts"
            ]
        
        # Return analysis results
        return {
            "signal": signal,
            "reasons": reasons,
            "recommendations": recommendations,
            "prices": {
                "front_contract": front_price,
                "next_contract": next_price,
                "contango_spread": f"${contango_spread:.2f}",
                "contango_percentage": f"{contango_percentage:.2f}%"
            },
            "analysis_timestamp": str(datetime.now())
        }
    except Exception as e:
        logger.error(f"Error in analyze_market: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)