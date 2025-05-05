"""
Combined Analysis Module
This module correlates market data (futures term structure) with
macroeconomic indicators (real rates, etc.) to provide deeper market insights.
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

# Import utilities for fetching data
try:
    from fred_data_utils import get_real_interest_rates, get_yield_curve
    from market_data_utils import get_gold_term_structure_data
    from macroeconomic_indicators import get_interest_rates_dashboard, get_inflation_dashboard, get_dollar_strength_dashboard
    
    DATA_MODULES_AVAILABLE = True
except ImportError as e:
    logger.error(f"Error importing data modules: {str(e)}")
    DATA_MODULES_AVAILABLE = False

def get_correlated_analysis() -> Dict[str, Any]:
    """
    Correlate gold term structure with real interest rates
    
    This function analyzes the relationship between real interest rates
    and gold futures term structure to identify potential market signals.
    
    Returns:
    - Dictionary with correlated analysis and insights
    """
    result = {
        "term_structure": {},
        "real_rates": {},
        "correlations": {},
        "analysis": {},
        "timestamp": str(datetime.datetime.now())
    }
    
    if not DATA_MODULES_AVAILABLE:
        logger.warning("Required data modules not available")
        result["error"] = "Required data modules not available"
        return result
    
    try:
        # Get gold term structure data
        gold_term_structure = get_gold_term_structure_data()
        if gold_term_structure:
            result["term_structure"] = gold_term_structure
        else:
            logger.warning("Gold term structure data not available")
            result["term_structure"]["error"] = "Data not available"
        
        # Get real interest rates data
        real_rates = get_real_interest_rates()
        if real_rates:
            result["real_rates"] = real_rates
        else:
            logger.warning("Real interest rates data not available")
            result["real_rates"]["error"] = "Data not available"
        
        # Perform correlation analysis if both datasets are available
        if "error" not in result["term_structure"] and "error" not in result["real_rates"]:
            # Calculate correlations and insights
            
            # Extract real 10-year rate
            if "real_rates" in real_rates and "t10y" in real_rates["real_rates"]:
                real_10y_rate = real_rates["real_rates"]["t10y"]
            else:
                real_10y_rate = None
            
            # Extract term structure status
            term_structure_status = None
            if "spreads" in gold_term_structure and "gc1_gc2" in gold_term_structure["spreads"]:
                gc1_gc2_spread = gold_term_structure["spreads"]["gc1_gc2"]
                term_structure_status = "contango" if gc1_gc2_spread < 0 else "backwardation"
            
            # Record the correlation data
            result["correlations"]["real_10y_rate"] = real_10y_rate
            result["correlations"]["term_structure_status"] = term_structure_status
            
            # Generate insights based on correlation
            if real_10y_rate is not None and term_structure_status is not None:
                if real_10y_rate < -1.0 and term_structure_status == "backwardation":
                    result["analysis"]["correlation_signal"] = "Strong gold bull signal"
                    result["analysis"]["signal_explanation"] = "Deeply negative real rates combined with backwardation in gold futures suggests strong physical demand and bullish momentum"
                elif real_10y_rate < 0 and term_structure_status == "backwardation":
                    result["analysis"]["correlation_signal"] = "Moderate gold bull signal"
                    result["analysis"]["signal_explanation"] = "Negative real rates with backwardation suggests supportive monetary conditions and strong physical demand"
                elif real_10y_rate < 0 and term_structure_status == "contango":
                    result["analysis"]["correlation_signal"] = "Mixed signal with bullish bias"
                    result["analysis"]["signal_explanation"] = "Negative real rates are supportive for gold, but contango suggests limited immediate physical demand"
                elif real_10y_rate > 1.0 and term_structure_status == "contango":
                    result["analysis"]["correlation_signal"] = "Strong gold bear signal"
                    result["analysis"]["signal_explanation"] = "Positive real rates combined with contango suggests weak demand and bearish momentum"
                elif real_10y_rate > 0 and term_structure_status == "contango":
                    result["analysis"]["correlation_signal"] = "Moderate gold bear signal"
                    result["analysis"]["signal_explanation"] = "Positive real rates with contango suggests challenging monetary conditions and weak physical demand"
                elif real_10y_rate > 0 and term_structure_status == "backwardation":
                    result["analysis"]["correlation_signal"] = "Mixed signal with bearish bias"
                    result["analysis"]["signal_explanation"] = "Positive real rates are challenging for gold, but backwardation suggests strong immediate physical demand"
                else:
                    result["analysis"]["correlation_signal"] = "Neutral signal"
                    result["analysis"]["signal_explanation"] = "Current conditions do not provide a clear directional bias"
            
            # Add quantitative factors
            if real_10y_rate is not None:
                result["analysis"]["real_rate_factor"] = "bullish" if real_10y_rate < 0 else "bearish"
                result["analysis"]["real_rate_strength"] = abs(real_10y_rate)
            
            if term_structure_status is not None:
                result["analysis"]["term_structure_factor"] = "bullish" if term_structure_status == "backwardation" else "bearish"
                if "gc1_gc2" in gold_term_structure.get("spreads", {}):
                    result["analysis"]["term_structure_strength"] = abs(gold_term_structure["spreads"]["gc1_gc2"])
        
        return result
    except Exception as e:
        logger.error(f"Error in correlated analysis: {str(e)}")
        result["error"] = str(e)
        return result

def get_market_divergence_analysis() -> Dict[str, Any]:
    """
    Identify divergences between gold price and macroeconomic factors
    
    This function looks for situations where gold prices are moving
    contrary to what fundamental factors would suggest, which can
    indicate potential turning points.
    
    Returns:
    - Dictionary with divergence analysis and potential signals
    """
    result = {
        "price_trend": {},
        "fundamental_factors": {},
        "divergences": {},
        "analysis": {},
        "timestamp": str(datetime.datetime.now())
    }
    
    if not DATA_MODULES_AVAILABLE:
        logger.warning("Required data modules not available")
        result["error"] = "Required data modules not available"
        return result
    
    try:
        # Get gold term structure data for price information
        gold_term_structure = get_gold_term_structure_data()
        if gold_term_structure and "prices" in gold_term_structure and "front_month" in gold_term_structure["prices"]:
            front_month = gold_term_structure["prices"]["front_month"]
            if "price" in front_month:
                result["price_trend"]["current_price"] = front_month["price"]
            
            # We would need historical prices to determine the trend
            # This would require additional data sources or API calls
            
            # For demonstration, assume we have trend information
            # In a real implementation, this would be calculated from historical data
            result["price_trend"]["short_term_trend"] = gold_term_structure.get("trend", {}).get("short_term", "neutral")
            result["price_trend"]["medium_term_trend"] = gold_term_structure.get("trend", {}).get("medium_term", "neutral")
        else:
            logger.warning("Gold price data not available")
            result["price_trend"]["error"] = "Price data not available"
        
        # Get fundamental factors
        # Real interest rates
        real_rates = get_real_interest_rates()
        if real_rates and "real_rates" in real_rates and "t10y" in real_rates["real_rates"]:
            result["fundamental_factors"]["real_rates"] = real_rates["real_rates"]["t10y"]
            result["fundamental_factors"]["real_rates_implication"] = "bullish" if real_rates["real_rates"]["t10y"] < 0 else "bearish"
        
        # Dollar strength
        dollar_strength = get_dollar_strength_dashboard()
        if dollar_strength and "indexes" in dollar_strength and "DTWEXBGS" in dollar_strength["indexes"]:
            if "yoy_change" in dollar_strength["indexes"]["DTWEXBGS"]:
                dollar_yoy = dollar_strength["indexes"]["DTWEXBGS"]["yoy_change"]
                result["fundamental_factors"]["dollar_strength"] = dollar_yoy
                result["fundamental_factors"]["dollar_implication"] = "bullish" if dollar_yoy < 0 else "bearish"
        
        # Inflation expectations
        inflation_data = get_inflation_dashboard()
        if inflation_data and "expectations" in inflation_data and "T10YIE" in inflation_data["expectations"]:
            infl_exp = inflation_data["expectations"]["T10YIE"]["value"]
            result["fundamental_factors"]["inflation_expectations"] = infl_exp
            result["fundamental_factors"]["inflation_implication"] = "bullish" if infl_exp > 2.5 else "neutral" if infl_exp > 2.0 else "bearish"
        
        # Check for divergences
        divergences_found = False
        
        # Only perform divergence analysis if we have price trend and fundamental data
        if "short_term_trend" in result["price_trend"] and "real_rates_implication" in result["fundamental_factors"]:
            # Count bullish and bearish fundamental factors
            bullish_count = sum(1 for key, value in result["fundamental_factors"].items() if key.endswith("_implication") and value == "bullish")
            bearish_count = sum(1 for key, value in result["fundamental_factors"].items() if key.endswith("_implication") and value == "bearish")
            neutral_count = sum(1 for key, value in result["fundamental_factors"].items() if key.endswith("_implication") and value == "neutral")
            
            # Determine overall fundamental bias
            fundamental_bias = "neutral"
            if bullish_count > bearish_count + neutral_count:
                fundamental_bias = "strongly_bullish"
            elif bullish_count > bearish_count:
                fundamental_bias = "moderately_bullish"
            elif bearish_count > bullish_count + neutral_count:
                fundamental_bias = "strongly_bearish"
            elif bearish_count > bullish_count:
                fundamental_bias = "moderately_bearish"
            
            result["fundamental_factors"]["overall_bias"] = fundamental_bias
            
            # Check if price trend contradicts fundamental bias
            price_trend = result["price_trend"]["short_term_trend"]
            
            if (price_trend == "bearish" and "bullish" in fundamental_bias) or (price_trend == "strongly_bearish" and "bullish" in fundamental_bias):
                result["divergences"]["price_fundamentals"] = "bearish_price_bullish_fundamentals"
                result["divergences"]["explanation"] = "Gold price is declining despite bullish fundamental factors"
                result["divergences"]["potential_signal"] = "Potential buying opportunity if bearish price momentum stabilizes"
                divergences_found = True
            elif (price_trend == "bullish" and "bearish" in fundamental_bias) or (price_trend == "strongly_bullish" and "bearish" in fundamental_bias):
                result["divergences"]["price_fundamentals"] = "bullish_price_bearish_fundamentals"
                result["divergences"]["explanation"] = "Gold price is rising despite bearish fundamental factors"
                result["divergences"]["potential_signal"] = "Potential selling opportunity if bullish price momentum wanes"
                divergences_found = True
            
            # Specific divergence checks for key factors
            if "real_rates_implication" in result["fundamental_factors"] and price_trend in ["bearish", "strongly_bearish"] and result["fundamental_factors"]["real_rates_implication"] == "bullish":
                result["divergences"]["real_rates"] = "Price weakness despite supportive real rates suggests other negative factors are dominating"
                divergences_found = True
            
            if "dollar_implication" in result["fundamental_factors"] and price_trend in ["bullish", "strongly_bullish"] and result["fundamental_factors"]["dollar_implication"] == "bearish":
                result["divergences"]["dollar"] = "Price strength despite dollar headwinds suggests other positive factors are dominating"
                divergences_found = True
        
        # Add overall analysis
        if divergences_found:
            result["analysis"]["summary"] = "Market divergences detected"
            result["analysis"]["recommendation"] = "Monitor closely for potential trend reversal"
        else:
            result["analysis"]["summary"] = "No significant divergences detected"
            result["analysis"]["recommendation"] = "Price action is aligned with fundamental factors"
        
        return result
    except Exception as e:
        logger.error(f"Error in market divergence analysis: {str(e)}")
        result["error"] = str(e)
        return result

def get_integrated_dashboard() -> Dict[str, Any]:
    """
    Create a comprehensive integrated dashboard combining market data with macroeconomic indicators
    
    Returns:
    - Dictionary with comprehensive market analysis
    """
    result = {
        "market_data": {},
        "macroeconomic_data": {},
        "correlated_analysis": {},
        "divergence_analysis": {},
        "combined_signals": {},
        "timestamp": str(datetime.datetime.now())
    }
    
    if not DATA_MODULES_AVAILABLE:
        logger.warning("Required data modules not available")
        result["error"] = "Required data modules not available"
        return result
    
    try:
        # Get market data (term structure)
        gold_term_structure = get_gold_term_structure_data()
        if gold_term_structure:
            result["market_data"]["term_structure"] = gold_term_structure
            
            # Extract key metrics for easy access
            if "prices" in gold_term_structure and "front_month" in gold_term_structure["prices"]:
                result["market_data"]["gc1_price"] = gold_term_structure["prices"]["front_month"].get("price", "N/A")
            
            if "spreads" in gold_term_structure:
                result["market_data"]["gc1_gc2_spread"] = gold_term_structure["spreads"].get("gc1_gc2", "N/A")
                result["market_data"]["structure_type"] = "Contango" if gold_term_structure["spreads"].get("gc1_gc2", 0) < 0 else "Backwardation"
            
            if "analysis" in gold_term_structure:
                result["market_data"]["term_structure_implication"] = gold_term_structure["analysis"].get("implication", "N/A")
        else:
            logger.warning("Gold term structure data not available")
            result["market_data"]["error"] = "Data not available"
        
        # Get macroeconomic data (real rates, yield curve)
        real_rates = get_real_interest_rates()
        if real_rates:
            result["macroeconomic_data"]["real_rates"] = real_rates
            
            # Extract key metrics for easy access
            if "real_rates" in real_rates and "t10y" in real_rates["real_rates"]:
                result["macroeconomic_data"]["real_10y_rate"] = real_rates["real_rates"]["t10y"]
            
            if "analysis" in real_rates:
                result["macroeconomic_data"]["real_rates_implication"] = real_rates["analysis"].get("implication", "N/A")
        else:
            logger.warning("Real interest rates data not available")
            result["macroeconomic_data"]["real_rates_error"] = "Data not available"
        
        yield_curve = get_yield_curve()
        if yield_curve:
            result["macroeconomic_data"]["yield_curve"] = yield_curve
            
            # Extract key metrics for easy access
            if "spreads" in yield_curve:
                result["macroeconomic_data"]["10y_2y_spread"] = yield_curve["spreads"].get("t10y_t2y", "N/A")
            
            if "analysis" in yield_curve:
                result["macroeconomic_data"]["yield_curve_shape"] = yield_curve["analysis"].get("shape", "N/A")
                result["macroeconomic_data"]["recession_signal"] = yield_curve["analysis"].get("recession_signal", "N/A")
        else:
            logger.warning("Yield curve data not available")
            result["macroeconomic_data"]["yield_curve_error"] = "Data not available"
        
        # Get correlated analysis
        correlated_analysis = get_correlated_analysis()
        if correlated_analysis and "error" not in correlated_analysis:
            result["correlated_analysis"] = correlated_analysis
            
            # Extract key metrics for easy access
            if "analysis" in correlated_analysis:
                result["correlated_analysis"]["correlation_signal"] = correlated_analysis["analysis"].get("correlation_signal", "N/A")
                result["correlated_analysis"]["signal_explanation"] = correlated_analysis["analysis"].get("signal_explanation", "N/A")
        else:
            logger.warning("Correlated analysis not available")
            result["correlated_analysis"]["error"] = correlated_analysis.get("error", "Analysis not available")
        
        # Get divergence analysis
        divergence_analysis = get_market_divergence_analysis()
        if divergence_analysis and "error" not in divergence_analysis:
            result["divergence_analysis"] = divergence_analysis
            
            # Extract key metrics for easy access
            if "divergences" in divergence_analysis:
                result["divergence_analysis"]["divergences_detected"] = len(divergence_analysis["divergences"]) > 0
            
            if "analysis" in divergence_analysis:
                result["divergence_analysis"]["summary"] = divergence_analysis["analysis"].get("summary", "N/A")
                result["divergence_analysis"]["recommendation"] = divergence_analysis["analysis"].get("recommendation", "N/A")
        else:
            logger.warning("Divergence analysis not available")
            result["divergence_analysis"]["error"] = divergence_analysis.get("error", "Analysis not available")
        
        # Generate combined signals
        # Count bullish and bearish signals from all analyses
        bullish_signals = 0
        bearish_signals = 0
        neutral_signals = 0
        total_signals = 0
        
        # Market data signals
        if "term_structure_implication" in result["market_data"]:
            implication = result["market_data"]["term_structure_implication"].lower()
            if "bullish" in implication:
                bullish_signals += 1
            elif "bearish" in implication:
                bearish_signals += 1
            else:
                neutral_signals += 1
            total_signals += 1
        
        # Macroeconomic signals
        if "real_rates_implication" in result["macroeconomic_data"]:
            implication = result["macroeconomic_data"]["real_rates_implication"].lower()
            if "bullish" in implication or "positive" in implication:
                bullish_signals += 1
            elif "bearish" in implication or "negative" in implication:
                bearish_signals += 1
            else:
                neutral_signals += 1
            total_signals += 1
        
        # Correlated analysis signals
        if "correlation_signal" in result["correlated_analysis"]:
            signal = result["correlated_analysis"]["correlation_signal"].lower()
            if "bull" in signal:
                bullish_signals += 1
            elif "bear" in signal:
                bearish_signals += 1
            else:
                neutral_signals += 1
            total_signals += 1
        
        # Divergence analysis could indicate counter-trend opportunities
        if "divergences_detected" in result["divergence_analysis"] and result["divergence_analysis"]["divergences_detected"]:
            if "divergences" in result["divergence_analysis"] and "price_fundamentals" in result["divergence_analysis"]["divergences"]:
                divergence_type = result["divergence_analysis"]["divergences"]["price_fundamentals"]
                if divergence_type == "bearish_price_bullish_fundamentals":
                    bullish_signals += 1  # Potential buying opportunity
                elif divergence_type == "bullish_price_bearish_fundamentals":
                    bearish_signals += 1  # Potential selling opportunity
                total_signals += 1
        
        # Determine overall bias
        overall_bias = "Neutral"
        if bullish_signals > bearish_signals + neutral_signals:
            overall_bias = "Strongly Bullish"
        elif bullish_signals > bearish_signals:
            overall_bias = "Moderately Bullish"
        elif bearish_signals > bullish_signals + neutral_signals:
            overall_bias = "Strongly Bearish"
        elif bearish_signals > bullish_signals:
            overall_bias = "Moderately Bearish"
        
        # Add signal counts and overall bias to the result
        result["combined_signals"]["bullish_signals"] = bullish_signals
        result["combined_signals"]["bearish_signals"] = bearish_signals
        result["combined_signals"]["neutral_signals"] = neutral_signals
        result["combined_signals"]["total_signals"] = total_signals
        result["combined_signals"]["overall_bias"] = overall_bias
        
        # Add recommendation based on overall bias
        if "Strongly Bullish" in overall_bias:
            result["combined_signals"]["recommendation"] = "Strong buy signal for gold"
        elif "Moderately Bullish" in overall_bias:
            result["combined_signals"]["recommendation"] = "Buy signal for gold with proper risk management"
        elif "Strongly Bearish" in overall_bias:
            result["combined_signals"]["recommendation"] = "Strong sell signal for gold"
        elif "Moderately Bearish" in overall_bias:
            result["combined_signals"]["recommendation"] = "Sell signal for gold with proper risk management"
        else:
            result["combined_signals"]["recommendation"] = "Neutral signal, avoid new positions or maintain minimal exposure"
        
        return result
    except Exception as e:
        logger.error(f"Error in integrated dashboard: {str(e)}")
        result["error"] = str(e)
        return result