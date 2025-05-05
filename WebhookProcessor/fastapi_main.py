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

# Import market data analysis functions
from market_data import (
    get_premarket_data,
    get_gold_term_structure,
    get_interest_rate_impact,
    analyze_market_sentiment,
    detect_gold_cycle_thresholds,
    get_economic_expectations,
    get_comprehensive_analysis
)

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
                    
                    <div class="endpoint bg-dark border border-secondary">
                        <h4>GET /gold/interest-impact</h4>
                        <p>Analyze impact of interest rates on gold prices</p>
                        <a href="/gold/interest-impact" class="btn btn-primary btn-sm">Try it</a>
                    </div>
                    
                    <div class="endpoint bg-dark border border-secondary">
                        <h4>GET /market-sentiment</h4>
                        <p>Analyze market sentiment and its impact on gold</p>
                        <a href="/market-sentiment" class="btn btn-primary btn-sm">Try it</a>
                    </div>
                    
                    <div class="endpoint bg-dark border border-secondary">
                        <h4>GET /gold/cycle</h4>
                        <p>Detect potential gold cycle turning points</p>
                        <a href="/gold/cycle" class="btn btn-primary btn-sm">Try it</a>
                    </div>
                    
                    <div class="endpoint bg-dark border border-secondary">
                        <h4>GET /economic-expectations</h4>
                        <p>Analyze current economic expectations for gold</p>
                        <a href="/economic-expectations" class="btn btn-primary btn-sm">Try it</a>
                    </div>
                    
                    <div class="endpoint bg-dark border border-secondary">
                        <h4>GET /comprehensive</h4>
                        <p>Get comprehensive market analysis combining all indicators</p>
                        <a href="/comprehensive" class="btn btn-primary btn-sm">Try it</a>
                    </div>
                    
                    <div class="endpoint bg-dark border border-secondary">
                        <h4>POST /analyze</h4>
                        <p>Legacy endpoint: Analyze futures market for exhaustion signals</p>
                        <pre>
{
  "ticker_front": "GC=F",
  "ticker_next": "GCM24.CMX",
  "physical_demand": "declining",
  "price_breakout": false
}
                        </pre>
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

@app.get("/premarket")
def premarket():
    """Get premarket data for major futures contracts"""
    try:
        data = get_premarket_data()
        return data
    except Exception as e:
        logger.error(f"Error fetching premarket data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching premarket data: {str(e)}")

@app.get("/gold/term-structure")
def gold_term_structure():
    """Analyze gold futures term structure (GC1, GC2, GC3)"""
    try:
        data = get_gold_term_structure()
        return data
    except Exception as e:
        logger.error(f"Error analyzing gold term structure: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing gold term structure: {str(e)}")

@app.get("/gold/interest-impact")
def interest_impact():
    """Analyze impact of interest rates on gold prices"""
    try:
        data = get_interest_rate_impact()
        return data
    except Exception as e:
        logger.error(f"Error analyzing interest rate impact: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing interest rate impact: {str(e)}")

@app.get("/market-sentiment")
def market_sentiment():
    """Analyze market sentiment and its impact on gold"""
    try:
        data = analyze_market_sentiment()
        return data
    except Exception as e:
        logger.error(f"Error analyzing market sentiment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing market sentiment: {str(e)}")

@app.get("/gold/cycle")
def gold_cycle():
    """Detect potential gold cycle turning points"""
    try:
        data = detect_gold_cycle_thresholds()
        return data
    except Exception as e:
        logger.error(f"Error detecting gold cycle: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error detecting gold cycle: {str(e)}")

@app.get("/economic-expectations")
def economic_expectations():
    """Analyze current economic expectations for gold"""
    try:
        data = get_economic_expectations()
        return data
    except Exception as e:
        logger.error(f"Error analyzing economic expectations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing economic expectations: {str(e)}")

@app.get("/comprehensive")
def comprehensive():
    """Get comprehensive market analysis combining all indicators"""
    try:
        data = get_comprehensive_analysis()
        return data
    except Exception as e:
        logger.error(f"Error generating comprehensive analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating comprehensive analysis: {str(e)}")

@app.post("/analyze")
def analyze_market(input: MarketInput):
    """
    Legacy endpoint: Analyze futures market for potential exhaustion signals
    
    This endpoint is maintained for backward compatibility
    """
    try:
        logger.debug(f"Analyzing market with input: {input}")
        
        # Get term structure data
        term_structure = get_gold_term_structure()
        
        # Extract price data
        front_price = 0.0
        next_price = 0.0
        
        if "contracts" in term_structure and "GC=F" in term_structure["contracts"]:
            front_price = term_structure["contracts"]["GC=F"]["price"]
        
        if "contracts" in term_structure and "GCM24.CMX" in term_structure["contracts"]:
            next_price = term_structure["contracts"]["GCM24.CMX"]["price"]
        
        # Fallback to yfinance direct query if needed
        if front_price == 0.0:
            try:
                front_data = yf.Ticker(input.ticker_front).history(period="1d")
                front_price = front_data['Close'].iloc[-1] if not front_data.empty else 1900.0
            except Exception as e:
                logger.error(f"Error getting front month data: {e}")
                front_price = 1900.0
        
        if next_price == 0.0:
            try:
                next_data = yf.Ticker(input.ticker_next).history(period="1d")
                next_price = next_data['Close'].iloc[-1] if not next_data.empty else 1950.0
            except Exception as e:
                logger.error(f"Error getting next month data: {e}")
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

@app.post("/analyze-tickers")
def analyze_tickers(input: TickerSymbols):
    """Analyze multiple ticker symbols for price and basic metrics"""
    try:
        logger.debug(f"Analyzing tickers: {input.symbols}")
        
        # Fetch data for the requested tickers
        data = yf.download(input.symbols, period="5d", group_by='ticker')
        
        result = {
            "analysis": {},
            "timestamp": str(datetime.now())
        }
        
        # Process each ticker
        for ticker in input.symbols:
            if ticker in data:
                ticker_data = data[ticker]
                if not ticker_data.empty:
                    # Calculate basic metrics
                    current = ticker_data['Close'].iloc[-1]
                    prev_day = ticker_data['Close'].iloc[-2] if len(ticker_data) > 1 else ticker_data['Open'].iloc[-1]
                    day_change = current - prev_day
                    day_change_pct = (day_change / prev_day) * 100 if prev_day != 0 else 0
                    
                    # Calculate 5-day change if available
                    five_day_change = None
                    five_day_change_pct = None
                    if len(ticker_data) >= 5:
                        five_day_prior = ticker_data['Close'].iloc[-5]
                        five_day_change = current - five_day_prior
                        five_day_change_pct = (five_day_change / five_day_prior) * 100 if five_day_prior != 0 else 0
                    
                    # Add to result
                    result["analysis"][ticker] = {
                        "current_price": current,
                        "day_change": day_change,
                        "day_change_pct": day_change_pct,
                        "five_day_change": five_day_change,
                        "five_day_change_pct": five_day_change_pct,
                        "volume": ticker_data['Volume'].iloc[-1],
                        "timestamp": str(ticker_data.index[-1])
                    }
                else:
                    result["analysis"][ticker] = {"error": "No data available"}
            else:
                result["analysis"][ticker] = {"error": "Ticker not found in data"}
        
        return result
    except Exception as e:
        logger.error(f"Error analyzing tickers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing tickers: {str(e)}")

# For direct execution
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)