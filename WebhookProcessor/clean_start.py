"""
Clean start implementation of Futures Market API
This file has NO imports from any other local modules to avoid conflicts
"""
from datetime import datetime
from typing import Dict, List, Optional, Union, Any

import yfinance as yf
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

# Create a completely separate FastAPI instance with a different name
app = FastAPI(
    title="Futures Market Analysis API",
    description="Advanced futures market analysis with exhaustion signals detection",
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

def get_price(ticker):
    """Attempts to retrieve the market price for a given ticker, with a fallback."""
    try:
        data = yf.Ticker(ticker).history(period="1d")
        if not data.empty:
            price = data['Close'].iloc[-1]
            return round(float(price), 2)
        else:
            return "Data unavailable"
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return "Error retrieving data"

@app.get("/", response_class=HTMLResponse)
async def read_root():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Futures Market Analysis API</title>
        <link rel="stylesheet" href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css">
        <style>
            body { padding: 20px; }
            .endpoint { margin-bottom: 15px; padding: 15px; border-radius: 5px; }
            pre { background-color: #333; padding: 10px; border-radius: 5px; }
        </style>
    </head>
    <body class="bg-dark text-light">
        <div class="container">
            <h1 class="my-4">Futures Market Analysis API</h1>
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
                        <h4>GET /api/premarket</h4>
                        <p>Get premarket data for major futures contracts (ES, GC, TNX, VIX)</p>
                        <a href="/api/premarket" class="btn btn-primary btn-sm">Try it</a>
                    </div>
                    
                    <div class="endpoint bg-dark border border-secondary">
                        <h4>GET /api/gold-term-structure</h4>
                        <p>Analyze gold futures term structure (GC1, GC2, GC3)</p>
                        <a href="/api/gold-term-structure" class="btn btn-primary btn-sm">Try it</a>
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

@app.get("/api/premarket")
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
                        "last_price": float(last_price),
                        "change": float(change),
                        "change_pct": float(change_pct),
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
        print(f"Error fetching premarket data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching premarket data: {str(e)}")

@app.get("/api/gold-term-structure")
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
                    prices[ticker] = float(ticker_data['Close'].iloc[-1])
                    result["contracts"][ticker] = {
                        "price": float(ticker_data['Close'].iloc[-1]),
                        "volume": float(ticker_data['Volume'].iloc[-1]),
                        "timestamp": str(ticker_data.index[-1])
                    }
        
        # Calculate term structure metrics
        if GOLD_FUTURES in prices and GOLD_FUTURES_2 in prices:
            # Calculate contango (positive) or backwardation (negative)
            front_next_spread = prices[GOLD_FUTURES_2] - prices[GOLD_FUTURES]
            front_next_pct = (front_next_spread / prices[GOLD_FUTURES]) * 100
            
            result["term_structure"]["front_next_spread"] = float(front_next_spread)
            result["term_structure"]["front_next_percentage"] = float(front_next_pct)
            result["term_structure"]["structure"] = "contango" if front_next_spread > 0 else "backwardation"
            
            # Add analysis
            if front_next_spread > 0:
                result["analysis"]["interpretation"] = "Gold futures are in contango, indicating market expectations of higher future prices."
                result["analysis"]["implications"] = [
                    "Physical supply is likely adequate",
                    "Storage costs and interest rates are influencing the premium in deferred contracts",
                    "Common in well-supplied markets or when interest rates are higher"
                ]
            else:
                result["analysis"]["interpretation"] = "Gold futures are in backwardation, indicating potential near-term supply constraints."
                result["analysis"]["implications"] = [
                    "Current physical demand may be strong",
                    "Potential near-term supply constraints or shortages",
                    "Market values immediate delivery more than future delivery"
                ]
        
        return result
    except Exception as e:
        print(f"Error analyzing gold term structure: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing gold term structure: {str(e)}")

@app.post("/api/analyze")
def analyze_market(input: MarketInput):
    """
    Analyze futures market for potential exhaustion signals
    """
    try:
        # Fetch data for the tickers
        front_data = yf.Ticker(input.ticker_front).history(period="1d")
        next_data = yf.Ticker(input.ticker_next).history(period="1d")
        
        if front_data.empty or next_data.empty:
            raise HTTPException(status_code=400, detail="Unable to retrieve market data for the provided tickers")
        
        front_price = float(front_data['Close'].iloc[-1])
        next_price = float(next_data['Close'].iloc[-1])
        
        # Calculate contango metrics
        contango_spread = next_price - front_price
        contango_percentage = (contango_spread / front_price) * 100 if front_price != 0 else 0
        term_structure = "contango" if contango_spread > 0 else "backwardation"
        
        # Analysis logic
        signal = "neutral"
        reasons = []
        recommendations = []
        market_condition = ""
        confidence_score = 50
        
        # Logic for detecting market exhaustion signals
        if input.price_breakout and term_structure == "backwardation" and input.physical_demand == "declining":
            # Potential top formation
            signal = "potential_exhaustion_top"
            reasons = [
                "Price breakout with backwardation structure",
                "Physical demand declining despite price rise",
                f"Term structure shows {term_structure}"
            ]
            recommendations = [
                "Consider reducing long exposure",
                "Watch for momentum divergence",
                "Set stops based on recent volatility"
            ]
            market_condition = "possible market top formation"
            confidence_score = 80
        elif not input.price_breakout and term_structure == "contango" and input.physical_demand == "rising":
            # Potential bottom formation
            signal = "potential_exhaustion_bottom"
            reasons = [
                "Price holding support with contango structure",
                "Physical demand rising despite price pressure",
                f"Term structure shows {term_structure}"
            ]
            recommendations = [
                "Watch for basing pattern",
                "Consider incremental long positions",
                "Monitor for shift in term structure"
            ]
            market_condition = "possible market bottom formation"
            confidence_score = 75
        else:
            # No clear signal
            signal = "neutral"
            reasons = [
                f"Mixed market signals",
                f"Term structure shows {term_structure}",
                f"Physical demand is {input.physical_demand}"
            ]
            recommendations = [
                "Maintain current positioning",
                "Monitor for changes in physical demand",
                "Watch for term structure shifts"
            ]
            market_condition = "no clear exhaustion signal"
            confidence_score = 50
        
        # Return analysis
        return {
            "signal": signal,
            "reasons": reasons,
            "recommendations": recommendations,
            "prices": {
                "front_month": front_price,
                "next_month": next_price,
                "difference": contango_spread,
                "term_structure_percentage": contango_percentage
            },
            "market_condition": market_condition,
            "term_structure": term_structure,
            "confidence_score": confidence_score,
            "analysis_timestamp": str(datetime.now())
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in analyze_market: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Only run the server if this file is executed directly
if __name__ == "__main__":
    import uvicorn
    print("Starting FastAPI server on port 8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)