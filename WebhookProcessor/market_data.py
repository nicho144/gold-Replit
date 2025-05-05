"""
Market Data Module for Futures Market Analysis
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Ticker symbols
ES_FUTURES = "ES=F"  # S&P 500 E-mini
GOLD_FUTURES = "GC=F"  # Gold Front Month
GOLD_FUTURES_2 = "GCM24.CMX"  # Gold Next Month
GOLD_FUTURES_3 = "GCQ24.CMX"  # Gold 3rd Month
TEN_YEAR_YIELD = "^TNX"  # 10-Year Treasury Yield
VIX = "^VIX"  # Volatility Index
GOLD_ETF = "GLD"  # SPDR Gold Trust ETF (spot gold proxy)

def get_premarket_data() -> Dict[str, Any]:
    """
    Get the latest premarket data for major futures contracts and indices
    """
    try:
        # Fetch data for multiple tickers at once
        tickers = [ES_FUTURES, GOLD_FUTURES, TEN_YEAR_YIELD, VIX]
        data = yf.download(tickers, period="1d", premarket=True, group_by='ticker')
        
        # Process the data
        result = {}
        for ticker in tickers:
            if ticker in data:
                ticker_data = data[ticker]
                if not ticker_data.empty:
                    last_price = ticker_data['Close'].iloc[-1]
                    prev_close = ticker_data['Open'].iloc[0]
                    change = last_price - prev_close
                    change_pct = (change / prev_close) * 100 if prev_close != 0 else 0
                    
                    result[ticker] = {
                        "last_price": last_price,
                        "change": change,
                        "change_pct": change_pct,
                        "timestamp": str(ticker_data.index[-1])
                    }
                else:
                    result[ticker] = {"error": "No data available"}
            else:
                result[ticker] = {"error": "Ticker not found in data"}
        
        # Add market status
        now = datetime.now()
        market_hours = {
            "premarket": (now.hour >= 4 and now.hour < 9) or (now.hour == 9 and now.minute < 30),
            "market": (now.hour >= 9 and now.hour < 16) and not (now.hour == 9 and now.minute < 30),
            "after_hours": (now.hour >= 16 and now.hour < 20),
            "closed": not ((now.hour >= 4 and now.hour < 20) or (now.hour == 9 and now.minute < 30))
        }
        
        result["market_status"] = [k for k, v in market_hours.items() if v][0]
        result["timestamp"] = str(datetime.now())
        
        return result
    except Exception as e:
        logger.error(f"Error fetching premarket data: {e}")
        return {"error": str(e)}

def get_gold_term_structure() -> Dict[str, Any]:
    """
    Analyze gold futures term structure (GC1, GC2, GC3) and 
    calculate contango/backwardation metrics
    """
    try:
        # Fetch data for gold futures contracts
        tickers = [GOLD_FUTURES, GOLD_FUTURES_2, GOLD_FUTURES_3, GOLD_ETF]
        data = yf.download(tickers, period="5d", group_by='ticker')
        
        # Process the data
        result = {
            "contracts": {},
            "term_structure": {},
            "analysis": {}
        }
        
        # Extract latest prices
        prices = {}
        for ticker in tickers:
            if ticker in data:
                ticker_data = data[ticker]
                if not ticker_data.empty:
                    prices[ticker] = ticker_data['Close'].iloc[-1]
                    result["contracts"][ticker] = {
                        "price": ticker_data['Close'].iloc[-1],
                        "volume": ticker_data['Volume'].iloc[-1],
                        "timestamp": str(ticker_data.index[-1])
                    }
        
        # Calculate term structure metrics
        if GOLD_FUTURES in prices and GOLD_FUTURES_2 in prices:
            # Calculate contango (positive) or backwardation (negative)
            front_next_spread = prices[GOLD_FUTURES_2] - prices[GOLD_FUTURES]
            front_next_pct = (front_next_spread / prices[GOLD_FUTURES]) * 100
            
            result["term_structure"]["front_next_spread"] = front_next_spread
            result["term_structure"]["front_next_percentage"] = front_next_pct
            result["term_structure"]["structure"] = "contango" if front_next_spread > 0 else "backwardation"
            result["term_structure"]["steepness"] = abs(front_next_pct)
            
            # If we have 3rd month data, calculate curve steepness
            if GOLD_FUTURES_3 in prices:
                next_third_spread = prices[GOLD_FUTURES_3] - prices[GOLD_FUTURES_2]
                next_third_pct = (next_third_spread / prices[GOLD_FUTURES_2]) * 100
                
                result["term_structure"]["next_third_spread"] = next_third_spread
                result["term_structure"]["next_third_percentage"] = next_third_pct
                
                # Calculate curve steepness (comparison of spreads)
                curve_steepness = front_next_spread - next_third_spread
                result["term_structure"]["curve_steepness"] = curve_steepness
                
                # Steepening or flattening
                if front_next_spread > 0:  # Contango
                    if curve_steepness > 0:
                        result["term_structure"]["curve_shape"] = "steepening_contango"
                    else:
                        result["term_structure"]["curve_shape"] = "flattening_contango"
                else:  # Backwardation
                    if curve_steepness < 0:
                        result["term_structure"]["curve_shape"] = "steepening_backwardation"
                    else:
                        result["term_structure"]["curve_shape"] = "flattening_backwardation"
        
        # Calculate spot-to-futures basis
        if GOLD_ETF in prices and GOLD_FUTURES in prices:
            spot_futures_spread = prices[GOLD_FUTURES] - prices[GOLD_ETF]
            spot_futures_pct = (spot_futures_spread / prices[GOLD_ETF]) * 100
            
            result["term_structure"]["spot_futures_spread"] = spot_futures_spread
            result["term_structure"]["spot_futures_percentage"] = spot_futures_pct
        
        # Analyze term structure for market signals
        if "structure" in result["term_structure"]:
            structure = result["term_structure"]["structure"]
            steepness = result["term_structure"]["steepness"]
            
            # Analyze based on term structure
            if structure == "contango":
                if steepness > 3.0:
                    result["analysis"]["signal"] = "strong_bearish"
                    result["analysis"]["interpretation"] = "Steep contango indicates significant future supply or weak current demand"
                elif steepness > 1.5:
                    result["analysis"]["signal"] = "moderate_bearish"
                    result["analysis"]["interpretation"] = "Moderate contango suggests increasing supply or weakening demand"
                else:
                    result["analysis"]["signal"] = "mild_bearish"
                    result["analysis"]["interpretation"] = "Mild contango indicates slightly negative forward expectations"
            else:  # backwardation
                if steepness > 3.0:
                    result["analysis"]["signal"] = "strong_bullish"
                    result["analysis"]["interpretation"] = "Steep backwardation indicates tight supply or strong current demand"
                elif steepness > 1.5:
                    result["analysis"]["signal"] = "moderate_bullish"
                    result["analysis"]["interpretation"] = "Moderate backwardation suggests stable demand and limited supply"
                else:
                    result["analysis"]["signal"] = "mild_bullish"
                    result["analysis"]["interpretation"] = "Mild backwardation indicates slightly positive current conditions"
        
        return result
    except Exception as e:
        logger.error(f"Error analyzing gold term structure: {e}")
        return {"error": str(e)}

def get_interest_rate_impact() -> Dict[str, Any]:
    """
    Analyze the relationship between interest rates (10Y Treasury Yield) and gold prices
    """
    try:
        # Fetch historical data
        tickers = [TEN_YEAR_YIELD, GOLD_FUTURES]
        data = yf.download(tickers, period="1y", interval="1d", group_by='ticker')
        
        # Process the data
        result = {
            "current": {},
            "correlation": {},
            "analysis": {}
        }
        
        # Extract yield and gold data
        yield_data = data[TEN_YEAR_YIELD]['Close']
        gold_data = data[GOLD_FUTURES]['Close']
        
        # Calculate current values
        result["current"]["treasury_yield"] = yield_data.iloc[-1]
        result["current"]["gold_price"] = gold_data.iloc[-1]
        
        # Calculate change over different time periods
        for period, days in [("1d", 1), ("1w", 5), ("1m", 20), ("3m", 60), ("6m", 120)]:
            offset = min(days, len(yield_data) - 1)
            
            yield_change = yield_data.iloc[-1] - yield_data.iloc[-offset-1]
            yield_change_pct = (yield_change / yield_data.iloc[-offset-1]) * 100
            
            gold_change = gold_data.iloc[-1] - gold_data.iloc[-offset-1]
            gold_change_pct = (gold_change / gold_data.iloc[-offset-1]) * 100
            
            result["current"][f"yield_change_{period}"] = yield_change
            result["current"][f"yield_change_pct_{period}"] = yield_change_pct
            result["current"][f"gold_change_{period}"] = gold_change
            result["current"][f"gold_change_pct_{period}"] = gold_change_pct
        
        # Calculate correlation
        correlation = yield_data.corr(gold_data)
        result["correlation"]["overall"] = correlation
        
        # Calculate rolling correlation (30-day window)
        combined = pd.DataFrame({"yield": yield_data, "gold": gold_data})
        rolling_corr = combined['yield'].rolling(window=30).corr(combined['gold'])
        result["correlation"]["recent_30d"] = rolling_corr.iloc[-1]
        
        # Analyze relationship
        if correlation < -0.5:
            result["analysis"]["relationship"] = "strong_negative"
            result["analysis"]["interpretation"] = "Strong negative correlation between yields and gold prices"
        elif correlation < -0.2:
            result["analysis"]["relationship"] = "moderate_negative"
            result["analysis"]["interpretation"] = "Moderate negative correlation between yields and gold prices"
        elif correlation < 0.2:
            result["analysis"]["relationship"] = "weak"
            result["analysis"]["interpretation"] = "Weak correlation between yields and gold prices"
        elif correlation < 0.5:
            result["analysis"]["relationship"] = "moderate_positive"
            result["analysis"]["interpretation"] = "Moderate positive correlation between yields and gold prices"
        else:
            result["analysis"]["relationship"] = "strong_positive"
            result["analysis"]["interpretation"] = "Strong positive correlation between yields and gold prices"
        
        # Analyze current trend impact
        recent_yield_trend = result["current"]["yield_change_1m"]
        if recent_yield_trend > 0.25:  # Yield increasing significantly
            if correlation < -0.2:  # Negative correlation
                result["analysis"]["impact"] = "bearish"
                result["analysis"]["forecast"] = "Rising yields likely to pressure gold prices lower"
            else:
                result["analysis"]["impact"] = "neutral"
                result["analysis"]["forecast"] = "Rising yields having limited impact on gold prices"
        elif recent_yield_trend < -0.25:  # Yield decreasing significantly
            if correlation < -0.2:  # Negative correlation
                result["analysis"]["impact"] = "bullish"
                result["analysis"]["forecast"] = "Falling yields likely to support gold prices"
            else:
                result["analysis"]["impact"] = "neutral"
                result["analysis"]["forecast"] = "Falling yields having limited impact on gold prices"
        else:  # Yield relatively stable
            result["analysis"]["impact"] = "neutral"
            result["analysis"]["forecast"] = "Stable yields likely to have minimal impact on gold prices"
        
        return result
    except Exception as e:
        logger.error(f"Error analyzing interest rate impact: {e}")
        return {"error": str(e)}

def analyze_market_sentiment() -> Dict[str, Any]:
    """
    Analyze market sentiment using VIX and its relationship to gold
    """
    try:
        # Fetch VIX and Gold data
        tickers = [VIX, GOLD_FUTURES, ES_FUTURES]
        data = yf.download(tickers, period="3m", interval="1d", group_by='ticker')
        
        result = {
            "current": {},
            "correlations": {},
            "analysis": {}
        }
        
        # Extract latest data
        vix_data = data[VIX]['Close']
        gold_data = data[GOLD_FUTURES]['Close']
        sp_data = data[ES_FUTURES]['Close']
        
        # Calculate current values and changes
        result["current"]["vix"] = vix_data.iloc[-1]
        result["current"]["gold"] = gold_data.iloc[-1]
        result["current"]["sp500"] = sp_data.iloc[-1]
        
        # VIX thresholds
        vix_current = vix_data.iloc[-1]
        vix_percentile = 100 * (vix_data < vix_current).sum() / len(vix_data)
        
        if vix_current > 30:
            vix_state = "high"
            sentiment = "fearful"
        elif vix_current > 20:
            vix_state = "elevated"
            sentiment = "cautious"
        elif vix_current > 15:
            vix_state = "normal"
            sentiment = "neutral"
        else:
            vix_state = "low"
            sentiment = "complacent"
        
        result["current"]["vix_state"] = vix_state
        result["current"]["vix_percentile"] = vix_percentile
        result["current"]["sentiment"] = sentiment
        
        # Calculate correlations
        vix_gold_corr = vix_data.corr(gold_data)
        vix_sp_corr = vix_data.corr(sp_data)
        gold_sp_corr = gold_data.corr(sp_data)
        
        result["correlations"]["vix_gold"] = vix_gold_corr
        result["correlations"]["vix_sp500"] = vix_sp_corr
        result["correlations"]["gold_sp500"] = gold_sp_corr
        
        # Analyze market sentiment impact on gold
        if vix_state in ["high", "elevated"]:
            if vix_gold_corr > 0.3:
                result["analysis"]["gold_sentiment"] = "bullish"
                result["analysis"]["interpretation"] = "Elevated market fear is positive for gold as a safe-haven"
            elif vix_gold_corr < -0.3:
                result["analysis"]["gold_sentiment"] = "bearish"
                result["analysis"]["interpretation"] = "Despite elevated VIX, gold is not acting as a safe-haven"
            else:
                result["analysis"]["gold_sentiment"] = "neutral"
                result["analysis"]["interpretation"] = "Market fear having limited impact on gold"
        else:
            if gold_sp_corr > 0.5:
                result["analysis"]["gold_sentiment"] = "risk_on"
                result["analysis"]["interpretation"] = "Gold moving in tandem with risk assets (not safe-haven behavior)"
            elif gold_sp_corr < -0.3:
                result["analysis"]["gold_sentiment"] = "hedging"
                result["analysis"]["interpretation"] = "Gold serving as a hedge against equity market risk"
            else:
                result["analysis"]["gold_sentiment"] = "neutral"
                result["analysis"]["interpretation"] = "Gold showing independence from equity markets"
        
        return result
    except Exception as e:
        logger.error(f"Error analyzing market sentiment: {e}")
        return {"error": str(e)}

def detect_gold_cycle_thresholds() -> Dict[str, Any]:
    """
    Detect potential gold cycle turning points based on historical thresholds
    """
    try:
        # Get current data
        term_structure = get_gold_term_structure()
        interest_impact = get_interest_rate_impact()
        sentiment = analyze_market_sentiment()
        
        # Compile threshold indicators
        result = {
            "indicators": {},
            "thresholds": {},
            "analysis": {}
        }
        
        # Extract key metrics from other analyses
        if "term_structure" in term_structure and "structure" in term_structure["term_structure"]:
            contango = term_structure["term_structure"]["structure"] == "contango"
            steepness = term_structure["term_structure"].get("steepness", 0)
            
            result["indicators"]["contango"] = contango
            result["indicators"]["term_structure_steepness"] = steepness
            
            # Term structure thresholds
            result["thresholds"]["steep_contango"] = steepness > 2.5 and contango
        else:
            result["indicators"]["term_structure_error"] = "Term structure data not available"
        
        # Interest rate thresholds
        if "analysis" in interest_impact:
            rising_yields = interest_impact["current"].get("yield_change_1m", 0) > 0
            
            result["indicators"]["rising_yields"] = rising_yields
            result["indicators"]["yield_gold_correlation"] = interest_impact["correlation"].get("recent_30d", 0)
            
            # Threshold: rising yields with negative correlation
            result["thresholds"]["negative_yield_impact"] = (
                rising_yields and 
                interest_impact["correlation"].get("recent_30d", 0) < -0.3
            )
        else:
            result["indicators"]["interest_impact_error"] = "Interest rate impact data not available"
        
        # Market sentiment thresholds
        if "analysis" in sentiment:
            risk_on = sentiment["analysis"].get("gold_sentiment") == "risk_on"
            vix_state = sentiment["current"].get("vix_state", "normal")
            
            result["indicators"]["risk_on_sentiment"] = risk_on
            result["indicators"]["vix_state"] = vix_state
            
            # Threshold: complacent market with gold moving with risk assets
            result["thresholds"]["risk_complacency"] = (
                risk_on and 
                vix_state in ["low", "normal"]
            )
        else:
            result["indicators"]["sentiment_error"] = "Sentiment data not available"
        
        # Count bearish threshold breaches
        bearish_count = sum([
            result["thresholds"].get("steep_contango", False),
            result["thresholds"].get("negative_yield_impact", False),
            result["thresholds"].get("risk_complacency", False)
        ])
        
        # Overall cycle analysis
        if bearish_count >= 3:
            result["analysis"]["cycle_signal"] = "strongly_bearish"
            result["analysis"]["interpretation"] = "Multiple indicators suggest potential end of gold bullish cycle"
        elif bearish_count == 2:
            result["analysis"]["cycle_signal"] = "moderately_bearish"
            result["analysis"]["interpretation"] = "Some indicators point to weakening gold cycle"
        elif bearish_count == 1:
            result["analysis"]["cycle_signal"] = "mildly_bearish"
            result["analysis"]["interpretation"] = "Early warning signs of potential cycle turn"
        else:
            result["analysis"]["cycle_signal"] = "not_bearish"
            result["analysis"]["interpretation"] = "No significant bearish threshold breaches detected"
        
        result["analysis"]["threshold_breaches"] = bearish_count
        result["analysis"]["threshold_maximum"] = 3
        
        return result
    except Exception as e:
        logger.error(f"Error detecting gold cycle thresholds: {e}")
        return {"error": str(e)}

def get_economic_expectations() -> Dict[str, Any]:
    """
    Analyze current economic expectations and their impact on gold
    """
    try:
        # Gather relevant market data
        tickers = [TEN_YEAR_YIELD, "^DXY", "CL=F", GOLD_FUTURES]  # 10Y Yield, US Dollar, Crude Oil, Gold
        data = yf.download(tickers, period="3m", interval="1d", group_by='ticker')
        
        result = {
            "current": {},
            "trends": {},
            "analysis": {}
        }
        
        # Extract and analyze key economic indicators
        # 1. Interest Rates/Inflation Expectations
        yield_data = data[TEN_YEAR_YIELD]['Close']
        yield_change_1m = (yield_data.iloc[-1] - yield_data.iloc[-21]) / yield_data.iloc[-21] * 100
        
        # 2. Dollar Strength
        dollar_data = data["^DXY"]['Close'] if "^DXY" in data else None
        if dollar_data is not None and not dollar_data.empty:
            dollar_change_1m = (dollar_data.iloc[-1] - dollar_data.iloc[-21]) / dollar_data.iloc[-21] * 100
        else:
            dollar_change_1m = None
        
        # 3. Inflation Pressure (via crude oil)
        oil_data = data["CL=F"]['Close']
        oil_change_1m = (oil_data.iloc[-1] - oil_data.iloc[-21]) / oil_data.iloc[-21] * 100
        
        # Store current values and trends
        result["current"]["treasury_yield"] = yield_data.iloc[-1]
        result["current"]["dollar_index"] = dollar_data.iloc[-1] if dollar_data is not None and not dollar_data.empty else None
        result["current"]["crude_oil"] = oil_data.iloc[-1]
        
        result["trends"]["yield_change_1m"] = yield_change_1m
        result["trends"]["dollar_change_1m"] = dollar_change_1m
        result["trends"]["oil_change_1m"] = oil_change_1m
        
        # Analyze economic expectations
        # Rising yields + Rising dollar = Tightening monetary environment (negative for gold)
        # Rising oil = Inflation pressure (positive for gold)
        inflation_expectation = "rising" if oil_change_1m > 5 else "stable" if abs(oil_change_1m) <= 5 else "falling"
        
        tightening_signals = 0
        if yield_change_1m > 5:
            tightening_signals += 1
        if dollar_change_1m is not None and dollar_change_1m > 2:
            tightening_signals += 1
        
        monetary_environment = "tightening" if tightening_signals >= 1 else "neutral" if tightening_signals == 1 else "loosening"
        
        result["analysis"]["inflation_expectation"] = inflation_expectation
        result["analysis"]["monetary_environment"] = monetary_environment
        
        # Overall impact analysis
        if monetary_environment == "tightening" and inflation_expectation != "rising":
            result["analysis"]["economic_impact"] = "bearish"
            result["analysis"]["interpretation"] = "Tightening monetary environment without rising inflation is negative for gold"
        elif monetary_environment == "loosening" and inflation_expectation == "rising":
            result["analysis"]["economic_impact"] = "strongly_bullish"
            result["analysis"]["interpretation"] = "Loosening monetary policy with rising inflation is very positive for gold"
        elif monetary_environment == "loosening":
            result["analysis"]["economic_impact"] = "bullish"
            result["analysis"]["interpretation"] = "Loosening monetary environment is positive for gold"
        elif inflation_expectation == "rising":
            result["analysis"]["economic_impact"] = "mildly_bullish"
            result["analysis"]["interpretation"] = "Rising inflation expectations provide some support for gold"
        else:
            result["analysis"]["economic_impact"] = "neutral"
            result["analysis"]["interpretation"] = "Current economic conditions have mixed implications for gold"
        
        return result
    except Exception as e:
        logger.error(f"Error analyzing economic expectations: {e}")
        return {"error": str(e)}

def get_comprehensive_analysis() -> Dict[str, Any]:
    """
    Combine all analyses into a comprehensive market report
    """
    try:
        premarket = get_premarket_data()
        term_structure = get_gold_term_structure()
        interest_impact = get_interest_rate_impact()
        sentiment = analyze_market_sentiment()
        cycle = detect_gold_cycle_thresholds()
        economic = get_economic_expectations()
        
        result = {
            "timestamp": str(datetime.now()),
            "premarket_data": premarket,
            "term_structure": term_structure,
            "interest_rate_impact": interest_impact,
            "market_sentiment": sentiment,
            "gold_cycle": cycle,
            "economic_expectations": economic,
            "summary": {}
        }
        
        # Generate summary
        gold_signals = []
        
        # Add signals from term structure
        if "analysis" in term_structure and "signal" in term_structure["analysis"]:
            gold_signals.append({
                "factor": "Term Structure",
                "signal": term_structure["analysis"]["signal"],
                "interpretation": term_structure["analysis"]["interpretation"]
            })
        
        # Add signals from interest rates
        if "analysis" in interest_impact and "impact" in interest_impact["analysis"]:
            gold_signals.append({
                "factor": "Interest Rates",
                "signal": interest_impact["analysis"]["impact"],
                "interpretation": interest_impact["analysis"]["forecast"]
            })
        
        # Add signals from sentiment
        if "analysis" in sentiment and "gold_sentiment" in sentiment["analysis"]:
            gold_signals.append({
                "factor": "Market Sentiment",
                "signal": sentiment["analysis"]["gold_sentiment"],
                "interpretation": sentiment["analysis"]["interpretation"]
            })
        
        # Add signals from economic expectations
        if "analysis" in economic and "economic_impact" in economic["analysis"]:
            gold_signals.append({
                "factor": "Economic Expectations",
                "signal": economic["analysis"]["economic_impact"],
                "interpretation": economic["analysis"]["interpretation"]
            })
        
        # Add signals from cycle analysis
        if "analysis" in cycle and "cycle_signal" in cycle["analysis"]:
            gold_signals.append({
                "factor": "Cycle Analysis",
                "signal": cycle["analysis"]["cycle_signal"],
                "interpretation": cycle["analysis"]["interpretation"]
            })
        
        result["summary"]["signals"] = gold_signals
        
        # Count bullish vs bearish signals
        signal_counts = {"bullish": 0, "bearish": 0, "neutral": 0}
        
        for signal in gold_signals:
            signal_value = signal["signal"].lower()
            if "bullish" in signal_value or signal_value in ["positive", "rising"]:
                signal_counts["bullish"] += 1
            elif "bearish" in signal_value or signal_value in ["negative", "falling"]:
                signal_counts["bearish"] += 1
            else:
                signal_counts["neutral"] += 1
        
        result["summary"]["signal_counts"] = signal_counts
        
        # Generate overall market outlook
        if signal_counts["bullish"] > signal_counts["bearish"] + signal_counts["neutral"]:
            overall_signal = "bullish"
            confidence = "high" if signal_counts["bullish"] >= 4 else "moderate"
        elif signal_counts["bearish"] > signal_counts["bullish"] + signal_counts["neutral"]:
            overall_signal = "bearish"
            confidence = "high" if signal_counts["bearish"] >= 4 else "moderate"
        elif signal_counts["bullish"] > signal_counts["bearish"]:
            overall_signal = "mildly_bullish"
            confidence = "low"
        elif signal_counts["bearish"] > signal_counts["bullish"]:
            overall_signal = "mildly_bearish"
            confidence = "low"
        else:
            overall_signal = "neutral"
            confidence = "low"
        
        result["summary"]["overall_signal"] = overall_signal
        result["summary"]["confidence"] = confidence
        
        # Get current gold price and generate price targets
        current_gold = None
        if GOLD_FUTURES in premarket and "last_price" in premarket[GOLD_FUTURES]:
            current_gold = premarket[GOLD_FUTURES]["last_price"]
        elif "current" in term_structure and "contracts" in term_structure and GOLD_FUTURES in term_structure["contracts"]:
            current_gold = term_structure["contracts"][GOLD_FUTURES]["price"]
        
        if current_gold is not None:
            if overall_signal == "bullish":
                support = current_gold * 0.97  # 3% below current price
                resistance = current_gold * 1.05  # 5% above current price
            elif overall_signal == "bearish":
                support = current_gold * 0.95  # 5% below current price
                resistance = current_gold * 1.03  # 3% above current price
            elif overall_signal == "mildly_bullish":
                support = current_gold * 0.98  # 2% below current price
                resistance = current_gold * 1.03  # 3% above current price
            elif overall_signal == "mildly_bearish":
                support = current_gold * 0.97  # 3% below current price
                resistance = current_gold * 1.02  # 2% above current price
            else:  # neutral
                support = current_gold * 0.98  # 2% below current price
                resistance = current_gold * 1.02  # 2% above current price
            
            result["summary"]["price_targets"] = {
                "current": current_gold,
                "support": support,
                "resistance": resistance
            }
        
        # Generate trading recommendations
        recommendations = []
        
        if overall_signal in ["bullish", "mildly_bullish"]:
            recommendations.append("Consider long positions in gold futures or ETFs")
            if "term_structure" in term_structure and "structure" in term_structure["term_structure"]:
                if term_structure["term_structure"]["structure"] == "contango":
                    recommendations.append("Be cautious of roll costs in long-term ETF holdings")
                else:  # backwardation
                    recommendations.append("Roll yield is favorable for long-term futures positions")
        elif overall_signal in ["bearish", "mildly_bearish"]:
            recommendations.append("Consider reducing long exposure or implementing hedges")
            if signal_counts["bearish"] >= 3:
                recommendations.append("Short positions may be warranted for experienced traders")
        else:  # neutral
            recommendations.append("Wait for clearer signals before taking new positions")
            recommendations.append("Focus on shorter-term trading opportunities rather than long-term trend following")
        
        # Add interest rate specific recommendation
        if "analysis" in interest_impact and "impact" in interest_impact["analysis"]:
            if interest_impact["analysis"]["impact"] == "bearish":
                recommendations.append("Monitor interest rate developments closely as they're pressuring gold")
            elif interest_impact["analysis"]["impact"] == "bullish":
                recommendations.append("Current interest rate environment is supportive for gold prices")
        
        result["summary"]["recommendations"] = recommendations
        
        return result
    except Exception as e:
        logger.error(f"Error generating comprehensive analysis: {e}")
        return {"error": str(e)}