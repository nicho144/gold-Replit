"""
Futures Market Analysis API
This is the main file for the FastAPI application.
It provides futures market analysis with exhaustion signals detection.
"""
from datetime import datetime
from typing import Dict, List, Optional, Union, Any

import yfinance as yf
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Create a FastAPI app
app = FastAPI(
    title="Futures Market Analysis API",
    description="Advanced futures market analysis with exhaustion signals detection",
    version="1.0.0",
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

class MarketAnalysis(BaseModel):
    signal: str
    reasons: List[str]
    recommendations: List[str]
    prices: Dict[str, Union[float, str]]
    market_condition: Optional[str] = None
    term_structure: Optional[str] = None
    confidence_score: Optional[int] = None
    analysis_timestamp: Optional[str] = None

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

@app.get("/")
def read_root():
    """Root endpoint"""
    return {"message": "Futures Market Analysis API", "version": "1.0.0"}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": str(datetime.now())}

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
    front_price = get_price(input.ticker_front)
    next_price = get_price(input.ticker_next)
    
    # Check if we could retrieve the prices
    if front_price == "Error retrieving data" or next_price == "Error retrieving data":
        raise HTTPException(status_code=500, detail="Error retrieving market data")
    
    # Calculate term structure (contango or backwardation)
    term_structure = "contango" if isinstance(next_price, (int, float)) and \
                                    isinstance(front_price, (int, float)) and \
                                    next_price > front_price else "backwardation"
    
    # Detect potential exhaustion signals
    signal = "neutral"
    reasons = []
    recommendations = []
    
    # Price-based signals
    if input.price_breakout and term_structure == "backwardation" and input.physical_demand == "declining":
        signal = "potential_exhaustion_top"
        reasons.append("Price breakout with backwardation structure")
        reasons.append("Physical demand declining despite price rise")
        reasons.append("Term structure shows backwardation")
        recommendations.append("Consider reducing long exposure")
        recommendations.append("Watch for momentum divergence")
        recommendations.append("Set stops based on recent volatility")
        market_condition = "possible market top formation"
        confidence_score = 80
    elif not input.price_breakout and term_structure == "contango" and input.physical_demand == "rising":
        signal = "potential_exhaustion_bottom"
        reasons.append("Price holding support with contango structure")
        reasons.append("Physical demand rising despite price pressure")
        reasons.append("Term structure shows contango")
        recommendations.append("Watch for basing pattern")
        recommendations.append("Consider incremental long positions")
        recommendations.append("Monitor for shift in term structure")
        market_condition = "possible market bottom formation"
        confidence_score = 75
    else:
        signal = "neutral"
        reasons.append("Mixed market signals")
        reasons.append(f"Term structure shows {term_structure}")
        reasons.append(f"Physical demand is {input.physical_demand}")
        recommendations.append("Maintain current positioning")
        recommendations.append("Monitor for changes in physical demand")
        recommendations.append("Watch for term structure shifts")
        market_condition = "no clear exhaustion signal"
        confidence_score = 50
    
    return MarketAnalysis(
        signal=signal,
        reasons=reasons,
        recommendations=recommendations,
        prices={
            "front_month": front_price,
            "next_month": next_price,
            "difference": (next_price - front_price) if isinstance(next_price, (int, float)) and 
                            isinstance(front_price, (int, float)) else "N/A"
        },
        market_condition=market_condition,
        term_structure=term_structure,
        confidence_score=confidence_score,
        analysis_timestamp=str(datetime.now())
    )

@app.get("/api/premarket")
def premarket():
    """Get premarket data for major futures contracts"""
    # Key futures contracts to monitor
    futures_contracts = {
        "ES": "ES=F",      # S&P 500 E-mini
        "NQ": "NQ=F",      # Nasdaq 100 E-mini
        "YM": "YM=F",      # Dow Jones E-mini
        "RTY": "RTY=F",    # Russell 2000 E-mini
        "GC": "GC=F",      # Gold
        "SI": "SI=F",      # Silver
        "CL": "CL=F",      # Crude Oil
        "ZC": "ZC=F",      # Corn
        "ZW": "ZW=F",      # Wheat
        "ZS": "ZS=F"       # Soybeans
    }
    
    results = {}
    for name, ticker in futures_contracts.items():
        try:
            ticker_obj = yf.Ticker(ticker)
            data = ticker_obj.history(period="1d")
            
            if not data.empty:
                last_close = round(float(data['Close'].iloc[-1]), 2)
                prev_close = round(float(data['Close'].iloc[0]), 2) if len(data) > 1 else last_close
                change = round(last_close - prev_close, 2)
                percent_change = round((change / prev_close) * 100, 2) if prev_close != 0 else 0
                
                results[name] = {
                    "ticker": ticker,
                    "last_price": last_close,
                    "change": change,
                    "percent_change": percent_change,
                    "timestamp": str(datetime.now())
                }
            else:
                results[name] = {"ticker": ticker, "error": "No data available"}
        except Exception as e:
            results[name] = {"ticker": ticker, "error": str(e)}
    
    return {
        "premarket_data": results,
        "timestamp": str(datetime.now())
    }

@app.get("/api/gold-term-structure")
def gold_term_structure():
    """Analyze gold futures term structure (GC1, GC2, GC3)"""
    # Gold futures contracts
    gc_contracts = {
        "GC1": "GC=F",       # Front month
        "GC2": "GCJ24.CMX",  # Second month
        "GC3": "GCK24.CMX"   # Third month
    }
    
    # Fetch data for each contract
    prices = {}
    for name, ticker in gc_contracts.items():
        price = get_price(ticker)
        prices[name] = price
    
    # Calculate spreads if we have valid data
    spreads = {}
    term_structure = "Unknown"
    
    if all(isinstance(prices[key], (int, float)) for key in ["GC1", "GC2", "GC3"]):
        spreads["GC2-GC1"] = round(prices["GC2"] - prices["GC1"], 2)
        spreads["GC3-GC2"] = round(prices["GC3"] - prices["GC2"], 2)
        
        # Determine term structure
        if spreads["GC2-GC1"] > 0 and spreads["GC3-GC2"] > 0:
            term_structure = "Full Contango"
        elif spreads["GC2-GC1"] < 0 and spreads["GC3-GC2"] < 0:
            term_structure = "Full Backwardation"
        elif spreads["GC2-GC1"] > 0 > spreads["GC3-GC2"]:
            term_structure = "Mixed (Contango near-term, Backwardation far-term)"
        elif spreads["GC2-GC1"] < 0 < spreads["GC3-GC2"]:
            term_structure = "Mixed (Backwardation near-term, Contango far-term)"
        
        # Calculate contango/backwardation as percentage of spot
        if prices["GC1"] != 0:
            spreads["contango_percent"] = round((spreads["GC2-GC1"] / prices["GC1"]) * 100, 2)
        else:
            spreads["contango_percent"] = "N/A"
    
    return {
        "prices": prices,
        "spreads": spreads,
        "term_structure": term_structure,
        "analysis": {
            "interpretation": f"Gold futures currently show {term_structure} structure",
            "market_implications": get_term_structure_implications(term_structure)
        },
        "timestamp": str(datetime.now())
    }

def get_term_structure_implications(structure):
    """Return market implications based on term structure"""
    implications = {
        "Full Contango": [
            "Traditional futures curve indicating adequate physical supply",
            "Storage costs and interest rates influence the premium in deferred contracts",
            "Often seen in well-supplied or surplus markets"
        ],
        "Full Backwardation": [
            "Indicates potential supply constraints or shortages",
            "Market values immediate delivery more than future delivery",
            "Can signal bullish conditions or supply disruptions"
        ],
        "Mixed (Contango near-term, Backwardation far-term)": [
            "Near-term supply appears adequate",
            "Potential concerns about longer-term supply disruptions",
            "Complex structure that may indicate transitioning market conditions"
        ],
        "Mixed (Backwardation near-term, Contango far-term)": [
            "Current supply tightness or constraints",
            "Expectations that supply will normalize in the longer term",
            "Often seen during temporary supply disruptions"
        ],
        "Unknown": [
            "Unable to determine term structure from available data",
            "Consider checking data quality or market conditions"
        ]
    }
    
    return implications.get(structure, ["Term structure analysis unavailable"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)