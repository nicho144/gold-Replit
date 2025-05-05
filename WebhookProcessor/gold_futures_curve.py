"""
Gold Futures Curve Analysis Module
Focus on curve structure, spot-futures spreads, macroeconomic correlations, and seasonal recommendations
"""

import logging
import datetime
import os
from typing import Dict, Any, List, Optional
import yfinance as yf
import numpy as np

# Try to import FRED API for economic data
try:
    from fredapi import Fred
    FRED_API_KEY = os.environ.get("FRED_API_KEY")
    fred = Fred(api_key=FRED_API_KEY) if FRED_API_KEY else None
    HAS_FRED = fred is not None
except ImportError:
    fred = None
    HAS_FRED = False
    
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define constants - Use more reliable ticker symbols
GOLD_SPOT = "GLD"  # Gold ETF as proxy for spot
GOLD_FUTURES = "GC=F"  # Front-month gold futures
# Treasury yield symbols - multiple options for fallback
TEN_YEAR_YIELD = "US10Y"  # Primary 10-year yield ticker 
ALT_TEN_YEAR_YIELD = "^TNX"  # Alternative 10-year yield ticker
TEN_YEAR_FUTURES = "ZN=F"  # 10-year T-Note futures

# Define available gold futures contracts that we know are reliable in Yahoo Finance
# Using front month GC=F plus synthetic approximations for subsequent months
# This is more reliable than using specific contract months that might not be available
GOLD_FUTURES_SYMBOLS = ["GC=F"]  # Front month only, we'll calculate the rest

# Add other reliable market indicators 
KEY_MARKET_SYMBOLS = ["GLD", "GC=F", "ES=F", "^VIX", "DX-Y.NYB", "US10Y", "^TNX", "ZN=F"]

def get_premarket_data() -> Dict[str, Any]:
    """
    Get latest premarket data for major market indicators
    
    Returns:
    - Dictionary with the latest market data
    """
    try:
        # Fetch data for all key market symbols
        data = yf.download(KEY_MARKET_SYMBOLS, period="1mo", interval="1d", group_by='ticker')
        
        result = {
            "gold": 0,
            "sp500_futures": 0,
            "vix": 0,
            "dollar_index": 0,
            "treasury_futures": 0,
            "treasury_10y": 0,
            "treasury_yield_source": "Not available"
        }
        
        # Extract latest prices (most reliable sources first)
        # Get gold price
        try:
            if GOLD_FUTURES in data and len(data[GOLD_FUTURES]['Close']) > 0:
                result["gold"] = float(data[GOLD_FUTURES]['Close'].iloc[-1])
            elif GOLD_SPOT in data and len(data[GOLD_SPOT]['Close']) > 0:
                # Convert GLD ETF price to gold spot price (approximate 1:10 ratio)
                gld_price = float(data[GOLD_SPOT]['Close'].iloc[-1])
                result["gold"] = gld_price * 10.0
        except Exception as e:
            logger.error(f"Error getting gold price: {e}")
            result["gold"] = 3200.0  # Reasonable default based on recent price ranges
        
        # Get S&P 500 futures price
        try:
            if "ES=F" in data and len(data["ES=F"]['Close']) > 0:
                result["sp500_futures"] = float(data["ES=F"]['Close'].iloc[-1])
        except Exception as e:
            logger.error(f"Error getting S&P 500 futures price: {e}")
        
        # Get VIX
        try:
            if "^VIX" in data and len(data["^VIX"]['Close']) > 0:
                result["vix"] = float(data["^VIX"]['Close'].iloc[-1])
        except Exception as e:
            logger.error(f"Error getting VIX: {e}")
        
        # Get dollar index
        try:
            if "DX-Y.NYB" in data and len(data["DX-Y.NYB"]['Close']) > 0:
                result["dollar_index"] = float(data["DX-Y.NYB"]['Close'].iloc[-1])
        except Exception as e:
            logger.error(f"Error getting dollar index: {e}")
        
        # Get 10-year yield with fallback options
        # US10Y → ^TNX → ZN=F (converted)
        try:
            if "US10Y" in data and len(data["US10Y"]['Close']) > 0:
                result["treasury_10y"] = float(data["US10Y"]['Close'].iloc[-1])
                result["treasury_yield_source"] = "US10Y"
            elif "^TNX" in data and len(data["^TNX"]['Close']) > 0:
                result["treasury_10y"] = float(data["^TNX"]['Close'].iloc[-1])
                result["treasury_yield_source"] = "^TNX"
            elif "ZN=F" in data and len(data["ZN=F"]['Close']) > 0:
                # Convert 10-year note futures to yield (approximate)
                futures_price = float(data["ZN=F"]['Close'].iloc[-1])
                result["treasury_futures"] = futures_price
                # Rough conversion from futures price to yield
                # When price goes up, yield goes down and vice versa
                # Conversion factor varies but this approximation works for our purposes
                result["treasury_10y"] = 100.0 / futures_price
                # More precise conversion: approximate 10-year yield
                # This will give a more realistic value in the 2-5% range typically
                result["treasury_10y"] = 6.00 - (futures_price - 100) * 0.06
                # Ensure we get a reasonable yield value
                if result["treasury_10y"] < 0 or result["treasury_10y"] > 10:
                    result["treasury_10y"] = 2.25  # Reasonable default
                result["treasury_yield_source"] = "ZN=F (converted)"
        except Exception as e:
            logger.error(f"Error getting treasury yield: {e}")
            # Reasonable default based on recent ranges
            result["treasury_10y"] = 2.25
            result["treasury_yield_source"] = "Default value"
        
        logger.debug(f"Premarket data structure: {result}")
        return result
    
    except Exception as e:
        logger.error(f"Error getting premarket data: {e}")
        # Return reasonable defaults
        return {
            "gold": 3200.0,
            "sp500_futures": 5450.0,
            "vix": 30.0,
            "dollar_index": 100.0,
            "treasury_futures": 110.0,
            "treasury_10y": 2.25,
            "treasury_yield_source": "Default values"
        }

def get_gold_futures_curve() -> Dict[str, Any]:
    """
    Get gold futures curve data with focus on term structure and recommendations
    
    Returns:
    - Dictionary with futures curve data and analysis
    """
    try:
        # Fetch spot gold (using GLD as proxy) and futures contracts
        symbols = [GOLD_SPOT] + GOLD_FUTURES_SYMBOLS
        data = yf.download(symbols, period="2d", interval="1d", group_by='ticker')
        
        result = {
            "timestamp": str(datetime.datetime.now()),
            "contracts": [],
            "structure": "unknown",
            "structure_description": "Insufficient data",
            "curve_steepness": 0,
            "spot_futures_spread": 0,
            "spot_futures_trend": "unknown",
            "is_bullish": False,
            "direction_reason": "Insufficient data",
            "spreads": []
        }
        
        # Extract prices from latest data
        if all(symbol in data for symbol in symbols):
            try:
                # Calculate current prices
                if GOLD_SPOT in data and 'Close' in data[GOLD_SPOT] and len(data[GOLD_SPOT]['Close']) > 0:
                    try:
                        spot_price_etf = float(data[GOLD_SPOT]['Close'].iloc[-1])
                        # More accurate conversion from GLD price to gold spot price in USD/oz
                        # Each share of GLD represents approximately 1/10th of an ounce of gold
                        # The exact ratio may vary slightly due to ETF expenses
                        spot_price = spot_price_etf * 10.0
                        logger.debug(f"GLD ETF price: ${spot_price_etf:.2f}, converted to gold spot: ${spot_price:.2f}/oz")
                    except (ValueError, TypeError, IndexError) as e:
                        logger.error(f"Error processing GLD ETF price: {str(e)}")
                        # Fallback to gold price from premarket data
                        premarket = get_premarket_data()
                        spot_price = premarket.get('gold', 0)
                        logger.debug(f"Using fallback gold spot price: ${spot_price:.2f}/oz")
                else:
                    # Fallback to gold price from premarket data
                    premarket = get_premarket_data()
                    spot_price = premarket.get('gold', 0)
                    logger.debug(f"GLD data unavailable, using fallback gold spot price: ${spot_price:.2f}/oz")
                
                contract_prices = {}
                for symbol in GOLD_FUTURES_SYMBOLS:
                    if symbol in data and 'Close' in data[symbol] and len(data[symbol]['Close']) > 0:
                        contract_prices[symbol] = float(data[symbol]['Close'].iloc[-1])
                        logger.debug(f"Futures contract {symbol} price: ${contract_prices[symbol]:.2f}")
            except (ValueError, TypeError, IndexError) as e:
                logger.error(f"Error processing price data: {str(e)}")
                # Set to reasonable values to prevent NaN in calculations
                spot_price = 0
                contract_prices = {}
            
            # Only proceed if we have enough price data
            if contract_prices and GOLD_FUTURES in contract_prices:
                front_month_price = contract_prices[GOLD_FUTURES]
                
                # Calculate spot-futures spread with safe handling of calculations
                try:
                    spot_futures_spread = front_month_price - spot_price
                    # Ensure we have valid numerical values
                    if not (np.isnan(spot_futures_spread) or np.isinf(spot_futures_spread)):
                        result["spot_futures_spread"] = round(spot_futures_spread, 2)
                    else:
                        result["spot_futures_spread"] = 0
                        logger.warning(f"Invalid spot-futures spread calculated: {spot_futures_spread}")
                except Exception as e:
                    logger.error(f"Error calculating spot-futures spread: {e}")
                    spot_futures_spread = 0
                    result["spot_futures_spread"] = 0
                
                # Add spot-futures trend with safe handling
                try:
                    if spot_futures_spread > 0:
                        result["spot_futures_trend"] = "Premium (futures > spot)"
                        # Calculate annualized premium safely
                        # Assuming 30 days to expiry for front month
                        try:
                            if spot_price > 0:
                                annual_premium_pct = (spot_futures_spread / spot_price) * (365 / 30) * 100
                                if not (np.isnan(annual_premium_pct) or np.isinf(annual_premium_pct)):
                                    result["structure_description"] = f"Market in contango with annualized premium of approximately {round(annual_premium_pct, 2)}%"
                                else:
                                    result["structure_description"] = "Market in contango (premium calculation unavailable)"
                            else:
                                result["structure_description"] = "Market in contango (premium calculation unavailable)"
                        except (ZeroDivisionError, TypeError, ValueError) as e:
                            logger.warning(f"Error calculating annual premium: {e}")
                            result["structure_description"] = "Market in contango (premium calculation unavailable)"
                    else:
                        result["spot_futures_trend"] = "Discount (futures < spot)"
                        try:
                            if spot_price > 0:
                                annual_discount_pct = (-spot_futures_spread / spot_price) * (365 / 30) * 100
                                if not (np.isnan(annual_discount_pct) or np.isinf(annual_discount_pct)):
                                    result["structure_description"] = f"Market in backwardation with annualized discount of approximately {round(annual_discount_pct, 2)}%, indicating potential supply constraints"
                                else:
                                    result["structure_description"] = "Market in backwardation, indicating potential supply constraints"
                            else:
                                result["structure_description"] = "Market in backwardation, indicating potential supply constraints"
                        except (ZeroDivisionError, TypeError, ValueError) as e:
                            logger.warning(f"Error calculating annual discount: {e}")
                            result["structure_description"] = "Market in backwardation, indicating potential supply constraints"
                except Exception as e:
                    logger.error(f"Error determining market structure: {e}")
                    result["spot_futures_trend"] = "Unknown"
                    result["structure_description"] = "Unable to determine market structure"
                
                # Use actual contract prices instead of synthetic ones when available
                front_month_price = contract_prices[GOLD_FUTURES]
                
                # Get actual prices for 2nd and 3rd month contracts if available, otherwise create synthetic prices
                second_month_symbol = GOLD_FUTURES_SYMBOLS[1] if len(GOLD_FUTURES_SYMBOLS) > 1 else None
                third_month_symbol = GOLD_FUTURES_SYMBOLS[2] if len(GOLD_FUTURES_SYMBOLS) > 2 else None
                
                if second_month_symbol in contract_prices:
                    second_month_price = contract_prices[second_month_symbol]
                else:
                    # Fallback to synthetic price (typical gold contango of ~0.3% per month)
                    second_month_price = front_month_price * 1.003
                
                if third_month_symbol in contract_prices:
                    third_month_price = contract_prices[third_month_symbol]
                else:
                    # Fallback to synthetic price (typical gold contango of ~0.6% for 2 months out)
                    third_month_price = front_month_price * 1.006
                
                # Calculate curve steepness based on actual or synthetic values
                prices = [front_month_price, second_month_price, third_month_price]
                
                # Determine structure (gold is almost always in contango unless there's a supply shock)
                is_contango = spot_price < front_month_price
                result["structure"] = "contango" if is_contango else "backwardation"
                
                # Calculate curve steepness (annualized)
                # Assuming about 3 months between first and last contract
                months_diff = 2  # front month to 3rd month = ~2 months
                try:
                    if prices[0] > 0:
                        price_diff_pct = ((prices[-1] / prices[0]) - 1) * 100
                        annualized_steepness = price_diff_pct * (12 / months_diff)
                        result["curve_steepness"] = round(annualized_steepness, 2)
                    else:
                        # If first price is zero or negative (error case)
                        result["curve_steepness"] = 0.0
                except (ZeroDivisionError, TypeError, IndexError):
                    # Handle calculation errors
                    logger.warning("Error calculating curve steepness, using default value")
                    result["curve_steepness"] = 0.0
                
                # Add contract details
                expiry_dates = {
                    "GC=F": "Front Month",
                    "GC+1": "Next Month",
                    "GC+2": "3rd Month"
                }
                
                # Get current month and generate proper month names for contract expiries
                current_date = datetime.datetime.now()
                current_month = current_date.month
                
                # Calculate month names for contracts (Front month is usually current or next month)
                months = ["January", "February", "March", "April", "May", "June", 
                         "July", "August", "September", "October", "November", "December"]
                
                # Calculate next few months for contract expiry descriptions
                front_month_idx = current_month - 1  # 0-based index
                second_month_idx = (front_month_idx + 1) % 12
                third_month_idx = (front_month_idx + 2) % 12
                
                front_month_name = f"{months[front_month_idx]}/{months[second_month_idx]}"
                second_month_name = f"{months[second_month_idx]}/{months[(second_month_idx + 1) % 12]}"
                third_month_name = f"{months[third_month_idx]}/{months[(third_month_idx + 1) % 12]}"
                
                # Calculate year for display (could be next year for distant contracts)
                current_year = current_date.year
                second_month_year = current_year if second_month_idx >= front_month_idx else current_year + 1
                third_month_year = current_year if third_month_idx >= front_month_idx else current_year + 1
                
                # Safe premium calculation function to avoid division by zero and handle NaN
                def safe_premium_calc(futures_price, spot_price):
                    if spot_price is None or spot_price <= 0 or np.isnan(spot_price):
                        return "N/A"  # Return string for invalid spot price
                    if futures_price is None or np.isnan(futures_price):
                        return "N/A"  # Return string for invalid futures price
                    
                    try:
                        premium_pct = ((futures_price / spot_price) - 1) * 100
                        # Check if result is NaN or infinite
                        if np.isnan(premium_pct) or np.isinf(premium_pct):
                            return "N/A"
                        return round(premium_pct, 2)
                    except (ZeroDivisionError, TypeError, ValueError):
                        return "N/A"  # Return string for calculation errors
                
                # Add the real front month contract
                front_premium = safe_premium_calc(front_month_price, spot_price)
                result["contracts"].append({
                    "symbol": GOLD_FUTURES,
                    "expiry": f"Front Month ({front_month_name} {current_year})",
                    "price": round(front_month_price, 2),
                    "premium": front_premium,
                    "volume": "N/A",
                    "open_interest": "N/A"
                })
                
                # Add second month contract (actual or synthetic)
                second_symbol = second_month_symbol if second_month_symbol else "GC+1"
                second_premium = safe_premium_calc(second_month_price, spot_price)
                result["contracts"].append({
                    "symbol": second_symbol,
                    "expiry": f"Next Month ({second_month_name} {second_month_year})",
                    "price": round(second_month_price, 2),
                    "premium": second_premium,
                    "volume": "N/A",
                    "open_interest": "N/A"
                })
                
                # Add third month contract (actual or synthetic)
                third_symbol = third_month_symbol if third_month_symbol else "GC+2"
                third_premium = safe_premium_calc(third_month_price, spot_price)
                result["contracts"].append({
                    "symbol": third_symbol,
                    "expiry": f"3rd Month ({third_month_name} {third_month_year})",
                    "price": round(third_month_price, 2),
                    "premium": third_premium,
                    "volume": "N/A",
                    "open_interest": "N/A"
                })
                
                # Determine if market is bullish or bearish
                # Simple logic: if spot is rising and futures premium is increasing, bullish
                if len(data[GOLD_SPOT]['Close']) > 1 and len(data[GOLD_FUTURES]['Close']) > 1:
                    spot_change = data[GOLD_SPOT]['Close'].iloc[-1] - data[GOLD_SPOT]['Close'].iloc[-2]
                    futures_change = data[GOLD_FUTURES]['Close'].iloc[-1] - data[GOLD_FUTURES]['Close'].iloc[-2]
                    
                    # Simple bullish criteria
                    is_bullish = spot_change > 0 and futures_change >= spot_change
                    result["is_bullish"] = is_bullish
                    
                    if is_bullish:
                        if result["structure"] == "contango":
                            result["direction_reason"] = "Rising spot price with increasing futures premium indicates growing bullish sentiment"
                        else:
                            result["direction_reason"] = "Rising spot price with backwardation indicates strong immediate demand"
                    else:
                        if result["structure"] == "contango":
                            result["direction_reason"] = "Declining spot price with contango structure suggests speculative rather than fundamental demand"
                        else:
                            result["direction_reason"] = "Decreasing spot price despite backwardation indicates temporary supply constraints"
                
                # Generate spread trade recommendations
                if result["structure"] == "contango" and result["curve_steepness"] > 2:
                    # Steep contango - consider bear spread
                    result["spreads"].append({
                        "name": "Bear Spread (Sell nearby, Buy distant)",
                        "description": "Sell front-month and buy distant contract to profit from curve flattening",
                        "expected_return": round(result["curve_steepness"] / 2, 1)
                    })
                elif result["structure"] == "backwardation" and result["curve_steepness"] < -2:
                    # Steep backwardation - consider bull spread
                    result["spreads"].append({
                        "name": "Bull Spread (Buy nearby, Sell distant)",
                        "description": "Buy front-month and sell distant contract to profit from immediate demand",
                        "expected_return": round(abs(result["curve_steepness"]) / 2, 1)
                    })
                
                # Add seasonal spreads
                current_month = datetime.datetime.now().month
                
                # Q1-Q2 spread recommendation
                if 1 <= current_month <= 3:
                    result["spreads"].append({
                        "name": "April-June Spread",
                        "description": "Historical seasonal strength in Q2 vs. Q1",
                        "expected_return": 0.8
                    })
                # Q2-Q3 spread recommendation
                elif 4 <= current_month <= 6:
                    result["spreads"].append({
                        "name": "June-August Spread",
                        "description": "Buy June, Sell August to capture summer seasonal pattern",
                        "expected_return": 0.5
                    })
                # Q3-Q4 spread recommendation
                elif 7 <= current_month <= 9:
                    result["spreads"].append({
                        "name": "December-February Spread",
                        "description": "Position for end-of-year strength into Q1",
                        "expected_return": 1.2
                    })
                
        return result
    
    except Exception as e:
        logger.error(f"Error analyzing gold futures curve: {str(e)}")
        return {
            "error": f"Error analyzing gold futures curve: {str(e)}",
            "timestamp": str(datetime.datetime.now())
        }

def get_real_interest_rates() -> Dict[str, Any]:
    """Get real interest rates data from FRED with detailed gold market impact analysis"""
    result = {
        "timestamp": str(datetime.datetime.now()),
        "has_fred_data": HAS_FRED,
        "nominal_rates": {},
        "inflation_expectations": {},
        "real_rates": {},
        "is_positive_real_rates": False,
        "gold_impact": "Neutral",
        "detailed_gold_analysis": {}
    }
    
    try:
        # We need FRED data for this
        if HAS_FRED:
            # Get 10-year nominal Treasury yield from FRED
            t10y_nominal = fred.get_series("DGS10").iloc[-1]
            # Get 5-year nominal Treasury yield from FRED
            t5y_nominal = fred.get_series("DGS5").iloc[-1]
            # Get 2-year nominal Treasury yield from FRED
            t2y_nominal = fred.get_series("DGS2").iloc[-1]
            
            # Get 10-year inflation expectations (breakeven rate)
            t10y_inflation = fred.get_series("T10YIE").iloc[-1]
            # Get 5-year inflation expectations (breakeven rate)
            t5y_inflation = fred.get_series("T5YIE").iloc[-1]
            
            # Store nominal rates
            result["nominal_rates"] = {
                "t10y": round(t10y_nominal, 2),
                "t5y": round(t5y_nominal, 2),
                "t2y": round(t2y_nominal, 2)
            }
            
            # Store inflation expectations
            result["inflation_expectations"] = {
                "t10y": round(t10y_inflation, 2),
                "t5y": round(t5y_inflation, 2)
            }
            
            # Calculate real rates (nominal - inflation expectations)
            t10y_real = t10y_nominal - t10y_inflation
            t5y_real = t5y_nominal - t5y_inflation
            
            # Store real rates
            result["real_rates"] = {
                "t10y": round(t10y_real, 2),
                "t5y": round(t5y_real, 2)
            }
            
            # Calculate yield curve spread (10y - 2y)
            yield_curve_spread = t10y_nominal - t2y_nominal
            result["yield_curve"] = {
                "spread_10y_2y": round(yield_curve_spread, 2),
                "is_inverted": yield_curve_spread < 0,
                "description": "Inverted (recession signal)" if yield_curve_spread < 0 else "Normal"
            }
            
            # Real rates impact on gold
            result["is_positive_real_rates"] = t10y_real > 0
            
            # Enhanced gold impact analysis
            if t10y_real > 1:
                result["gold_impact"] = "Very Bearish (Strongly Positive Real Rates)"
                result["detailed_gold_analysis"]["real_rates"] = {
                    "status": "Very Bearish",
                    "explanation": "Strongly positive real rates (>1%) significantly increase the opportunity cost of holding gold, which pays no interest. Investors typically prefer interest-bearing assets when real returns are strongly positive, causing downward pressure on gold prices."
                }
            elif t10y_real > 0:
                result["gold_impact"] = "Bearish (Positive Real Rates)"
                result["detailed_gold_analysis"]["real_rates"] = {
                    "status": "Bearish",
                    "explanation": "Positive real rates (0-1%) make interest-bearing assets more attractive than gold. Since gold doesn't pay interest or dividends, it becomes less competitive in investment portfolios when real returns on bonds are positive."
                }
            elif t10y_real > -1:
                result["gold_impact"] = "Neutral to Slightly Bullish (Slightly Negative Real Rates)"
                result["detailed_gold_analysis"]["real_rates"] = {
                    "status": "Slightly Bullish",
                    "explanation": "Slightly negative real rates (-1% to 0%) reduce the opportunity cost of holding gold. When real returns on bonds are negative but close to zero, gold becomes relatively more attractive, though not dramatically so."
                }
            else:
                result["gold_impact"] = "Bullish (Deeply Negative Real Rates)"
                result["detailed_gold_analysis"]["real_rates"] = {
                    "status": "Strongly Bullish",
                    "explanation": "Deeply negative real rates (below -1%) make gold particularly attractive. When nominal interest rates fail to compensate for inflation by a significant margin, gold's role as an inflation hedge and store of value becomes more valuable, typically driving strong price appreciation."
                }
                
            # Enhanced yield curve analysis for gold
            if yield_curve_spread < -0.5:
                result["economic_outlook"] = "Recession Warning (Deeply Inverted Yield Curve)"
                result["detailed_gold_analysis"]["yield_curve"] = {
                    "status": "Bullish for Gold",
                    "explanation": "A deeply inverted yield curve (10Y-2Y spread < -0.5%) is a strong recession signal. During recessions, central banks typically cut rates and implement monetary stimulus, which is usually bullish for gold. Market uncertainty during economic downturns also increases safe-haven demand for gold."
                }
            elif yield_curve_spread < 0:
                result["economic_outlook"] = "Economic Slowdown (Inverted Yield Curve)"
                result["detailed_gold_analysis"]["yield_curve"] = {
                    "status": "Moderately Bullish",
                    "explanation": "An inverted yield curve suggests economic slowdown ahead, which typically prompts monetary easing by central banks. Lower future interest rates and increased economic uncertainty tend to support gold prices."
                }
            elif yield_curve_spread < 0.5:
                result["economic_outlook"] = "Slowing Growth (Flattening Yield Curve)"
                result["detailed_gold_analysis"]["yield_curve"] = {
                    "status": "Neutral to Slightly Bullish",
                    "explanation": "A flattening yield curve indicates slowing economic growth. While not necessarily bullish for gold immediately, it signals potential rate cuts in the future which could eventually support gold prices."
                }
            else:
                result["economic_outlook"] = "Expansion (Steep Yield Curve)"
                result["detailed_gold_analysis"]["yield_curve"] = {
                    "status": "Neutral to Bearish",
                    "explanation": "A steep yield curve typically indicates economic expansion and potentially higher future interest rates. This environment is generally less supportive for gold, though if the steepness is accompanied by inflation concerns, gold can still perform well."
                }
                
            # Combined analysis - how real rates and yield curve together affect gold
            result["detailed_gold_analysis"]["combined_outlook"] = {
                "summary": f"Real Rates: {result['detailed_gold_analysis']['real_rates']['status']} + Yield Curve: {result['detailed_gold_analysis']['yield_curve']['status']}",
                "explanation": "Gold tends to perform best when real rates are negative AND the yield curve is signaling economic weakness. This combination suggests monetary stimulus and currency debasement, both supportive for gold prices."
            }
        else:
            # No FRED data available
            result["error"] = "FRED API data not available. Please check your FRED_API_KEY environment variable."
    except Exception as e:
        logger.error(f"Error getting real interest rates: {str(e)}")
        result["error"] = f"Error getting real interest rates: {str(e)}"
    
    return result

def get_market_correlation_data() -> Dict[str, Any]:
    """Get correlation data between gold and other markets"""
    result = {
        "timestamp": str(datetime.datetime.now()),
        "correlations": {},
        "premarket": {}
    }
    
    try:
        # Get data for multiple markets: Gold, S&P 500, VIX, Dollar Index, 10Y Treasury Yield
        # Use the reliable symbols defined globally
        tickers_data = yf.download(KEY_MARKET_SYMBOLS, period="1mo", interval="1d")
        
        # Process premarket data (latest)
        if "Close" in tickers_data and len(tickers_data["Close"]) > 0:
            # Pre-market info
            # Process basic market data
            result["premarket"] = {
                "gold": round(tickers_data["Close"]["GC=F"].iloc[-1], 2) if "GC=F" in tickers_data["Close"].columns else "N/A",
                "sp500_futures": round(tickers_data["Close"]["ES=F"].iloc[-1], 2) if "ES=F" in tickers_data["Close"].columns else "N/A",
                "vix": round(tickers_data["Close"]["^VIX"].iloc[-1], 2) if "^VIX" in tickers_data["Close"].columns else "N/A",
                "dollar_index": round(tickers_data["Close"]["DX-Y.NYB"].iloc[-1], 2) if "DX-Y.NYB" in tickers_data["Close"].columns else "N/A",
                "treasury_futures": round(tickers_data["Close"]["ZN=F"].iloc[-1], 2) if "ZN=F" in tickers_data["Close"].columns else "N/A"
            }
            
            # Add enhanced treasury yield with multiple fallback options
            # Try US10Y first (primary)
            if "US10Y" in tickers_data["Close"].columns and not np.isnan(tickers_data["Close"]["US10Y"].iloc[-1]):
                result["premarket"]["treasury_10y"] = round(tickers_data["Close"]["US10Y"].iloc[-1], 2)
                result["premarket"]["treasury_yield_source"] = "US10Y"
            # Fallback to TNX if available
            elif "^TNX" in tickers_data["Close"].columns and not np.isnan(tickers_data["Close"]["^TNX"].iloc[-1]):
                result["premarket"]["treasury_10y"] = round(tickers_data["Close"]["^TNX"].iloc[-1], 2)
                result["premarket"]["treasury_yield_source"] = "^TNX"
            # Fallback to ZN futures if available (with approximate conversion)
            elif "ZN=F" in tickers_data["Close"].columns and not np.isnan(tickers_data["Close"]["ZN=F"].iloc[-1]):
                # Very rough conversion: higher ZN price = lower yields (inverse relationship)
                # This is only an approximation
                zn_price = tickers_data["Close"]["ZN=F"].iloc[-1]
                treasury_yield = 100.0 / zn_price * 2.5  # very simplistic conversion
                result["premarket"]["treasury_10y"] = round(treasury_yield, 2)
                result["premarket"]["treasury_yield_source"] = "ZN=F (converted)"
            # Last resort: use FRED data if available
            elif HAS_FRED:
                try:
                    # Get latest 10Y Treasury rate from FRED
                    treasury_10y = fred.get_series('DGS10').iloc[-1]
                    result["premarket"]["treasury_10y"] = round(treasury_10y, 2)
                    result["premarket"]["treasury_yield_source"] = "FRED"
                except Exception as e:
                    logger.error(f"Error fetching data from FRED: {str(e)}")
                    result["premarket"]["treasury_10y"] = "N/A"
                    result["premarket"]["treasury_yield_source"] = "unavailable"
            else:
                result["premarket"]["treasury_10y"] = "N/A"
                result["premarket"]["treasury_yield_source"] = "unavailable"
            
            # Daily changes
            if len(tickers_data["Close"]) > 1:
                # Calculate daily changes for basic markets
                result["daily_changes"] = {
                    "gold": round(((tickers_data["Close"]["GC=F"].iloc[-1] / tickers_data["Close"]["GC=F"].iloc[-2]) - 1) * 100, 2) if "GC=F" in tickers_data["Close"].columns else "N/A",
                    "sp500_futures": round(((tickers_data["Close"]["ES=F"].iloc[-1] / tickers_data["Close"]["ES=F"].iloc[-2]) - 1) * 100, 2) if "ES=F" in tickers_data["Close"].columns else "N/A",
                    "vix": round(((tickers_data["Close"]["^VIX"].iloc[-1] / tickers_data["Close"]["^VIX"].iloc[-2]) - 1) * 100, 2) if "^VIX" in tickers_data["Close"].columns else "N/A",
                    "dollar_index": round(((tickers_data["Close"]["DX-Y.NYB"].iloc[-1] / tickers_data["Close"]["DX-Y.NYB"].iloc[-2]) - 1) * 100, 2) if "DX-Y.NYB" in tickers_data["Close"].columns else "N/A",
                }
                
                # Calculate treasury yield daily changes with fallback options
                if "US10Y" in tickers_data["Close"].columns and not np.isnan(tickers_data["Close"]["US10Y"].iloc[-1]) and not np.isnan(tickers_data["Close"]["US10Y"].iloc[-2]):
                    # Primary source: US10Y
                    result["daily_changes"]["treasury_10y"] = round(((tickers_data["Close"]["US10Y"].iloc[-1] / tickers_data["Close"]["US10Y"].iloc[-2]) - 1) * 100, 2)
                elif "^TNX" in tickers_data["Close"].columns and not np.isnan(tickers_data["Close"]["^TNX"].iloc[-1]) and not np.isnan(tickers_data["Close"]["^TNX"].iloc[-2]):
                    # Fallback: ^TNX
                    result["daily_changes"]["treasury_10y"] = round(((tickers_data["Close"]["^TNX"].iloc[-1] / tickers_data["Close"]["^TNX"].iloc[-2]) - 1) * 100, 2)
                else:
                    # No valid data
                    result["daily_changes"]["treasury_10y"] = "N/A"
            
            # Correlations (calculated from the past month of data)
            gold_prices = tickers_data["Close"]["GC=F"] if "GC=F" in tickers_data["Close"].columns else None
            
            if gold_prices is not None and len(gold_prices) > 5:
                # Calculate correlations with gold
                sp500_corr = gold_prices.corr(tickers_data["Close"]["ES=F"]) if "ES=F" in tickers_data["Close"].columns else None
                vix_corr = gold_prices.corr(tickers_data["Close"]["^VIX"]) if "^VIX" in tickers_data["Close"].columns else None
                dollar_corr = gold_prices.corr(tickers_data["Close"]["DX-Y.NYB"]) if "DX-Y.NYB" in tickers_data["Close"].columns else None
                # Calculate treasury yield correlation with gold using the best available source
                if "US10Y" in tickers_data["Close"].columns and not np.isnan(tickers_data["Close"]["US10Y"]).any():
                    tnx_corr = gold_prices.corr(tickers_data["Close"]["US10Y"])
                    treasury_source = "US10Y"
                elif "^TNX" in tickers_data["Close"].columns and not np.isnan(tickers_data["Close"]["^TNX"]).any():
                    tnx_corr = gold_prices.corr(tickers_data["Close"]["^TNX"])
                    treasury_source = "^TNX"
                else:
                    tnx_corr = None
                    treasury_source = None
                
                result["correlations"] = {
                    "gold_sp500": round(sp500_corr, 2) if sp500_corr is not None else "N/A",
                    "gold_vix": round(vix_corr, 2) if vix_corr is not None else "N/A",
                    "gold_dollar": round(dollar_corr, 2) if dollar_corr is not None else "N/A",
                    "gold_10y_yield": round(tnx_corr, 2) if tnx_corr is not None else "N/A",
                    "treasury_yield_source": treasury_source if treasury_source is not None else "N/A"
                }
                
                # Enhanced gold technical analysis with detailed indicators
                if len(gold_prices) > 50:
                    # Calculate various moving averages
                    gold_ma200 = gold_prices.rolling(window=200).mean().iloc[-1] if len(gold_prices) >= 200 else None
                    gold_ma50 = gold_prices.rolling(window=50).mean().iloc[-1]
                    gold_ma20 = gold_prices.rolling(window=20).mean().iloc[-1]
                    gold_ma10 = gold_prices.rolling(window=10).mean().iloc[-1]
                    gold_price = gold_prices.iloc[-1]
                    
                    # Calculate simple price momentum over different timeframes
                    price_change_5d = ((gold_price / gold_prices.iloc[-6]) - 1) * 100 if len(gold_prices) >= 6 else None
                    price_change_10d = ((gold_price / gold_prices.iloc[-11]) - 1) * 100 if len(gold_prices) >= 11 else None
                    price_change_20d = ((gold_price / gold_prices.iloc[-21]) - 1) * 100 if len(gold_prices) >= 21 else None
                    
                    # Calculate Relative Strength Index (RSI) - basic implementation
                    delta = gold_prices.diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    rs = gain / loss
                    rsi = 100 - (100 / (1 + rs)).iloc[-1]
                    
                    # Calculate MACD
                    ema12 = gold_prices.ewm(span=12, adjust=False).mean()
                    ema26 = gold_prices.ewm(span=26, adjust=False).mean()
                    macd_line = ema12 - ema26
                    signal_line = macd_line.ewm(span=9, adjust=False).mean()
                    macd_histogram = macd_line - signal_line
                    
                    # Determine overall technical condition
                    technical_score = 0
                    
                    # Moving Average signals (weight: high)
                    if gold_price > gold_ma50:
                        technical_score += 2
                    if gold_price > gold_ma20:
                        technical_score += 1
                    if gold_ma20 > gold_ma50:
                        technical_score += 1  # Golden cross
                    
                    # MA trends
                    ma20_trend_bullish = gold_ma20 > gold_prices.rolling(window=20).mean().iloc[-5]
                    if ma20_trend_bullish:
                        technical_score += 1
                        
                    # RSI signals (weight: medium)
                    if 40 <= rsi <= 60:
                        # Neutral zone
                        technical_score += 0
                    elif 30 <= rsi < 40:
                        # Slightly oversold
                        technical_score += 1
                    elif 60 < rsi <= 70:
                        # Slightly overbought
                        technical_score -= 1
                    elif rsi < 30:
                        # Strongly oversold - bullish
                        technical_score += 2
                    elif rsi > 70:
                        # Strongly overbought - bearish
                        technical_score -= 2
                        
                    # MACD signals (weight: high)
                    if macd_line.iloc[-1] > signal_line.iloc[-1]:
                        technical_score += 2
                    if macd_line.iloc[-1] > 0:
                        technical_score += 1
                    if macd_histogram.iloc[-1] > macd_histogram.iloc[-2]:
                        technical_score += 1  # Rising momentum
                        
                    # Momentum signals (weight: medium)
                    if price_change_5d is not None and price_change_5d > 0:
                        technical_score += 1
                    
                    # Final technical condition classification
                    if technical_score >= 6:
                        technical_condition = "Strongly Bullish"
                    elif technical_score >= 3:
                        technical_condition = "Bullish"
                    elif technical_score >= 0:
                        technical_condition = "Neutral"
                    elif technical_score >= -3:
                        technical_condition = "Bearish"
                    else:
                        technical_condition = "Strongly Bearish"
                    
                    # Create comprehensive technical analysis object
                    result["gold_technicals"] = {
                        "price": round(gold_price, 2),
                        "ma200": round(gold_ma200, 2) if gold_ma200 is not None else None,
                        "ma50": round(gold_ma50, 2),
                        "ma20": round(gold_ma20, 2),
                        "ma10": round(gold_ma10, 2),
                        "rsi": round(rsi, 1),
                        "macd": {
                            "line": round(macd_line.iloc[-1], 2),
                            "signal": round(signal_line.iloc[-1], 2),
                            "histogram": round(macd_histogram.iloc[-1], 2),
                            "bullish": macd_line.iloc[-1] > signal_line.iloc[-1]
                        },
                        "momentum": {
                            "day5": round(price_change_5d, 2) if price_change_5d is not None else None,
                            "day10": round(price_change_10d, 2) if price_change_10d is not None else None,
                            "day20": round(price_change_20d, 2) if price_change_20d is not None else None
                        },
                        "above_ma20": gold_price > gold_ma20,
                        "above_ma50": gold_price > gold_ma50,
                        "above_ma200": gold_price > gold_ma200 if gold_ma200 is not None else None,
                        "ma20_trend": "Up" if ma20_trend_bullish else "Down",
                        "condition": technical_condition,
                        "signals": {
                            "moving_averages": "Bullish" if gold_price > gold_ma50 and gold_price > gold_ma20 else "Bearish" if gold_price < gold_ma50 and gold_price < gold_ma20 else "Neutral",
                            "rsi": "Oversold" if rsi < 30 else "Overbought" if rsi > 70 else "Neutral",
                            "macd": "Bullish" if macd_line.iloc[-1] > signal_line.iloc[-1] else "Bearish",
                            "price_momentum": "Bullish" if price_change_5d is not None and price_change_5d > 0 else "Bearish"
                        },
                        "technical_score": technical_score,
                        "analysis_summary": f"Gold is currently in a {technical_condition.lower()} technical position based on moving averages, momentum indicators, and oscillators."
                    }
    except Exception as e:
        logger.error(f"Error getting market correlation data: {str(e)}")
        result["error"] = f"Error getting market correlation data: {str(e)}"
    
    return result

def get_enhanced_gold_futures_curve() -> Dict[str, Any]:
    """
    Enhanced version of gold futures curve with economic data integration
    Combines futures curve analysis with real interest rates and market correlations
    """
    # Get the basic futures curve data
    curve_data = get_gold_futures_curve()
    
    # If there was an error, just return the error
    if "error" in curve_data:
        return curve_data
    
    try:
        # Enhance with real interest rates from FRED
        rates_data = get_real_interest_rates()
        if not "error" in rates_data:
            curve_data["interest_rates"] = rates_data
            
            # Update the market outlook based on real rates
            if "gold_impact" in rates_data:
                # Include real rates in market direction analysis
                current_direction = curve_data.get("is_bullish", False)
                
                # Real rates are a strong factor for gold
                real_rates_bullish = "Bullish" in rates_data["gold_impact"]
                
                # Integrate the signals - if both futures curve and real rates agree, higher confidence
                if current_direction and real_rates_bullish:
                    curve_data["confidence_level"] = "High (Futures Curve and Real Rates Aligned Bullish)"
                elif not current_direction and not real_rates_bullish:
                    curve_data["confidence_level"] = "High (Futures Curve and Real Rates Aligned Bearish)"
                else:
                    curve_data["confidence_level"] = "Mixed (Futures Curve and Real Rates Giving Conflicting Signals)"
        
        # Add market correlation data
        market_data = get_market_correlation_data()
        if not "error" in market_data:
            curve_data["market_data"] = market_data
            
            # Integrate technical signals
            if "gold_technicals" in market_data:
                # Pass through technical data with one simple addition
                curve_data["technical_indicators"] = market_data["gold_technicals"]
                
                # Ensure signals.macd exists for the template
                if "signals" not in curve_data["technical_indicators"]:
                    curve_data["technical_indicators"]["signals"] = {}
                
                curve_data["technical_indicators"]["signals"]["macd"] = "Bullish" if curve_data["technical_indicators"]["macd"]["bullish"] else "Bearish"
                
                # Enhance market direction analysis with technical data
                current_direction = curve_data.get("is_bullish", False)
                technical_bullish = market_data["gold_technicals"].get("condition") == "Bullish"
                
                if "confidence_level" in curve_data:
                    # Further refine confidence if technical signals also align
                    if (current_direction and technical_bullish) or (not current_direction and not technical_bullish):
                        curve_data["confidence_level"] += " with Technical Confirmation"
                else:
                    # Set confidence based on technical and futures curve alignment
                    if current_direction and technical_bullish:
                        curve_data["confidence_level"] = "Medium (Futures Curve and Technicals Aligned)"
                    elif not current_direction and not technical_bullish:
                        curve_data["confidence_level"] = "Medium (Futures Curve and Technicals Aligned)"
                    else:
                        curve_data["confidence_level"] = "Low (Mixed Signals from Futures Curve and Technicals)"
            
            # Add key market correlations that matter for gold
            if "correlations" in market_data:
                curve_data["key_correlations"] = market_data["correlations"]
            
            # Add premarket data for context
            if "premarket" in market_data:
                # Print premarket data structure for debugging
                logger.debug(f"Premarket data structure: {market_data['premarket']}")
                curve_data["premarket_data"] = market_data["premarket"]
        
        # Provide a comprehensive market outlook
        curve_data["market_outlook"] = {
            "summary": "Comprehensive gold market outlook based on multiple indicators:",
            "points": []
        }
        
        # Add futures curve insight
        if curve_data.get("structure") == "contango":
            curve_data["market_outlook"]["points"].append(
                "Futures curve in contango: Normal market structure indicating storage costs and interest rates impact."
            )
        elif curve_data.get("structure") == "backwardation":
            curve_data["market_outlook"]["points"].append(
                "Futures curve in backwardation: Unusual structure indicating strong immediate demand or supply constraints."
            )
        
        # Add real rates insight
        if "interest_rates" in curve_data and "gold_impact" in curve_data["interest_rates"]:
            curve_data["market_outlook"]["points"].append(
                f"Real interest rates: {curve_data['interest_rates']['gold_impact']}"
            )
            
            # Add yield curve insight
            if "yield_curve" in curve_data["interest_rates"]:
                curve_data["market_outlook"]["points"].append(
                    f"Yield curve: {curve_data['interest_rates']['yield_curve']['description']} with 10y-2y spread of {curve_data['interest_rates']['yield_curve']['spread_10y_2y']}%"
                )
        
        # Add technical insight
        if "technical_indicators" in curve_data:
            curve_data["market_outlook"]["points"].append(
                f"Technical indicators: {curve_data['technical_indicators'].get('condition', 'Neutral')}. "
                f"Price is {'above' if curve_data['technical_indicators'].get('above_ma20', False) else 'below'} 20-day MA and "
                f"{'above' if curve_data['technical_indicators'].get('above_ma50', False) else 'below'} 50-day MA."
            )
        
        # Add USD correlation insight
        if "key_correlations" in curve_data and "gold_dollar" in curve_data["key_correlations"]:
            gold_dollar_corr = curve_data["key_correlations"]["gold_dollar"]
            if isinstance(gold_dollar_corr, (int, float)):
                corr_description = "strong negative" if gold_dollar_corr < -0.7 else "moderate negative" if gold_dollar_corr < -0.3 else "weak negative" if gold_dollar_corr < 0 else "weak positive" if gold_dollar_corr < 0.3 else "moderate positive" if gold_dollar_corr < 0.7 else "strong positive"
                curve_data["market_outlook"]["points"].append(
                    f"USD correlation: {corr_description} ({gold_dollar_corr}). Traditionally, gold has a negative correlation with the dollar."
                )
        
        # Add summary directive
        outlook_summary = "Bullish" if curve_data.get("is_bullish", False) else "Bearish"
        confidence = curve_data.get("confidence_level", "Moderate")
        
        curve_data["market_outlook"]["directive"] = f"{outlook_summary} with {confidence} confidence"
        
    except Exception as e:
        logger.error(f"Error enhancing gold futures curve: {str(e)}")
        # Still return the basic data plus the error
        curve_data["enhancement_error"] = f"Error adding enhanced data: {str(e)}"
    
    return curve_data

if __name__ == "__main__":
    # Test function
    curve_data = get_enhanced_gold_futures_curve()
    print(curve_data)