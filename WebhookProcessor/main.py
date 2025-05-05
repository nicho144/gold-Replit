from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from datetime import datetime
import logging
from gold_futures_curve import get_enhanced_gold_futures_curve

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Gold Market Analysis")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def root(request: Request):
    """Comprehensive gold market analysis with term structure, yields, and market cycle indicators"""
    try:
        # Get enhanced gold futures curve data with all analysis modules
        curve_data = get_enhanced_gold_futures_curve()

        # Ensure we have a timestamp
        if 'timestamp' not in curve_data:
            curve_data['timestamp'] = str(datetime.now())

        return templates.TemplateResponse("gold_futures_curve.html", {
            "request": request,
            "data": curve_data
        })
    except Exception as e:
        logger.error(f"Error in gold market analysis: {str(e)}")
        return templates.TemplateResponse("gold_futures_curve.html", {
            "request": request,
            "data": {"error": str(e), "timestamp": str(datetime.now())}
        })

@app.get("/health")
async def health_check():
    return {"status": "healthy"}