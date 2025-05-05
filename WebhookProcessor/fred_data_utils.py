"""
Federal Reserve Economic Data (FRED) utilities
This module provides access to official government data 
from the Federal Reserve Economic Data (FRED) API.
"""
import os
import logging
import datetime
from typing import Dict, List, Any, Optional, Union, Tuple
import pandas as pd
import numpy as np

# FRED API is optional, fall back to estimated data if not available
try:
    from fredapi import Fred
    FRED_AVAILABLE = True
except ImportError:
    FRED_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# FRED series IDs for common economic indicators
SERIES_IDS = {
    "T10Y2Y": "T10Y2Y",             # 10-Year Treasury Constant Maturity Minus 2-Year Treasury Constant Maturity
    "DGS10": "DGS10",               # 10-Year Treasury Constant Maturity Rate
    "DGS5": "DGS5",                 # 5-Year Treasury Constant Maturity Rate
    "DGS2": "DGS2",                 # 2-Year Treasury Constant Maturity Rate
    "DGS1": "DGS1",                 # 1-Year Treasury Constant Maturity Rate
    "DTB3": "DTB3",                 # 3-Month Treasury Bill: Secondary Market Rate
    "T10YIE": "T10YIE",             # 10-Year Breakeven Inflation Rate
    "T5YIE": "T5YIE",               # 5-Year Breakeven Inflation Rate
    "GOLDAMGBD228NLBM": "GOLDAMGBD228NLBM",  # Gold Fixing Price 10:30 A.M. (London time) in London Bullion Market
    "CPIAUCSL": "CPIAUCSL",         # Consumer Price Index for All Urban Consumers: All Items in U.S. City Average
    "CORESTICKM159SFRBATL": "CORESTICKM159SFRBATL",  # Sticky Price Consumer Price Index less Food and Energy
    "VIXCLS": "VIXCLS",             # CBOE Volatility Index: VIX
    "DTWEXBGS": "DTWEXBGS",         # Trade Weighted U.S. Dollar Index: Broad
    "UNRATE": "UNRATE",             # Unemployment Rate
    "PAYEMS": "PAYEMS",             # All Employees, Total Nonfarm
    "INDPRO": "INDPRO",             # Industrial Production Index
    "UMCSENT": "UMCSENT",           # University of Michigan: Consumer Sentiment
}

def get_fred_client() -> Optional[Any]:
    """Get a FRED API client if the API key is available"""
    api_key = os.environ.get("FRED_API_KEY")
    if not api_key or not FRED_AVAILABLE:
        logger.warning("FRED API key not available or fredapi not installed")
        return None
    
    try:
        return Fred(api_key=api_key)
    except Exception as e:
        logger.error(f"Error initializing FRED client: {str(e)}")
        return None

def get_series_data(series_id: str, observation_start: Optional[str] = None) -> Optional[pd.Series]:
    """
    Get data for a specific FRED series
    
    Parameters:
    - series_id: The FRED series ID
    - observation_start: Optional start date in 'YYYY-MM-DD' format
    
    Returns:
    - pandas Series with the data or None if unavailable
    """
    fred = get_fred_client()
    if not fred:
        return None
    
    try:
        # Get series data (default to 5 years of data if no start date provided)
        if not observation_start:
            observation_start = (datetime.datetime.now() - datetime.timedelta(days=365*5)).strftime('%Y-%m-%d')
        
        data = fred.get_series(series_id, observation_start=observation_start)
        return data
    except Exception as e:
        logger.error(f"Error getting FRED series {series_id}: {str(e)}")
        return None

def get_real_interest_rates() -> Dict[str, Any]:
    """
    Calculate real interest rates using official FRED data
    
    Real Rate = Nominal Rate - Inflation Expectations
    
    Returns a dictionary with nominal rates, inflation expectations, and real rates
    """
    result = {
        "nominal_rates": {},
        "inflation_expectations": {},
        "real_rates": {},
        "analysis": {},
        "timestamp": str(datetime.datetime.now())
    }
    
    fred = get_fred_client()
    if not fred:
        logger.warning("FRED client not available, using estimated values")
        # Fallback to reasonable estimates
        result["nominal_rates"]["t10y"] = 4.3
        result["inflation_expectations"]["t10y"] = 2.8
        result["real_rates"]["t10y"] = 1.5
        result["nominal_rates"]["t5y"] = 4.1
        result["inflation_expectations"]["t5y"] = 2.6
        result["real_rates"]["t5y"] = 1.5
        result["nominal_rates"]["t2y"] = 4.0
        result["inflation_expectations"]["t2y"] = 2.5
        result["real_rates"]["t2y"] = 1.5
        result["analysis"]["implication"] = "Gold may struggle as investors can get positive real returns on Treasuries."
        result["data_source"] = "Estimated values (FRED API not available)"
        return result
    
    try:
        # Get 10-year Treasury yield (nominal rate)
        t10y = get_series_data("DGS10")
        if t10y is not None and not t10y.empty:
            result["nominal_rates"]["t10y"] = float(t10y.iloc[-1])
        else:
            result["nominal_rates"]["t10y"] = 4.3  # Fallback
        
        # Get 5-year Treasury yield
        t5y = get_series_data("DGS5")
        if t5y is not None and not t5y.empty:
            result["nominal_rates"]["t5y"] = float(t5y.iloc[-1])
        else:
            result["nominal_rates"]["t5y"] = 4.1  # Fallback
            
        # Get 2-year Treasury yield
        t2y = get_series_data("DGS2")
        if t2y is not None and not t2y.empty:
            result["nominal_rates"]["t2y"] = float(t2y.iloc[-1])
        else:
            result["nominal_rates"]["t2y"] = 4.0  # Fallback
            
        # Get inflation expectations (10-year breakeven inflation rate)
        t10y_inflation = get_series_data("T10YIE")
        if t10y_inflation is not None and not t10y_inflation.empty:
            result["inflation_expectations"]["t10y"] = float(t10y_inflation.iloc[-1])
        else:
            result["inflation_expectations"]["t10y"] = 2.8  # Fallback
            
        # Get inflation expectations (5-year breakeven inflation rate)
        t5y_inflation = get_series_data("T5YIE")
        if t5y_inflation is not None and not t5y_inflation.empty:
            result["inflation_expectations"]["t5y"] = float(t5y_inflation.iloc[-1])
        else:
            result["inflation_expectations"]["t5y"] = 2.6  # Fallback
            
        # Estimate 2-year inflation expectations (usually close to 5-year but slightly lower)
        result["inflation_expectations"]["t2y"] = result["inflation_expectations"]["t5y"] - 0.1
        
        # Calculate real rates
        result["real_rates"]["t10y"] = round(result["nominal_rates"]["t10y"] - result["inflation_expectations"]["t10y"], 2)
        result["real_rates"]["t5y"] = round(result["nominal_rates"]["t5y"] - result["inflation_expectations"]["t5y"], 2)
        result["real_rates"]["t2y"] = round(result["nominal_rates"]["t2y"] - result["inflation_expectations"]["t2y"], 2)
        
        # Analyze implications for gold
        t10y_real = result["real_rates"]["t10y"]
        
        if t10y_real < -1.0:
            implication = "Strong positive for gold. Deeply negative real rates make gold highly attractive as cash is rapidly losing value."
        elif t10y_real < 0:
            implication = "Positive for gold. Negative real rates make gold appealing as a store of value."
        elif t10y_real < 1.0:
            implication = "Neutral to slightly negative for gold. Slightly positive real rates create modest competition for gold."
        else:
            implication = "Negative for gold. Significantly positive real rates make interest-bearing assets more attractive than gold."
        
        result["analysis"]["implication"] = implication
        result["data_source"] = "Federal Reserve Economic Data (FRED)"
        
        return result
    except Exception as e:
        logger.error(f"Error calculating real interest rates: {str(e)}")
        # Fallback to reasonable estimates
        result["nominal_rates"]["t10y"] = 4.3
        result["inflation_expectations"]["t10y"] = 2.8
        result["real_rates"]["t10y"] = 1.5
        result["nominal_rates"]["t5y"] = 4.1
        result["inflation_expectations"]["t5y"] = 2.6
        result["real_rates"]["t5y"] = 1.5
        result["nominal_rates"]["t2y"] = 4.0
        result["inflation_expectations"]["t2y"] = 2.5
        result["real_rates"]["t2y"] = 1.5
        result["analysis"]["implication"] = "Gold may struggle as investors can get positive real returns on Treasuries."
        result["data_source"] = "Estimated values (error accessing FRED)"
        return result

def get_yield_curve() -> Dict[str, Any]:
    """
    Get the Treasury yield curve from FRED data
    
    Returns a dictionary with yield curve data and analysis
    """
    result = {
        "yields": {},
        "spreads": {},
        "analysis": {},
        "timestamp": str(datetime.datetime.now())
    }
    
    fred = get_fred_client()
    if not fred:
        logger.warning("FRED client not available, using estimated values")
        # Fallback to reasonable estimates
        result["yields"]["t30y"] = 4.5
        result["yields"]["t10y"] = 4.3
        result["yields"]["t5y"] = 4.1
        result["yields"]["t2y"] = 4.0
        result["yields"]["t1y"] = 3.9
        result["yields"]["t3m"] = 3.8
        result["spreads"]["t10y_t2y"] = 0.3
        result["spreads"]["t10y_t3m"] = 0.5
        result["analysis"]["shape"] = "Slightly positive slope"
        result["analysis"]["recession_signal"] = "Low recession risk"
        result["data_source"] = "Estimated values (FRED API not available)"
        return result
    
    try:
        # Get Treasury yields for various maturities
        t30y = get_series_data("DGS30")
        t10y = get_series_data("DGS10")
        t5y = get_series_data("DGS5")
        t2y = get_series_data("DGS2")
        t1y = get_series_data("DGS1")
        t3m = get_series_data("DTB3")
        
        # Store latest values
        if t30y is not None and not t30y.empty:
            result["yields"]["t30y"] = float(t30y.iloc[-1])
        else:
            result["yields"]["t30y"] = 4.5  # Fallback
            
        if t10y is not None and not t10y.empty:
            result["yields"]["t10y"] = float(t10y.iloc[-1])
        else:
            result["yields"]["t10y"] = 4.3  # Fallback
            
        if t5y is not None and not t5y.empty:
            result["yields"]["t5y"] = float(t5y.iloc[-1])
        else:
            result["yields"]["t5y"] = 4.1  # Fallback
            
        if t2y is not None and not t2y.empty:
            result["yields"]["t2y"] = float(t2y.iloc[-1])
        else:
            result["yields"]["t2y"] = 4.0  # Fallback
            
        if t1y is not None and not t1y.empty:
            result["yields"]["t1y"] = float(t1y.iloc[-1])
        else:
            result["yields"]["t1y"] = 3.9  # Fallback
            
        if t3m is not None and not t3m.empty:
            result["yields"]["t3m"] = float(t3m.iloc[-1])
        else:
            result["yields"]["t3m"] = 3.8  # Fallback
        
        # Calculate key spreads
        result["spreads"]["t10y_t2y"] = round(result["yields"]["t10y"] - result["yields"]["t2y"], 2)
        result["spreads"]["t10y_t3m"] = round(result["yields"]["t10y"] - result["yields"]["t3m"], 2)
        result["spreads"]["t30y_t10y"] = round(result["yields"]["t30y"] - result["yields"]["t10y"], 2)
        result["spreads"]["t5y_t2y"] = round(result["yields"]["t5y"] - result["yields"]["t2y"], 2)
        
        # Analyze yield curve shape
        if result["spreads"]["t10y_t2y"] < -0.25:
            curve_shape = "Inverted (10yr-2yr)"
            recession_risk = "Elevated recession risk signal"
        elif result["spreads"]["t10y_t3m"] < -0.25:
            curve_shape = "Inverted (10yr-3mo)"
            recession_risk = "Elevated recession risk signal"
        elif result["spreads"]["t10y_t2y"] < 0:
            curve_shape = "Slightly inverted"
            recession_risk = "Moderate recession risk"
        elif result["spreads"]["t10y_t2y"] < 0.5:
            curve_shape = "Flat to slightly positive"
            recession_risk = "Low to moderate recession risk"
        else:
            curve_shape = "Positive slope"
            recession_risk = "Lower recession risk"
        
        result["analysis"]["shape"] = curve_shape
        result["analysis"]["recession_signal"] = recession_risk
        result["data_source"] = "Federal Reserve Economic Data (FRED)"
        
        return result
    except Exception as e:
        logger.error(f"Error getting yield curve data: {str(e)}")
        # Fallback to reasonable estimates
        result["yields"]["t30y"] = 4.5
        result["yields"]["t10y"] = 4.3
        result["yields"]["t5y"] = 4.1
        result["yields"]["t2y"] = 4.0
        result["yields"]["t1y"] = 3.9
        result["yields"]["t3m"] = 3.8
        result["spreads"]["t10y_t2y"] = 0.3
        result["spreads"]["t10y_t3m"] = 0.5
        result["analysis"]["shape"] = "Slightly positive slope"
        result["analysis"]["recession_signal"] = "Low recession risk"
        result["data_source"] = "Estimated values (error accessing FRED)"
        return result

def get_gold_price() -> Dict[str, Any]:
    """
    Get the gold price from FRED data
    
    Returns a dictionary with gold price data and analysis
    """
    result = {
        "prices": {},
        "changes": {},
        "analysis": {},
        "timestamp": str(datetime.datetime.now())
    }
    
    fred = get_fred_client()
    if not fred:
        logger.warning("FRED client not available, using estimated values")
        # Fallback to reasonable estimates
        result["prices"]["current"] = 2350.0
        result["prices"]["prev_day"] = 2345.0
        result["prices"]["month_ago"] = 2300.0
        result["prices"]["year_ago"] = 2100.0
        result["changes"]["daily"] = 0.2
        result["changes"]["monthly"] = 2.2
        result["changes"]["yearly"] = 11.9
        result["analysis"]["performance"] = "Gold has been in a strong uptrend over the past year."
        result["data_source"] = "Estimated values (FRED API not available)"
        return result
    
    try:
        # Get gold price data
        gold = get_series_data("GOLDAMGBD228NLBM", 
                               observation_start=(datetime.datetime.now() - datetime.timedelta(days=365*2)).strftime('%Y-%m-%d'))
        
        if gold is not None and not gold.empty:
            # Get latest price and historical prices for comparison
            latest_price = float(gold.iloc[-1])
            prev_day_price = float(gold.iloc[-2]) if len(gold) > 1 else latest_price * 0.998
            
            # Find price from approximately one month ago (21 trading days)
            month_ago_idx = -22 if len(gold) >= 22 else 0
            month_ago_price = float(gold.iloc[month_ago_idx])
            
            # Find price from approximately one year ago (252 trading days)
            year_ago_idx = -252 if len(gold) >= 252 else 0
            year_ago_price = float(gold.iloc[year_ago_idx])
            
            # Store prices
            result["prices"]["current"] = latest_price
            result["prices"]["prev_day"] = prev_day_price
            result["prices"]["month_ago"] = month_ago_price
            result["prices"]["year_ago"] = year_ago_price
            
            # Calculate changes
            result["changes"]["daily"] = round((latest_price / prev_day_price - 1) * 100, 2)
            result["changes"]["monthly"] = round((latest_price / month_ago_price - 1) * 100, 2)
            result["changes"]["yearly"] = round((latest_price / year_ago_price - 1) * 100, 2)
            
            # Analyze performance
            if result["changes"]["yearly"] > 20:
                performance = "Gold has shown exceptional strength over the past year."
            elif result["changes"]["yearly"] > 10:
                performance = "Gold has been in a strong uptrend over the past year."
            elif result["changes"]["yearly"] > 0:
                performance = "Gold has shown modest gains over the past year."
            else:
                performance = "Gold has struggled to make gains over the past year."
                
            result["analysis"]["performance"] = performance
            result["data_source"] = "Federal Reserve Economic Data (FRED)"
        else:
            # Fallback to reasonable estimates
            result["prices"]["current"] = 2350.0
            result["prices"]["prev_day"] = 2345.0
            result["prices"]["month_ago"] = 2300.0
            result["prices"]["year_ago"] = 2100.0
            result["changes"]["daily"] = 0.2
            result["changes"]["monthly"] = 2.2
            result["changes"]["yearly"] = 11.9
            result["analysis"]["performance"] = "Gold has been in a strong uptrend over the past year."
            result["data_source"] = "Estimated values (FRED data unavailable)"
        
        return result
    except Exception as e:
        logger.error(f"Error getting gold price data: {str(e)}")
        # Fallback to reasonable estimates
        result["prices"]["current"] = 2350.0
        result["prices"]["prev_day"] = 2345.0
        result["prices"]["month_ago"] = 2300.0
        result["prices"]["year_ago"] = 2100.0
        result["changes"]["daily"] = 0.2
        result["changes"]["monthly"] = 2.2
        result["changes"]["yearly"] = 11.9
        result["analysis"]["performance"] = "Gold has been in a strong uptrend over the past year."
        result["data_source"] = "Estimated values (error accessing FRED)"
        return result