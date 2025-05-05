"""
Advanced Market Analysis Module
This module provides enhanced analysis of gold term structure and treasury yield curves,
with correlation metrics between them.
"""
import os
import logging
import datetime
from typing import Dict, List, Any, Optional, Union, Tuple
import time
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Import dependencies with fallback handling
try:
    import pandas as pd
    import numpy as np
    NUMERIC_LIBS_AVAILABLE = True
except ImportError:
    logger.warning("pandas/numpy not installed, some analysis features will be limited")
    NUMERIC_LIBS_AVAILABLE = False

# Import FRED API with fallback
try:
    from fredapi import Fred
    FRED_AVAILABLE = True
    FRED_API_KEY = os.environ.get("FRED_API_KEY")
    fred = Fred(api_key=FRED_API_KEY) if FRED_API_KEY else None
except ImportError:
    logger.warning("fredapi not installed, FRED data unavailable")
    FRED_AVAILABLE = False
    fred = None

# Import yfinance with fallback
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    logger.warning("yfinance not installed, market data functions will be limited")
    YFINANCE_AVAILABLE = False

# Try importing our other utility modules
try:
    from improved_market_data_utils import (
        get_price_with_retry,
        get_ticker_info_with_retry,
        get_price_history_with_retry,
        get_multiple_tickers_with_retry,
        get_gold_futures_chain
    )
    IMPROVED_MARKET_UTILS_AVAILABLE = True
except ImportError:
    logger.warning("improved_market_data_utils not available, using fallback methods")
    IMPROVED_MARKET_UTILS_AVAILABLE = False

try:
    from fred_data_utils import (
        get_real_interest_rates,
        get_yield_curve
    )
    FRED_UTILS_AVAILABLE = True
except ImportError:
    logger.warning("fred_data_utils not available, using direct FRED access")
    FRED_UTILS_AVAILABLE = False


def get_gold_spot_price() -> Optional[float]:
    """
    Get the current gold spot price
    
    Returns:
    - Float price or None if unavailable
    """
    # Try different methods to get gold spot price
    # XAU/USD is the gold spot price in USD
    if IMPROVED_MARKET_UTILS_AVAILABLE:
        price = get_price_with_retry("GC=F")  # Front month gold futures as proxy
        if price:
            return price
    
    if YFINANCE_AVAILABLE:
        try:
            # Try direct ticker for gold
            gold_ticker = yf.Ticker("GC=F")
            hist = gold_ticker.history(period="1d")
            if not hist.empty and "Close" in hist.columns:
                return float(hist["Close"].iloc[-1])
            
            # Try gold ETF as fallback
            gold_etf = yf.Ticker("GLD")
            hist = gold_etf.history(period="1d")
            if not hist.empty and "Close" in hist.columns:
                # GLD price is approximately 1/10 of gold price per oz
                return float(hist["Close"].iloc[-1]) * 10
        except Exception as e:
            logger.error(f"Error retrieving gold spot price: {str(e)}")
    
    # If all else fails, try FRED data
    if FRED_AVAILABLE and fred:
        try:
            # WGC gold price series from FRED
            gold_data = fred.get_series('GOLDPMGBD228NLBM')
            if not gold_data.empty:
                # Get the most recent price
                return float(gold_data.iloc[-1])
        except Exception as e:
            logger.error(f"Error retrieving gold price from FRED: {str(e)}")
    
    logger.warning("Could not retrieve gold spot price from any source")
    return None


def get_enhanced_gold_term_structure() -> Dict[str, Any]:
    """
    Enhanced analysis of gold futures term structure with spot price comparison,
    contango/backwardation metrics, and historical context
    
    Returns:
    - Dictionary with comprehensive gold term structure analysis
    """
    result = {
        "term_structure": {
            "curve_type": None,
            "contracts": {},
            "spreads": {},
        },
        "spot_futures_analysis": {
            "spot_price": None,
            "basis": None,
            "annualized_basis": None,
            "historical_context": {}
        },
        "market_cycle": {
            "current_state": None,
            "bull_threshold": None,
            "bear_threshold": None,
            "distance_to_threshold": None
        },
        "timestamp": str(datetime.now())
    }
    
    try:
        # Get spot price
        spot_price = get_gold_spot_price()
        if spot_price:
            result["spot_futures_analysis"]["spot_price"] = spot_price
        
        # Get futures data
        if IMPROVED_MARKET_UTILS_AVAILABLE:
            futures_chain = get_gold_futures_chain()
        else:
            futures_chain = {}
            if YFINANCE_AVAILABLE:
                # Fallback to basic yfinance if improved utils not available
                try:
                    # Try to get specific contract months
                    front_month = yf.Ticker("GC=F")
                    front_month_hist = front_month.history(period="1d")
                    if not front_month_hist.empty and "Close" in front_month_hist.columns:
                        price = float(front_month_hist["Close"].iloc[-1])
                        futures_chain["GC_front_price"] = price
                        
                        # Get contract info if available
                        try:
                            info = front_month.info
                            if "contractSymbol" in info:
                                futures_chain["GC_front_contract"] = info["contractSymbol"]
                        except:
                            pass
                except Exception as e:
                    logger.error(f"Error getting gold futures data: {str(e)}")
        
        # Current year and next year
        current_year = datetime.now().year % 100
        next_year = (datetime.now().year + 1) % 100
        
        # Month codes: F(Jan), G(Feb), H(Mar), J(Apr), K(May), M(Jun), N(Jul), Q(Aug), U(Sep), V(Oct), X(Nov), Z(Dec)
        month_codes = {
            1: "F", 2: "G", 3: "H", 4: "J", 5: "K", 6: "M",
            7: "N", 8: "Q", 9: "U", 10: "V", 11: "X", 12: "Z"
        }
        
        # Current month and future months
        current_month = datetime.now().month
        
        # Specific gold futures contract tickers to check
        contract_tickers = []
        
        # Add front month as GC=F
        contract_tickers.append("GC=F")
        
        # Add specific COMEX contracts for next few months
        for i in range(6):  # Current month and next 5 months
            month_idx = ((current_month - 1 + i) % 12) + 1
            year = current_year if month_idx >= current_month else next_year
            month_code = month_codes[month_idx]
            contract = f"GC{month_code}{year}.CMX"
            contract_tickers.append(contract)
        
        # Get prices for all tickers
        if IMPROVED_MARKET_UTILS_AVAILABLE:
            contract_prices = get_multiple_tickers_with_retry(contract_tickers)
        else:
            contract_prices = {}
            if YFINANCE_AVAILABLE:
                for ticker in contract_tickers:
                    try:
                        ticker_obj = yf.Ticker(ticker)
                        hist = ticker_obj.history(period="1d")
                        if not hist.empty and "Close" in hist.columns:
                            contract_prices[ticker] = float(hist["Close"].iloc[-1])
                    except Exception as e:
                        logger.error(f"Error retrieving price for {ticker}: {str(e)}")
        
        # Add contract prices to result
        if contract_prices:
            # Sort by price (usually descending for contango, ascending for backwardation)
            sorted_contracts = sorted(contract_prices.items(), key=lambda x: x[0])
            
            # Add each contract to the result
            for i, (ticker, price) in enumerate(sorted_contracts):
                if price is not None:
                    # Determine contract month
                    month_name = "Unknown"
                    if ticker == "GC=F":
                        month_name = "Front Month"
                        expiration = "Current"
                    elif len(ticker) >= 4 and ticker[2] in month_codes.values():
                        # Extract month code and year from ticker like GCM24.CMX
                        month_code = ticker[2]
                        month_idx = next((k for k, v in month_codes.items() if v == month_code), None)
                        if month_idx:
                            month_name = datetime(2000, month_idx, 1).strftime("%B")
                            # Extract year if possible
                            try:
                                year_code = ticker[3:5]
                                year = int("20" + year_code)
                                expiration = f"{month_name} {year}"
                            except:
                                expiration = month_name
                        else:
                            expiration = ticker
                    else:
                        expiration = ticker
                    
                    result["term_structure"]["contracts"][ticker] = {
                        "price": price,
                        "expiration": expiration,
                        "month_name": month_name
                    }
            
            # Calculate spreads between adjacent contracts
            contracts = list(result["term_structure"]["contracts"].items())
            for i in range(len(contracts) - 1):
                ticker1, data1 = contracts[i]
                ticker2, data2 = contracts[i+1]
                price1 = data1["price"]
                price2 = data2["price"]
                
                spread = price1 - price2
                spread_pct = (spread / price1) * 100
                
                # Annualize the spread for better comparison
                # Estimate months between contracts
                if ticker1 == "GC=F" and ticker2.startswith("GC") and len(ticker2) >= 4:
                    # Front month to specific month
                    current_month = datetime.now().month
                    month_code = ticker2[2]
                    month_idx = next((k for k, v in month_codes.items() if v == month_code), None)
                    
                    if month_idx:
                        # Calculate months difference
                        if month_idx < current_month:
                            # Next year
                            months_between = (12 - current_month) + month_idx
                        else:
                            months_between = month_idx - current_month
                        
                        # Ensure at least 1 month difference
                        months_between = max(1, months_between)
                        
                        # Annualized spread
                        annualized_spread_pct = (spread_pct / months_between) * 12
                    else:
                        months_between = 1
                        annualized_spread_pct = spread_pct * 12
                else:
                    # Default to 1 month difference
                    months_between = 1
                    annualized_spread_pct = spread_pct * 12
                
                result["term_structure"]["spreads"][f"{ticker1}_{ticker2}"] = {
                    "spread_dollars": round(spread, 2),
                    "spread_percent": round(spread_pct, 3),
                    "annualized_spread_percent": round(annualized_spread_pct, 3),
                    "estimated_months_between": months_between
                }
            
            # Determine curve type (contango vs backwardation)
            front_prices = [data["price"] for ticker, data in contracts[:3]]
            if len(front_prices) >= 2:
                if front_prices[0] < front_prices[1]:
                    if len(front_prices) >= 3 and front_prices[1] < front_prices[2]:
                        result["term_structure"]["curve_type"] = "Contango (upward sloping curve)"
                    else:
                        result["term_structure"]["curve_type"] = "Partial Contango (mixed curve)"
                elif front_prices[0] > front_prices[1]:
                    if len(front_prices) >= 3 and front_prices[1] > front_prices[2]:
                        result["term_structure"]["curve_type"] = "Backwardation (downward sloping curve)"
                    else:
                        result["term_structure"]["curve_type"] = "Partial Backwardation (mixed curve)"
                else:
                    result["term_structure"]["curve_type"] = "Flat"
            
            # Calculate basis between spot and front month
            if spot_price and "GC=F" in contract_prices:
                front_price = contract_prices["GC=F"]
                basis = front_price - spot_price
                basis_pct = (basis / spot_price) * 100
                
                # Estimate months to front month expiration (typically 1-2 months)
                # Get current month and day to estimate time to expiration
                current_day = datetime.now().day
                months_to_expiration = 1 if current_day < 20 else 2
                
                # Annualized basis
                annualized_basis_pct = (basis_pct / months_to_expiration) * 12
                
                result["spot_futures_analysis"]["basis"] = round(basis, 2)
                result["spot_futures_analysis"]["basis_percent"] = round(basis_pct, 3)
                result["spot_futures_analysis"]["annualized_basis"] = round(annualized_basis_pct, 3)
                
                # Add interpretation of basis
                if basis > 0:
                    result["spot_futures_analysis"]["basis_interpretation"] = "Positive (futures premium over spot)"
                    
                    # Typical cost of carry situation
                    if 0 < annualized_basis_pct < 5:
                        result["spot_futures_analysis"]["market_condition"] = "Normal cost of carry premium"
                    elif annualized_basis_pct >= 5:
                        result["spot_futures_analysis"]["market_condition"] = "Elevated futures premium, potential bullish sentiment"
                else:
                    result["spot_futures_analysis"]["basis_interpretation"] = "Negative (spot premium over futures)"
                    result["spot_futures_analysis"]["market_condition"] = "Backwardation, potential physical supply constraints"
        
        # Add market cycle analysis
        # Historical thresholds based on gold price behavior
        # These would ideally be calculated from historical data analysis
        current_price = spot_price
        if not current_price and "GC=F" in contract_prices:
            current_price = contract_prices["GC=F"]
        
        if current_price:
            # Example thresholds (should be refined based on actual historical data)
            # Bullish threshold: 10% above 200-day moving average
            # Bearish threshold: 10% below 200-day moving average
            
            # Get historical price data for 200-day MA
            ma_200 = None
            if IMPROVED_MARKET_UTILS_AVAILABLE:
                hist_data = get_price_history_with_retry("GC=F", period="1y", interval="1d")
                if hist_data is not None and not hist_data.empty and "Close" in hist_data.columns:
                    ma_200 = hist_data["Close"].rolling(window=200).mean().iloc[-1]
            elif YFINANCE_AVAILABLE:
                try:
                    hist_data = yf.download("GC=F", period="1y", progress=False)
                    if not hist_data.empty and "Close" in hist_data.columns:
                        ma_200 = hist_data["Close"].rolling(window=200).mean().iloc[-1]
                except Exception as e:
                    logger.error(f"Error calculating moving average: {str(e)}")
            
            if ma_200:
                bull_threshold = ma_200 * 1.1  # 10% above 200d MA
                bear_threshold = ma_200 * 0.9  # 10% below 200d MA
                
                result["market_cycle"]["bull_threshold"] = round(bull_threshold, 2)
                result["market_cycle"]["bear_threshold"] = round(bear_threshold, 2)
                result["market_cycle"]["ma_200"] = round(ma_200, 2)
                
                # Determine current market state
                if current_price > bull_threshold:
                    result["market_cycle"]["current_state"] = "Strong Bull Market"
                    result["market_cycle"]["distance_to_threshold"] = round(current_price - bull_threshold, 2)
                elif current_price < bear_threshold:
                    result["market_cycle"]["current_state"] = "Bear Market"
                    result["market_cycle"]["distance_to_threshold"] = round(bear_threshold - current_price, 2)
                else:
                    # Between thresholds
                    if current_price > ma_200:
                        result["market_cycle"]["current_state"] = "Moderate Bull Market"
                        result["market_cycle"]["distance_to_threshold"] = round(bull_threshold - current_price, 2)
                    else:
                        result["market_cycle"]["current_state"] = "Weakening Market"
                        result["market_cycle"]["distance_to_threshold"] = round(current_price - bear_threshold, 2)
                
                # Add percentage to threshold
                if result["market_cycle"]["distance_to_threshold"] and current_price:
                    result["market_cycle"]["percent_to_threshold"] = round((result["market_cycle"]["distance_to_threshold"] / current_price) * 100, 2)
        
        return result
    except Exception as e:
        logger.error(f"Error in enhanced gold term structure analysis: {str(e)}")
        return {
            "error": str(e),
            "timestamp": str(datetime.now())
        }


def get_treasury_yield_curve() -> Dict[str, Any]:
    """
    Get detailed Treasury yield curve data with analysis
    
    Returns:
    - Dictionary with yield curve data and analysis
    """
    result = {
        "yields": {},
        "spreads": {},
        "curve_shape": None,
        "inversion_status": None,
        "historical_context": {},
        "gold_implications": {},
        "timestamp": str(datetime.now())
    }
    
    try:
        # Use yield curve function from fred_data_utils if available
        if FRED_UTILS_AVAILABLE:
            yield_curve_data = get_yield_curve()
            if yield_curve_data:
                return yield_curve_data
        
        # Direct FRED API implementation if FRED_UTILS not available
        if not FRED_AVAILABLE or not fred:
            logger.error("FRED API not available, cannot retrieve yield curve data")
            result["error"] = "FRED API not available"
            return result
        
        # Treasury maturity series IDs
        maturities = {
            "3m": "DGS3MO",  # 3-Month Treasury Constant Maturity Rate
            "6m": "DGS6MO",  # 6-Month Treasury Constant Maturity Rate
            "1y": "DGS1",    # 1-Year Treasury Constant Maturity Rate
            "2y": "DGS2",    # 2-Year Treasury Constant Maturity Rate
            "3y": "DGS3",    # 3-Year Treasury Constant Maturity Rate
            "5y": "DGS5",    # 5-Year Treasury Constant Maturity Rate
            "7y": "DGS7",    # 7-Year Treasury Constant Maturity Rate
            "10y": "DGS10",  # 10-Year Treasury Constant Maturity Rate
            "20y": "DGS20",  # 20-Year Treasury Constant Maturity Rate
            "30y": "DGS30"   # 30-Year Treasury Constant Maturity Rate
        }
        
        # Get all yield data
        for key, series_id in maturities.items():
            try:
                data = fred.get_series(series_id)
                if not data.empty:
                    latest_value = data.iloc[-1]
                    if not pd.isna(latest_value):
                        result["yields"][key] = {
                            "value": round(float(latest_value), 3),
                            "series_id": series_id,
                            "maturity": key
                        }
            except Exception as e:
                logger.error(f"Error retrieving yield for {key} ({series_id}): {str(e)}")
        
        # Calculate key spreads
        if "10y" in result["yields"] and "2y" in result["yields"]:
            # 10-year minus 2-year (most watched for recession signals)
            spread_10y_2y = result["yields"]["10y"]["value"] - result["yields"]["2y"]["value"]
            result["spreads"]["10y_2y"] = {
                "value": round(spread_10y_2y, 3),
                "name": "10-Year minus 2-Year",
                "recession_indicator": True
            }
            
            # Check for inversion
            if spread_10y_2y < 0:
                result["spreads"]["10y_2y"]["status"] = "Inverted"
                result["spreads"]["10y_2y"]["interpretation"] = "Yield curve inversion signals increased recession risk"
            else:
                result["spreads"]["10y_2y"]["status"] = "Normal"
                result["spreads"]["10y_2y"]["interpretation"] = "Positive spread indicates normal economic expectations"
        
        if "10y" in result["yields"] and "3m" in result["yields"]:
            # 10-year minus 3-month (also watched for recession signals)
            spread_10y_3m = result["yields"]["10y"]["value"] - result["yields"]["3m"]["value"]
            result["spreads"]["10y_3m"] = {
                "value": round(spread_10y_3m, 3),
                "name": "10-Year minus 3-Month",
                "recession_indicator": True
            }
            
            # Check for inversion
            if spread_10y_3m < 0:
                result["spreads"]["10y_3m"]["status"] = "Inverted"
                result["spreads"]["10y_3m"]["interpretation"] = "Yield curve inversion signals increased recession risk"
            else:
                result["spreads"]["10y_3m"]["status"] = "Normal"
                result["spreads"]["10y_3m"]["interpretation"] = "Positive spread indicates normal economic expectations"
        
        if "30y" in result["yields"] and "5y" in result["yields"]:
            # 30-year minus 5-year (long-term expectations)
            spread_30y_5y = result["yields"]["30y"]["value"] - result["yields"]["5y"]["value"]
            result["spreads"]["30y_5y"] = {
                "value": round(spread_30y_5y, 3),
                "name": "30-Year minus 5-Year",
                "recession_indicator": False
            }
        
        # Determine curve shape
        if len(result["yields"]) >= 3:
            # Check if short-term, mid-term, and long-term rates are available
            has_short = any(k in result["yields"] for k in ["3m", "6m", "1y"])
            has_mid = any(k in result["yields"] for k in ["2y", "3y", "5y", "7y"])
            has_long = any(k in result["yields"] for k in ["10y", "20y", "30y"])
            
            if has_short and has_mid and has_long:
                # Get representative rates for each segment
                short_rate = next(result["yields"][k]["value"] for k in ["3m", "6m", "1y"] if k in result["yields"])
                mid_rate = next(result["yields"][k]["value"] for k in ["2y", "3y", "5y", "7y"] if k in result["yields"])
                long_rate = next(result["yields"][k]["value"] for k in ["10y", "20y", "30y"] if k in result["yields"])
                
                # Determine curve shape
                if short_rate < mid_rate < long_rate:
                    result["curve_shape"] = "Normal (upward sloping)"
                elif short_rate > mid_rate > long_rate:
                    result["curve_shape"] = "Inverted (downward sloping)"
                elif short_rate < mid_rate > long_rate:
                    result["curve_shape"] = "Humped (mid-rates highest)"
                elif short_rate > mid_rate < long_rate:
                    result["curve_shape"] = "Bowl-shaped (mid-rates lowest)"
                else:
                    result["curve_shape"] = "Flat or mixed"
        
        # Check for inversions
        inversions = [k for k, v in result["spreads"].items() if v.get("value", 0) < 0]
        if inversions:
            result["inversion_status"] = f"Inverted at: {', '.join(inversions)}"
            
            # Check if recession-indicating spreads are inverted
            recession_signals = [k for k, v in result["spreads"].items() 
                              if v.get("value", 0) < 0 and v.get("recession_indicator", False)]
            
            if recession_signals:
                result["recession_signal"] = "Warning: Yield curve indicates elevated recession risk"
            else:
                result["recession_signal"] = "No clear recession signal from key yield curve indicators"
        else:
            result["inversion_status"] = "No inversions detected"
            result["recession_signal"] = "Normal yield curve suggests lower recession risk"
        
        # Implications for gold
        # Historical relationship: Gold often performs well during yield curve inversions
        # and when real rates (especially short-term) are low or negative
        
        # Gold tends to perform well when:
        # 1. Yield curve is inverted (flight to safety)
        # 2. Real interest rates are negative
        # 3. Long-term yields are declining (economic concern)
        
        gold_bullish_factors = 0
        gold_bearish_factors = 0
        
        # Factor 1: Yield curve inversion
        if inversions:
            result["gold_implications"]["yield_curve"] = "Bullish for gold (inverted yield curve often precedes economic weakness)"
            gold_bullish_factors += 1
        else:
            result["gold_implications"]["yield_curve"] = "Neutral to bearish for gold (normal yield curve suggests economic growth)"
            gold_bearish_factors += 1
        
        # Factor 2: Real interest rates
        # Try to get inflation expectations to calculate real rates
        if "10y" in result["yields"]:
            nominal_10y = result["yields"]["10y"]["value"]
            
            # Try to get 10-year inflation expectations
            try:
                # 10-Year Breakeven Inflation Rate
                inflation_exp_10y = fred.get_series('T10YIE')
                if not inflation_exp_10y.empty:
                    latest_inflation_exp = inflation_exp_10y.iloc[-1]
                    if not pd.isna(latest_inflation_exp):
                        # Make sure we're working with numeric values
                        if isinstance(nominal_10y, (int, float)) and isinstance(latest_inflation_exp, (int, float)):
                            real_10y = nominal_10y - latest_inflation_exp
                            result["gold_implications"]["real_10y_rate"] = round(real_10y, 3)
                        
                            if real_10y < 0:
                                result["gold_implications"]["real_rates"] = "Bullish for gold (negative real 10-year yield)"
                                gold_bullish_factors += 1
                            elif real_10y < 1:
                                result["gold_implications"]["real_rates"] = "Moderately bullish for gold (low positive real 10-year yield)"
                                gold_bullish_factors += 1
                            else:
                                result["gold_implications"]["real_rates"] = "Bearish for gold (positive real 10-year yield above 1%)"
                                gold_bearish_factors += 1
            except Exception as e:
                logger.error(f"Error calculating real rates: {str(e)}")
        
        # Factor 3: Trend in long-term yields
        try:
            if "10y" in result["yields"]:
                # Get 10-year yield from 6 months ago
                end_date = datetime.now()
                start_date = end_date - timedelta(days=180)
                
                # Get the data
                hist_10y = fred.get_series('DGS10', start_date, end_date)
                if len(hist_10y) >= 2:
                    first_value = hist_10y.iloc[0]
                    last_value = hist_10y.iloc[-1]
                    
                    if not pd.isna(first_value) and not pd.isna(last_value):
                        change_10y = last_value - first_value
                        result["gold_implications"]["10y_yield_trend"] = round(change_10y, 3)
                        
                        if change_10y < -0.5:
                            result["gold_implications"]["yield_trend"] = "Bullish for gold (significant decline in 10-year yield)"
                            gold_bullish_factors += 1
                        elif change_10y < 0:
                            result["gold_implications"]["yield_trend"] = "Mildly bullish for gold (modest decline in 10-year yield)"
                            gold_bullish_factors += 1
                        elif change_10y > 1:
                            result["gold_implications"]["yield_trend"] = "Bearish for gold (sharp rise in 10-year yield)"
                            gold_bearish_factors += 1
                        elif change_10y > 0:
                            result["gold_implications"]["yield_trend"] = "Mildly bearish for gold (modest rise in 10-year yield)"
                            gold_bearish_factors += 1
        except Exception as e:
            logger.error(f"Error analyzing yield trend: {str(e)}")
        
        # Overall gold outlook based on treasury factors
        total_factors = gold_bullish_factors + gold_bearish_factors
        if total_factors > 0:
            bullish_percentage = (gold_bullish_factors / total_factors) * 100
            
            if bullish_percentage >= 75:
                result["gold_implications"]["overall_outlook"] = "Strongly bullish for gold based on treasury factors"
            elif bullish_percentage >= 50:
                result["gold_implications"]["overall_outlook"] = "Moderately bullish for gold based on treasury factors"
            elif bullish_percentage >= 25:
                result["gold_implications"]["overall_outlook"] = "Moderately bearish for gold based on treasury factors"
            else:
                result["gold_implications"]["overall_outlook"] = "Strongly bearish for gold based on treasury factors"
            
            result["gold_implications"]["bullish_factors"] = gold_bullish_factors
            result["gold_implications"]["bearish_factors"] = gold_bearish_factors
            result["gold_implications"]["total_factors"] = total_factors
        
        return result
    except Exception as e:
        logger.error(f"Error in treasury yield curve analysis: {str(e)}")
        return {
            "error": str(e),
            "timestamp": str(datetime.now())
        }


def get_gold_real_rates_correlation() -> Dict[str, Any]:
    """
    Analyze the correlation between gold prices and real interest rates
    
    Returns:
    - Dictionary with correlation data and analysis
    """
    result = {
        "gold_prices": {},
        "real_rates": {},
        "correlation": {},
        "analysis": {},
        "timestamp": str(datetime.now())
    }
    
    try:
        # Check if we have required libraries
        if not NUMERIC_LIBS_AVAILABLE:
            result["error"] = "Required libraries (pandas/numpy) not available"
            return result
        
        if not FRED_AVAILABLE or not fred:
            result["error"] = "FRED API not available"
            return result
        
        # Time period for analysis
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)  # Last year of data
        
        # Get gold price data from FRED
        try:
            # London Bullion Market Association Gold Price (USD per Troy Ounce)
            gold_data = fred.get_series('GOLDPMGBD228NLBM', start_date, end_date)
            if not gold_data.empty:
                # Store current and historical gold prices
                result["gold_prices"]["current"] = float(gold_data.iloc[-1])
                result["gold_prices"]["year_ago"] = float(gold_data.iloc[0])
                result["gold_prices"]["year_change"] = round(float(gold_data.iloc[-1]) - float(gold_data.iloc[0]), 2)
                result["gold_prices"]["year_change_pct"] = round((float(gold_data.iloc[-1]) / float(gold_data.iloc[0]) - 1) * 100, 2)
        except Exception as e:
            logger.error(f"Error retrieving gold price data: {str(e)}")
            result["gold_prices"]["error"] = str(e)
        
        # Get 10-year real interest rate data
        try:
            # 10-Year Treasury Inflation-Indexed Security, Constant Maturity (DFII10)
            real_rates_data = fred.get_series('DFII10', start_date, end_date)
            if not real_rates_data.empty:
                # Store current and historical real rates
                result["real_rates"]["current"] = float(real_rates_data.iloc[-1])
                result["real_rates"]["year_ago"] = float(real_rates_data.iloc[0])
                result["real_rates"]["year_change"] = round(float(real_rates_data.iloc[-1]) - float(real_rates_data.iloc[0]), 2)
        except Exception as e:
            logger.error(f"Error retrieving real interest rate data: {str(e)}")
            result["real_rates"]["error"] = str(e)
        
        # Calculate correlation if we have both datasets
        if "error" not in result["gold_prices"] and "error" not in result["real_rates"]:
            # Align the datasets
            aligned_data = pd.concat([gold_data, real_rates_data], axis=1, join='inner')
            aligned_data.columns = ['gold', 'real_rate']
            
            # Clean any missing values
            aligned_data = aligned_data.dropna()
            
            if len(aligned_data) >= 30:  # Enough data points for correlation
                # Calculate correlation
                correlation = aligned_data['gold'].corr(aligned_data['real_rate'])
                result["correlation"]["value"] = round(correlation, 3)
                
                # Interpret the correlation
                if correlation <= -0.7:
                    result["correlation"]["strength"] = "Strong negative"
                    result["correlation"]["interpretation"] = "Gold price strongly moves in opposite direction to real rates"
                elif correlation <= -0.3:
                    result["correlation"]["strength"] = "Moderate negative"
                    result["correlation"]["interpretation"] = "Gold price moderately moves in opposite direction to real rates"
                elif correlation < 0:
                    result["correlation"]["strength"] = "Weak negative"
                    result["correlation"]["interpretation"] = "Gold price weakly moves in opposite direction to real rates"
                elif correlation < 0.3:
                    result["correlation"]["strength"] = "Weak positive"
                    result["correlation"]["interpretation"] = "Gold price weakly moves in same direction as real rates"
                elif correlation < 0.7:
                    result["correlation"]["strength"] = "Moderate positive"
                    result["correlation"]["interpretation"] = "Gold price moderately moves in same direction as real rates"
                else:
                    result["correlation"]["strength"] = "Strong positive"
                    result["correlation"]["interpretation"] = "Gold price strongly moves in same direction as real rates"
                
                # Analyze the implication
                if correlation < 0:
                    result["correlation"]["typical_relationship"] = "Normal (negative correlation is typical historically)"
                else:
                    result["correlation"]["typical_relationship"] = "Unusual (positive correlation is atypical historically)"
                
                # Calculate 3-month rolling correlation to see if relationship is changing
                if len(aligned_data) >= 90:  # At least 3 months of data
                    rolling_corr = aligned_data['gold'].rolling(window=60).corr(aligned_data['real_rate'])
                    recent_corr = rolling_corr.iloc[-1]
                    earlier_corr = rolling_corr.iloc[-60] if len(rolling_corr) >= 120 else rolling_corr.iloc[60]
                    
                    if not pd.isna(recent_corr) and not pd.isna(earlier_corr):
                        corr_change = recent_corr - earlier_corr
                        result["correlation"]["recent_change"] = round(corr_change, 3)
                        
                        if abs(corr_change) > 0.3:
                            if corr_change > 0:
                                result["correlation"]["trend"] = "Correlation becoming significantly more positive"
                            else:
                                result["correlation"]["trend"] = "Correlation becoming significantly more negative"
                        elif abs(corr_change) > 0.1:
                            if corr_change > 0:
                                result["correlation"]["trend"] = "Correlation becoming somewhat more positive"
                            else:
                                result["correlation"]["trend"] = "Correlation becoming somewhat more negative"
                        else:
                            result["correlation"]["trend"] = "Correlation relationship stable"
        
        # Add analysis based on current real rate level and gold price movement
        if "current" in result["real_rates"] and "year_change_pct" in result["gold_prices"]:
            current_real_rate = result["real_rates"]["current"]
            gold_year_change_pct = result["gold_prices"]["year_change_pct"]
            
            # Analysis based on real rate level
            if current_real_rate < 0:
                result["analysis"]["real_rate_level"] = "Negative real rates (typically bullish for gold)"
                
                if gold_year_change_pct > 0:
                    result["analysis"]["price_alignment"] = "Aligned with theory: Gold price rising during negative real rates"
                else:
                    result["analysis"]["price_alignment"] = "Divergent from theory: Gold price falling despite negative real rates"
            elif current_real_rate < 1:
                result["analysis"]["real_rate_level"] = "Low positive real rates (moderately supportive for gold)"
                
                if gold_year_change_pct > 0:
                    result["analysis"]["price_alignment"] = "Aligned with theory: Gold price rising during low real rates"
                else:
                    result["analysis"]["price_alignment"] = "Somewhat divergent: Gold price falling despite low real rates"
            else:
                result["analysis"]["real_rate_level"] = "High positive real rates (typically bearish for gold)"
                
                if gold_year_change_pct < 0:
                    result["analysis"]["price_alignment"] = "Aligned with theory: Gold price falling during high real rates"
                else:
                    result["analysis"]["price_alignment"] = "Divergent from theory: Gold price rising despite high real rates"
            
            # Add change in real rates analysis
            if "year_change" in result["real_rates"]:
                real_rate_change = result["real_rates"]["year_change"]
                
                if real_rate_change < -0.5:
                    result["analysis"]["real_rate_trend"] = "Significantly falling real rates (bullish for gold)"
                elif real_rate_change < 0:
                    result["analysis"]["real_rate_trend"] = "Moderately falling real rates (somewhat bullish for gold)"
                elif real_rate_change < 0.5:
                    result["analysis"]["real_rate_trend"] = "Moderately rising real rates (somewhat bearish for gold)"
                else:
                    result["analysis"]["real_rate_trend"] = "Significantly rising real rates (bearish for gold)"
        
        return result
    except Exception as e:
        logger.error(f"Error analyzing gold-real rates correlation: {str(e)}")
        return {
            "error": str(e),
            "timestamp": str(datetime.now())
        }


def get_integrated_gold_analysis() -> Dict[str, Any]:
    """
    Comprehensive gold market analysis integrating term structure, real rates,
    and treasury yield curve data
    
    Returns:
    - Dictionary with integrated analysis
    """
    result = {
        "term_structure": {},
        "yield_curve": {},
        "real_rates_correlation": {},
        "integrated_signals": {},
        "timestamp": str(datetime.now())
    }
    
    try:
        # Get individual analyses
        gold_term_structure = get_enhanced_gold_term_structure()
        treasury_curve = get_treasury_yield_curve()
        gold_real_rates = get_gold_real_rates_correlation()
        
        # Add individual analyses to result
        result["term_structure"] = gold_term_structure
        result["yield_curve"] = treasury_curve
        result["real_rates_correlation"] = gold_real_rates
        
        # Create integrated signals
        bullish_signals = 0
        bearish_signals = 0
        neutral_signals = 0
        
        # 1. Analyze gold term structure signals
        if "curve_type" in gold_term_structure.get("term_structure", {}):
            curve_type = gold_term_structure["term_structure"]["curve_type"]
            
            if "Backwardation" in curve_type:
                result["integrated_signals"]["term_structure"] = "Bullish: Backwardation indicates strong immediate demand"
                bullish_signals += 1
            elif "Contango" in curve_type:
                # Check if steep or normal contango
                if "Steep" in curve_type:
                    result["integrated_signals"]["term_structure"] = "Bearish: Steep contango indicates weak immediate demand"
                    bearish_signals += 1
                else:
                    result["integrated_signals"]["term_structure"] = "Neutral: Normal contango is typical for gold markets"
                    neutral_signals += 1
        
        # 2. Analyze market cycle signal
        if "current_state" in gold_term_structure.get("market_cycle", {}):
            state = gold_term_structure["market_cycle"]["current_state"]
            
            if "Strong Bull" in state:
                result["integrated_signals"]["market_cycle"] = "Bullish: Strong bull market conditions"
                bullish_signals += 1
            elif "Moderate Bull" in state:
                result["integrated_signals"]["market_cycle"] = "Moderately Bullish: Positive trend but below strong bull threshold"
                bullish_signals += 1
            elif "Bear" in state:
                result["integrated_signals"]["market_cycle"] = "Bearish: Bear market conditions"
                bearish_signals += 1
            elif "Weakening" in state:
                result["integrated_signals"]["market_cycle"] = "Moderately Bearish: Weakening trend"
                bearish_signals += 1
        
        # 3. Analyze spot-futures relationship
        if "basis_interpretation" in gold_term_structure.get("spot_futures_analysis", {}):
            basis = gold_term_structure["spot_futures_analysis"]["basis_interpretation"]
            
            if "Negative" in basis:
                # Backwardation in spot-futures relationship
                result["integrated_signals"]["spot_futures"] = "Bullish: Spot premium indicates strong immediate demand"
                bullish_signals += 1
            elif "Positive" in basis:
                # Check for excessive contango
                if "annualized_basis" in gold_term_structure["spot_futures_analysis"]:
                    ann_basis = gold_term_structure["spot_futures_analysis"]["annualized_basis"]
                    
                    if ann_basis > 5:
                        result["integrated_signals"]["spot_futures"] = "Bearish: Excessive futures premium"
                        bearish_signals += 1
                    else:
                        result["integrated_signals"]["spot_futures"] = "Neutral: Normal futures premium"
                        neutral_signals += 1
        
        # 4. Analyze yield curve signals
        if "gold_implications" in treasury_curve and "overall_outlook" in treasury_curve["gold_implications"]:
            outlook = treasury_curve["gold_implications"]["overall_outlook"]
            
            if "Strongly bullish" in outlook:
                result["integrated_signals"]["treasury_curve"] = "Bullish: Treasury curve strongly supports gold"
                bullish_signals += 1
            elif "Moderately bullish" in outlook:
                result["integrated_signals"]["treasury_curve"] = "Moderately Bullish: Treasury curve moderately supports gold"
                bullish_signals += 1
            elif "Moderately bearish" in outlook:
                result["integrated_signals"]["treasury_curve"] = "Moderately Bearish: Treasury curve moderately negative for gold"
                bearish_signals += 1
            elif "Strongly bearish" in outlook:
                result["integrated_signals"]["treasury_curve"] = "Bearish: Treasury curve strongly negative for gold"
                bearish_signals += 1
        
        # 5. Analyze real rates signals
        if "analysis" in gold_real_rates and "real_rate_level" in gold_real_rates["analysis"]:
            real_rate_level = gold_real_rates["analysis"]["real_rate_level"]
            
            if "Negative" in real_rate_level:
                result["integrated_signals"]["real_rates"] = "Bullish: Negative real rates support gold"
                bullish_signals += 1
            elif "Low positive" in real_rate_level:
                result["integrated_signals"]["real_rates"] = "Moderately Bullish: Low positive real rates somewhat support gold"
                bullish_signals += 1
            elif "High positive" in real_rate_level:
                result["integrated_signals"]["real_rates"] = "Bearish: High positive real rates pressure gold"
                bearish_signals += 1
        
        # 6. Add real rate trend signal
        if "analysis" in gold_real_rates and "real_rate_trend" in gold_real_rates["analysis"]:
            trend = gold_real_rates["analysis"]["real_rate_trend"]
            
            if "falling" in trend:
                if "Significantly" in trend:
                    result["integrated_signals"]["real_rate_trend"] = "Bullish: Significantly falling real rates"
                    bullish_signals += 1
                else:
                    result["integrated_signals"]["real_rate_trend"] = "Moderately Bullish: Moderately falling real rates"
                    bullish_signals += 1
            elif "rising" in trend:
                if "Significantly" in trend:
                    result["integrated_signals"]["real_rate_trend"] = "Bearish: Significantly rising real rates"
                    bearish_signals += 1
                else:
                    result["integrated_signals"]["real_rate_trend"] = "Moderately Bearish: Moderately rising real rates"
                    bearish_signals += 1
        
        # Calculate overall signal
        total_signals = bullish_signals + bearish_signals + neutral_signals
        
        if total_signals > 0:
            result["integrated_signals"]["bullish_count"] = bullish_signals
            result["integrated_signals"]["bearish_count"] = bearish_signals
            result["integrated_signals"]["neutral_count"] = neutral_signals
            result["integrated_signals"]["total_count"] = total_signals
            
            bullish_pct = (bullish_signals / total_signals) * 100
            bearish_pct = (bearish_signals / total_signals) * 100
            
            # Determine overall bias
            if bullish_pct >= 70:
                result["integrated_signals"]["overall_bias"] = "Strongly Bullish"
            elif bullish_pct >= 50:
                result["integrated_signals"]["overall_bias"] = "Moderately Bullish"
            elif bearish_pct >= 70:
                result["integrated_signals"]["overall_bias"] = "Strongly Bearish"
            elif bearish_pct >= 50:
                result["integrated_signals"]["overall_bias"] = "Moderately Bearish"
            else:
                result["integrated_signals"]["overall_bias"] = "Neutral"
            
            # Add recommendation based on overall bias
            bias = result["integrated_signals"]["overall_bias"]
            
            if "Strongly Bullish" in bias:
                result["integrated_signals"]["recommendation"] = "Consider overweight allocation to gold with medium to long-term horizon"
            elif "Moderately Bullish" in bias:
                result["integrated_signals"]["recommendation"] = "Consider moderate allocation to gold with medium-term horizon"
            elif "Neutral" in bias:
                result["integrated_signals"]["recommendation"] = "Maintain existing gold allocations; no strong signal for change"
            elif "Moderately Bearish" in bias:
                result["integrated_signals"]["recommendation"] = "Consider reducing gold exposure or implementing hedging strategies"
            elif "Strongly Bearish" in bias:
                result["integrated_signals"]["recommendation"] = "Consider underweight allocation to gold until conditions improve"
        
        return result
    except Exception as e:
        logger.error(f"Error in integrated gold analysis: {str(e)}")
        return {
            "error": str(e),
            "timestamp": str(datetime.now())
        }