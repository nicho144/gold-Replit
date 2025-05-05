"""
Macroeconomic Indicators Module
This module provides access to key macroeconomic indicators that impact gold prices,
sourced from FRED (Federal Reserve Economic Data).
"""
import os
import logging
import datetime
from typing import Dict, List, Any, Optional, Union, Tuple
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Try to import FRED API, with fallbacks if not available
try:
    from fredapi import Fred
    FRED_AVAILABLE = True
except ImportError:
    FRED_AVAILABLE = False

# Key macroeconomic indicators that impact gold prices
MACRO_INDICATORS = {
    # Interest Rates
    "DGS10": {"name": "10-Year Treasury Yield", "category": "interest_rates", "units": "Percent"},
    "DGS5": {"name": "5-Year Treasury Yield", "category": "interest_rates", "units": "Percent"},
    "DGS2": {"name": "2-Year Treasury Yield", "category": "interest_rates", "units": "Percent"},
    "DGS1": {"name": "1-Year Treasury Yield", "category": "interest_rates", "units": "Percent"},
    "DTB3": {"name": "3-Month Treasury Bill", "category": "interest_rates", "units": "Percent"},
    "FEDFUNDS": {"name": "Federal Funds Rate", "category": "interest_rates", "units": "Percent"},
    
    # Inflation Metrics
    "T10YIE": {"name": "10-Year Breakeven Inflation", "category": "inflation", "units": "Percent"},
    "T5YIE": {"name": "5-Year Breakeven Inflation", "category": "inflation", "units": "Percent"},
    "CPIAUCSL": {"name": "Consumer Price Index", "category": "inflation", "units": "Index"},
    "PCEPI": {"name": "Personal Consumption Expenditures Price Index", "category": "inflation", "units": "Index"},
    
    # Economic Growth
    "GDPC1": {"name": "Real GDP", "category": "economic_growth", "units": "Billions of Chained 2017 Dollars"},
    "INDPRO": {"name": "Industrial Production", "category": "economic_growth", "units": "Index"},
    "PAYEMS": {"name": "Nonfarm Payrolls", "category": "economic_growth", "units": "Thousands of Persons"},
    "UNRATE": {"name": "Unemployment Rate", "category": "economic_growth", "units": "Percent"},
    
    # Dollar Strength
    "DTWEXBGS": {"name": "Trade Weighted US Dollar Index", "category": "dollar_strength", "units": "Index"},
    "DTWEXM": {"name": "Trade Weighted US Dollar Index (Major Currencies)", "category": "dollar_strength", "units": "Index"},
    
    # Market Sentiment
    "VIXCLS": {"name": "CBOE Volatility Index (VIX)", "category": "market_sentiment", "units": "Index"},
    "UMCSENT": {"name": "Consumer Sentiment", "category": "market_sentiment", "units": "Index"},
    
    # Commodities
    "WPU10210501": {"name": "PPI: Gold Ores", "category": "commodities", "units": "Index"},
    "PCU2122212122210": {"name": "PPI: Gold Ores Mining", "category": "commodities", "units": "Index"},
    "PPIACO": {"name": "PPI: All Commodities", "category": "commodities", "units": "Index"},
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

def get_indicator_data(series_id: str, observation_start: Optional[str] = None) -> Optional[pd.Series]:
    """
    Get data for a specific indicator from FRED
    
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
        # Default to 5 years of data if no start date provided
        if not observation_start:
            observation_start = (datetime.datetime.now() - datetime.timedelta(days=365*5)).strftime('%Y-%m-%d')
        
        data = fred.get_series(series_id, observation_start=observation_start)
        return data
    except Exception as e:
        logger.error(f"Error getting FRED series {series_id}: {str(e)}")
        return None

def get_indicator_info(series_id: str) -> Optional[Dict[str, Any]]:
    """
    Get metadata about a specific indicator from FRED
    
    Parameters:
    - series_id: The FRED series ID
    
    Returns:
    - Dictionary with metadata or None if unavailable
    """
    # Return info from our local dictionary if available
    if series_id in MACRO_INDICATORS:
        return MACRO_INDICATORS[series_id]
    
    fred = get_fred_client()
    if not fred:
        return None
    
    try:
        info = fred.get_series_info(series_id)
        return {
            "name": info.title,
            "units": info.units,
            "frequency": info.frequency,
            "seasonal_adjustment": info.seasonal_adjustment
        }
    except Exception as e:
        logger.error(f"Error getting info for FRED series {series_id}: {str(e)}")
        return None

def get_interest_rates_dashboard() -> Dict[str, Any]:
    """
    Get comprehensive interest rates data from FRED
    
    Returns:
    - Dictionary with interest rates data and analysis
    """
    result = {
        "rates": {},
        "spreads": {},
        "history": {},
        "analysis": {},
        "timestamp": str(datetime.datetime.now())
    }
    
    fred = get_fred_client()
    if not fred:
        logger.warning("FRED client not available, using estimated values")
        # Provide reasonable fallback
        result["data_source"] = "Estimated values (FRED API not available)"
        return result
    
    try:
        # Get key interest rates
        rate_series_ids = ["FEDFUNDS", "DTB3", "DGS1", "DGS2", "DGS5", "DGS10", "DGS30"]
        for series_id in rate_series_ids:
            data = get_indicator_data(series_id)
            if data is not None and not data.empty:
                # Store the latest value
                result["rates"][series_id] = {
                    "value": float(data.iloc[-1]),
                    "name": MACRO_INDICATORS.get(series_id, {}).get("name", series_id)
                }
                
                # Store historical data for charts (last 90 days)
                result["history"][series_id] = {
                    "data": data.iloc[-90:].to_dict(),
                    "name": MACRO_INDICATORS.get(series_id, {}).get("name", series_id)
                }
        
        # Calculate key spreads (if data available)
        if "DGS10" in result["rates"] and "DGS2" in result["rates"]:
            result["spreads"]["10y_2y"] = {
                "value": round(result["rates"]["DGS10"]["value"] - result["rates"]["DGS2"]["value"], 2),
                "name": "10-Year minus 2-Year Treasury"
            }
            
        if "DGS10" in result["rates"] and "DTB3" in result["rates"]:
            result["spreads"]["10y_3m"] = {
                "value": round(result["rates"]["DGS10"]["value"] - result["rates"]["DTB3"]["value"], 2),
                "name": "10-Year minus 3-Month Treasury"
            }
            
        if "DGS30" in result["rates"] and "DGS10" in result["rates"]:
            result["spreads"]["30y_10y"] = {
                "value": round(result["rates"]["DGS30"]["value"] - result["rates"]["DGS10"]["value"], 2),
                "name": "30-Year minus 10-Year Treasury"
            }
        
        # Add analysis of yield curve
        if "10y_2y" in result["spreads"]:
            spread_10y_2y = result["spreads"]["10y_2y"]["value"]
            if spread_10y_2y < -0.25:
                result["analysis"]["yield_curve"] = "Inverted yield curve (10yr-2yr) signals elevated recession risk"
            elif spread_10y_2y < 0:
                result["analysis"]["yield_curve"] = "Slightly inverted yield curve suggests caution"
            elif spread_10y_2y < 0.5:
                result["analysis"]["yield_curve"] = "Flat yield curve indicates slowing growth"
            else:
                result["analysis"]["yield_curve"] = "Positive yield curve suggests economic expansion"
        
        # Add gold implication based on real rates
        t10y = result["rates"].get("DGS10", {}).get("value", 0)
        t10y_infl = get_indicator_data("T10YIE")
        if t10y_infl is not None and not t10y_infl.empty:
            inflation_exp = float(t10y_infl.iloc[-1])
            real_rate = round(t10y - inflation_exp, 2)
            
            if real_rate < -1.0:
                result["analysis"]["gold_implication"] = "Strongly bullish for gold due to deeply negative real rates"
            elif real_rate < 0:
                result["analysis"]["gold_implication"] = "Bullish for gold due to negative real rates"
            elif real_rate < 1.0:
                result["analysis"]["gold_implication"] = "Neutral for gold with slightly positive real rates"
            else:
                result["analysis"]["gold_implication"] = "Bearish for gold due to significantly positive real rates"
                
            result["rates"]["real_10y"] = {
                "value": real_rate,
                "name": "10-Year Real Rate"
            }
        
        result["data_source"] = "Federal Reserve Economic Data (FRED)"
        return result
    except Exception as e:
        logger.error(f"Error getting interest rates dashboard: {str(e)}")
        result["data_source"] = "Error retrieving data"
        result["error"] = str(e)
        return result

def get_inflation_dashboard() -> Dict[str, Any]:
    """
    Get comprehensive inflation data from FRED
    
    Returns:
    - Dictionary with inflation data and analysis
    """
    result = {
        "current": {},
        "expectations": {},
        "history": {},
        "analysis": {},
        "timestamp": str(datetime.datetime.now())
    }
    
    fred = get_fred_client()
    if not fred:
        logger.warning("FRED client not available, using estimated values")
        # Provide reasonable fallback
        result["data_source"] = "Estimated values (FRED API not available)"
        return result
    
    try:
        # Get current inflation metrics
        current_series_ids = ["CPIAUCSL", "PCEPI"]
        for series_id in current_series_ids:
            data = get_indicator_data(series_id)
            if data is not None and not data.empty:
                # Calculate year-over-year percent change
                if len(data) >= 12:
                    yoy_change = (data.iloc[-1] / data.iloc[-13] - 1) * 100
                else:
                    yoy_change = None
                    
                result["current"][series_id] = {
                    "value": float(data.iloc[-1]),
                    "yoy_change": round(yoy_change, 2) if yoy_change is not None else None,
                    "name": MACRO_INDICATORS.get(series_id, {}).get("name", series_id)
                }
                
                # Store historical data for charts (last 60 months = 5 years)
                result["history"][series_id] = {
                    "data": data.iloc[-60:].to_dict(),
                    "name": MACRO_INDICATORS.get(series_id, {}).get("name", series_id)
                }
        
        # Get inflation expectations
        expectation_series_ids = ["T5YIE", "T10YIE"]
        for series_id in expectation_series_ids:
            data = get_indicator_data(series_id)
            if data is not None and not data.empty:
                result["expectations"][series_id] = {
                    "value": float(data.iloc[-1]),
                    "name": MACRO_INDICATORS.get(series_id, {}).get("name", series_id)
                }
                
                # Store historical data for charts (last 90 days)
                result["history"][series_id] = {
                    "data": data.iloc[-90:].to_dict(),
                    "name": MACRO_INDICATORS.get(series_id, {}).get("name", series_id)
                }
        
        # Add analysis based on inflation data
        if "CPIAUCSL" in result["current"] and result["current"]["CPIAUCSL"].get("yoy_change") is not None:
            cpi_yoy = result["current"]["CPIAUCSL"]["yoy_change"]
            if cpi_yoy > 5:
                result["analysis"]["inflation_status"] = "Significantly above Fed target, strongly negative for economic stability"
            elif cpi_yoy > 3:
                result["analysis"]["inflation_status"] = "Above Fed target, negative for economic stability"
            elif cpi_yoy > 2:
                result["analysis"]["inflation_status"] = "Slightly above Fed target, neutral for economic stability"
            else:
                result["analysis"]["inflation_status"] = "At or below Fed target, positive for economic stability"
        
        # Add gold implications based on inflation expectations
        if "T10YIE" in result["expectations"]:
            inflation_exp = result["expectations"]["T10YIE"]["value"]
            if inflation_exp > 3:
                result["analysis"]["gold_implication"] = "Strongly bullish for gold due to high inflation expectations"
            elif inflation_exp > 2.5:
                result["analysis"]["gold_implication"] = "Bullish for gold due to above-target inflation expectations"
            elif inflation_exp > 2.0:
                result["analysis"]["gold_implication"] = "Neutral to slightly bullish for gold with moderate inflation expectations"
            else:
                result["analysis"]["gold_implication"] = "Bearish for gold due to low inflation expectations"
        
        result["data_source"] = "Federal Reserve Economic Data (FRED)"
        return result
    except Exception as e:
        logger.error(f"Error getting inflation dashboard: {str(e)}")
        result["data_source"] = "Error retrieving data"
        result["error"] = str(e)
        return result

def get_economic_growth_dashboard() -> Dict[str, Any]:
    """
    Get comprehensive economic growth data from FRED
    
    Returns:
    - Dictionary with economic growth data and analysis
    """
    result = {
        "indicators": {},
        "history": {},
        "analysis": {},
        "timestamp": str(datetime.datetime.now())
    }
    
    fred = get_fred_client()
    if not fred:
        logger.warning("FRED client not available, using estimated values")
        # Provide reasonable fallback
        result["data_source"] = "Estimated values (FRED API not available)"
        return result
    
    try:
        # Get economic growth indicators
        series_ids = ["GDPC1", "INDPRO", "PAYEMS", "UNRATE"]
        for series_id in series_ids:
            data = get_indicator_data(series_id)
            if data is not None and not data.empty:
                # Store the latest value
                result["indicators"][series_id] = {
                    "value": float(data.iloc[-1]),
                    "name": MACRO_INDICATORS.get(series_id, {}).get("name", series_id)
                }
                
                # Calculate growth or change
                if series_id == "GDPC1" and len(data) >= 2:
                    # For GDP, calculate quarter-over-quarter percent change
                    qoq_change = (data.iloc[-1] / data.iloc[-2] - 1) * 100
                    result["indicators"][series_id]["qoq_change"] = round(qoq_change, 2)
                elif series_id == "INDPRO" and len(data) >= 13:
                    # For Industrial Production, calculate year-over-year percent change
                    yoy_change = (data.iloc[-1] / data.iloc[-13] - 1) * 100
                    result["indicators"][series_id]["yoy_change"] = round(yoy_change, 2)
                elif series_id == "PAYEMS" and len(data) >= 2:
                    # For Payrolls, calculate month-over-month change
                    mom_change = data.iloc[-1] - data.iloc[-2]
                    result["indicators"][series_id]["mom_change"] = int(mom_change)
                
                # Store historical data for charts (last 60 points)
                result["history"][series_id] = {
                    "data": data.iloc[-60:].to_dict(),
                    "name": MACRO_INDICATORS.get(series_id, {}).get("name", series_id)
                }
        
        # Add analysis of economic growth
        if "GDPC1" in result["indicators"] and "qoq_change" in result["indicators"]["GDPC1"]:
            gdp_growth = result["indicators"]["GDPC1"]["qoq_change"]
            if gdp_growth < 0:
                result["analysis"]["growth_status"] = "Contraction suggests potential recession"
            elif gdp_growth < 1:
                result["analysis"]["growth_status"] = "Very slow growth indicates economic weakness"
            elif gdp_growth < 2:
                result["analysis"]["growth_status"] = "Below-trend growth suggests caution"
            elif gdp_growth < 3:
                result["analysis"]["growth_status"] = "Moderate growth indicates stable economy"
            else:
                result["analysis"]["growth_status"] = "Strong growth suggests economic expansion"
        
        # Add unemployment analysis
        if "UNRATE" in result["indicators"]:
            unemployment = result["indicators"]["UNRATE"]["value"]
            if unemployment < 4:
                result["analysis"]["labor_market"] = "Very tight labor market indicates potential wage inflation"
            elif unemployment < 5:
                result["analysis"]["labor_market"] = "Strong labor market supports consumer spending"
            elif unemployment < 6:
                result["analysis"]["labor_market"] = "Moderate labor market indicates stable economy"
            else:
                result["analysis"]["labor_market"] = "Elevated unemployment suggests economic weakness"
        
        # Add gold implications based on economic conditions
        if ("growth_status" in result["analysis"]) and ("inflation_status" in result.get("analysis", {})):
            growth_status = result["analysis"]["growth_status"]
            if "recession" in growth_status.lower() or "contraction" in growth_status.lower():
                result["analysis"]["gold_implication"] = "Bullish for gold as safe haven during economic weakness"
            elif "weakness" in growth_status.lower() or "slow" in growth_status.lower():
                result["analysis"]["gold_implication"] = "Mildly bullish for gold due to economic uncertainty"
            elif "moderate" in growth_status.lower() or "stable" in growth_status.lower():
                result["analysis"]["gold_implication"] = "Neutral for gold with balanced economic growth"
            else:
                result["analysis"]["gold_implication"] = "Bearish for gold as strong growth favors risk assets"
        
        result["data_source"] = "Federal Reserve Economic Data (FRED)"
        return result
    except Exception as e:
        logger.error(f"Error getting economic growth dashboard: {str(e)}")
        result["data_source"] = "Error retrieving data"
        result["error"] = str(e)
        return result

def get_dollar_strength_dashboard() -> Dict[str, Any]:
    """
    Get dollar strength indicators from FRED
    
    Returns:
    - Dictionary with dollar strength data and analysis
    """
    result = {
        "indexes": {},
        "history": {},
        "analysis": {},
        "timestamp": str(datetime.datetime.now())
    }
    
    fred = get_fred_client()
    if not fred:
        logger.warning("FRED client not available, using estimated values")
        # Provide reasonable fallback
        result["data_source"] = "Estimated values (FRED API not available)"
        return result
    
    try:
        # Get dollar indexes
        series_ids = ["DTWEXBGS", "DTWEXM"]
        for series_id in series_ids:
            data = get_indicator_data(series_id)
            if data is not None and not data.empty:
                # Store the latest value
                result["indexes"][series_id] = {
                    "value": float(data.iloc[-1]),
                    "name": MACRO_INDICATORS.get(series_id, {}).get("name", series_id)
                }
                
                # Calculate change over different periods
                if len(data) >= 22:  # Approximately one month of trading days
                    mom_change = (data.iloc[-1] / data.iloc[-22] - 1) * 100
                    result["indexes"][series_id]["mom_change"] = round(mom_change, 2)
                
                if len(data) >= 252:  # Approximately one year of trading days
                    yoy_change = (data.iloc[-1] / data.iloc[-252] - 1) * 100
                    result["indexes"][series_id]["yoy_change"] = round(yoy_change, 2)
                
                # Store historical data for charts (last 252 days = 1 year)
                result["history"][series_id] = {
                    "data": data.iloc[-252:].to_dict(),
                    "name": MACRO_INDICATORS.get(series_id, {}).get("name", series_id)
                }
        
        # Add analysis of dollar strength
        if "DTWEXBGS" in result["indexes"] and "yoy_change" in result["indexes"]["DTWEXBGS"]:
            dollar_change = result["indexes"]["DTWEXBGS"]["yoy_change"]
            if dollar_change > 10:
                result["analysis"]["dollar_trend"] = "Very strong dollar suggests significant headwinds for commodities"
                result["analysis"]["gold_implication"] = "Strongly bearish for gold due to surging dollar"
            elif dollar_change > 5:
                result["analysis"]["dollar_trend"] = "Strong dollar creates headwinds for commodities"
                result["analysis"]["gold_implication"] = "Bearish for gold due to strengthening dollar"
            elif dollar_change > 0:
                result["analysis"]["dollar_trend"] = "Modest dollar strength creates mild pressure on commodities"
                result["analysis"]["gold_implication"] = "Mildly bearish for gold with appreciating dollar"
            elif dollar_change > -5:
                result["analysis"]["dollar_trend"] = "Mild dollar weakness supports commodity prices"
                result["analysis"]["gold_implication"] = "Mildly bullish for gold with depreciating dollar"
            else:
                result["analysis"]["dollar_trend"] = "Significant dollar weakness is highly supportive of commodities"
                result["analysis"]["gold_implication"] = "Strongly bullish for gold due to weakening dollar"
        
        result["data_source"] = "Federal Reserve Economic Data (FRED)"
        return result
    except Exception as e:
        logger.error(f"Error getting dollar strength dashboard: {str(e)}")
        result["data_source"] = "Error retrieving data"
        result["error"] = str(e)
        return result

def get_market_sentiment_dashboard() -> Dict[str, Any]:
    """
    Get market sentiment indicators from FRED
    
    Returns:
    - Dictionary with market sentiment data and analysis
    """
    result = {
        "indicators": {},
        "history": {},
        "analysis": {},
        "timestamp": str(datetime.datetime.now())
    }
    
    fred = get_fred_client()
    if not fred:
        logger.warning("FRED client not available, using estimated values")
        # Provide reasonable fallback
        result["data_source"] = "Estimated values (FRED API not available)"
        return result
    
    try:
        # Get sentiment indicators
        series_ids = ["VIXCLS", "UMCSENT"]
        for series_id in series_ids:
            data = get_indicator_data(series_id)
            if data is not None and not data.empty:
                # Store the latest value
                result["indicators"][series_id] = {
                    "value": float(data.iloc[-1]),
                    "name": MACRO_INDICATORS.get(series_id, {}).get("name", series_id)
                }
                
                # Store historical data for charts (last 90 days or points)
                result["history"][series_id] = {
                    "data": data.iloc[-90:].to_dict(),
                    "name": MACRO_INDICATORS.get(series_id, {}).get("name", series_id)
                }
        
        # Add analysis of VIX (volatility)
        if "VIXCLS" in result["indicators"]:
            vix = result["indicators"]["VIXCLS"]["value"]
            if vix > 30:
                result["analysis"]["market_volatility"] = "High volatility indicates significant market fear"
                result["analysis"]["gold_vix_implication"] = "Bullish for gold as a safe haven during market stress"
            elif vix > 20:
                result["analysis"]["market_volatility"] = "Elevated volatility suggests market uncertainty"
                result["analysis"]["gold_vix_implication"] = "Mildly bullish for gold due to increased uncertainty"
            else:
                result["analysis"]["market_volatility"] = "Low volatility indicates market complacency"
                result["analysis"]["gold_vix_implication"] = "Neutral to bearish for gold as safe haven demand is low"
        
        # Add analysis of consumer sentiment
        if "UMCSENT" in result["indicators"]:
            sentiment = result["indicators"]["UMCSENT"]["value"]
            if sentiment < 70:
                result["analysis"]["consumer_sentiment"] = "Very weak consumer sentiment suggests recession risk"
                result["analysis"]["gold_sentiment_implication"] = "Bullish for gold due to economic pessimism"
            elif sentiment < 80:
                result["analysis"]["consumer_sentiment"] = "Weak consumer sentiment indicates economic headwinds"
                result["analysis"]["gold_sentiment_implication"] = "Mildly bullish for gold with cautious consumers"
            elif sentiment < 90:
                result["analysis"]["consumer_sentiment"] = "Moderate consumer sentiment suggests stable economy"
                result["analysis"]["gold_sentiment_implication"] = "Neutral for gold with balanced sentiment"
            else:
                result["analysis"]["consumer_sentiment"] = "Strong consumer sentiment indicates economic optimism"
                result["analysis"]["gold_sentiment_implication"] = "Bearish for gold as optimism favors risk assets"
        
        result["data_source"] = "Federal Reserve Economic Data (FRED)"
        return result
    except Exception as e:
        logger.error(f"Error getting market sentiment dashboard: {str(e)}")
        result["data_source"] = "Error retrieving data"
        result["error"] = str(e)
        return result

def get_comprehensive_macro_dashboard() -> Dict[str, Any]:
    """
    Get a comprehensive macroeconomic dashboard with all relevant indicators
    
    Returns:
    - Dictionary with all macroeconomic data and combined analysis
    """
    result = {
        "interest_rates": get_interest_rates_dashboard(),
        "inflation": get_inflation_dashboard(),
        "economic_growth": get_economic_growth_dashboard(),
        "dollar_strength": get_dollar_strength_dashboard(),
        "market_sentiment": get_market_sentiment_dashboard(),
        "combined_analysis": {},
        "timestamp": str(datetime.datetime.now())
    }
    
    # Create a combined implications analysis for gold
    gold_implications = []
    
    # Add interest rate implications
    if "gold_implication" in result["interest_rates"].get("analysis", {}):
        gold_implications.append({
            "factor": "Interest Rates",
            "implication": result["interest_rates"]["analysis"]["gold_implication"]
        })
    
    # Add inflation implications
    if "gold_implication" in result["inflation"].get("analysis", {}):
        gold_implications.append({
            "factor": "Inflation",
            "implication": result["inflation"]["analysis"]["gold_implication"]
        })
    
    # Add economic growth implications
    if "gold_implication" in result["economic_growth"].get("analysis", {}):
        gold_implications.append({
            "factor": "Economic Growth",
            "implication": result["economic_growth"]["analysis"]["gold_implication"]
        })
    
    # Add dollar strength implications
    if "gold_implication" in result["dollar_strength"].get("analysis", {}):
        gold_implications.append({
            "factor": "Dollar Strength",
            "implication": result["dollar_strength"]["analysis"]["gold_implication"]
        })
    
    # Add market sentiment implications
    if "gold_vix_implication" in result["market_sentiment"].get("analysis", {}):
        gold_implications.append({
            "factor": "Market Volatility",
            "implication": result["market_sentiment"]["analysis"]["gold_vix_implication"]
        })
    
    if "gold_sentiment_implication" in result["market_sentiment"].get("analysis", {}):
        gold_implications.append({
            "factor": "Consumer Sentiment",
            "implication": result["market_sentiment"]["analysis"]["gold_sentiment_implication"]
        })
    
    # Add the implications to the result
    result["combined_analysis"]["gold_implications"] = gold_implications
    
    # Count the bullish, bearish, and neutral factors
    bullish_count = sum(1 for imp in gold_implications if "bullish" in imp["implication"].lower())
    bearish_count = sum(1 for imp in gold_implications if "bearish" in imp["implication"].lower())
    neutral_count = len(gold_implications) - bullish_count - bearish_count
    
    # Determine overall bias based on majority
    if bullish_count > bearish_count + neutral_count:
        overall_bias = "Strongly Bullish"
    elif bullish_count > bearish_count:
        overall_bias = "Moderately Bullish"
    elif bearish_count > bullish_count + neutral_count:
        overall_bias = "Strongly Bearish"
    elif bearish_count > bullish_count:
        overall_bias = "Moderately Bearish"
    else:
        overall_bias = "Neutral"
    
    result["combined_analysis"]["overall_gold_bias"] = overall_bias
    result["combined_analysis"]["bullish_factors"] = bullish_count
    result["combined_analysis"]["bearish_factors"] = bearish_count
    result["combined_analysis"]["neutral_factors"] = neutral_count
    result["combined_analysis"]["total_factors"] = len(gold_implications)
    
    result["data_source"] = "Federal Reserve Economic Data (FRED)"
    return result