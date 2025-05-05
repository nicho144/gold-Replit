from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import uvicorn
from models import MarketInput, MarketAnalysis
from utils import analyze_futures_market
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Futures Market Analysis API",
    description="API for detecting potential market exhaustion signals based on term structure and market conditions",
    version="1.0.0",
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Render the main frontend interface"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/docs-custom", response_class=HTMLResponse)
async def custom_docs(request: Request):
    """Render custom documentation page"""
    return templates.TemplateResponse("documentation.html", {"request": request})

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

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    # Run the FastAPI app directly
    uvicorn.run(app, host="0.0.0.0", port=8000)