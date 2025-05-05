# Futures Market Analysis API

A dual-implementation API for analyzing futures markets to detect potential market exhaustion signals based on term structure, physical demand, and price action.

## Service Overview

This application provides tools for traders to identify potential market exhaustion signals in futures markets by analyzing:

- Term structure (contango/backwardation)
- Physical demand trends
- Price action and breakouts
- Open interest changes

The service offers both a web interface (Flask) and a REST API (FastAPI) for flexibility.

## Implementations

### 1. Web Interface (Flask)

- **URL**: `/` 
- **Port**: 5000
- **Description**: Web-based UI for entering market data and viewing analysis

### 2. REST API (FastAPI)

- **Base URL**: `http://localhost:8000`
- **Port**: 8000
- **Health Check**: GET `/health`
- **API Docs**: Access interactive documentation at `/docs`

## API Endpoints

### Analyze Market

Analyze futures market for potential exhaustion signals.

- **Endpoint**: `/analyze`
- **Method**: POST
- **Content-Type**: application/json

**Request Body**:

```json
{
  "ticker_front": "GC=F",
  "ticker_next": "GCM24.CMX",
  "physical_demand": "declining",
  "price_breakout": false
}
```

**Parameters**:

- `ticker_front`: Ticker symbol for front month contract (e.g., "GC=F" for Gold Front Month)
- `ticker_next`: Ticker symbol for next month contract (e.g., "GCM24.CMX")
- `physical_demand`: Current physical demand trend ("declining", "stable", "rising")
- `price_breakout`: Boolean indicating if price has broken resistance

**Response Example**:

```json
{
  "signal": "BEARISH — Potential exhaustion",
  "reasons": [
    "Contango widened: 1950.00 > 1900.00",
    "Open interest spike",
    "Price stalling (no breakout)",
    "Physical demand declining"
  ],
  "recommendations": [
    "Reduce long exposure in futures or ETFs",
    "Consider bear spreads or cash",
    "Watch roll yield drag on ETFs"
  ],
  "prices": {
    "front_contract": 1900.0,
    "next_contract": 1950.0,
    "contango_spread": "$50.00",
    "contango_percentage": "2.63%"
  },
  "analysis_timestamp": "2025-04-15 05:52:33.067109"
}
```

## Running the Services

### Using Replit Workflows

Two workflows are configured:

1. **Start application**: Runs the Flask web interface on port 5000
2. **run_futures_market_api**: Runs the FastAPI REST API on port 8000

### Running Locally

To run the Flask web interface:
```
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

To run the FastAPI REST API:
```
uvicorn fastapi_main:app --host=0.0.0.0 --port=8000
```

## Data Sources

The application uses yfinance to fetch real-time and historical market data from Yahoo Finance.