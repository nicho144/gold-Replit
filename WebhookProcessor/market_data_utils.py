"""
Market Data Utilities module for Futures Market Analysis
This module contains functions for analyzing market data,
including premarket data, gold term structure, and interest rate impacts.
"""
import yfinance as yf
import pandas as pd
import datetime
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_premarket_data() -> Dict[str, Any]:
    """
    Get the latest premarket data for major futures contracts and indices
    """
    try:
        # Ticker symbols
        ES_FUTURES = "ES=F"  # S&P 500 E-mini
        GOLD_FUTURES = "GC=F"  # Gold Front Month
        TEN_YEAR_YIELD = "US10Y"  # 10-Year Treasury Yield (improved ticker)
        ALT_TEN_YEAR_YIELD = "^TNX"  # Alternative 10-Year Treasury Yield 
        TEN_YEAR_FUTURES = "ZN=F"  # 10-Year T-Note Futures (another alternative)
        VIX = "^VIX"  # Volatility Index
        
        # Additional tickers
        CRUDE_OIL = "CL=F"  # Crude Oil futures
        NATURAL_GAS = "NG=F"  # Natural Gas futures
        SILVER = "SI=F"  # Silver futures
        
        # Fetch data for multiple tickers at once
        tickers = [ES_FUTURES, GOLD_FUTURES, TEN_YEAR_YIELD, ALT_TEN_YEAR_YIELD, TEN_YEAR_FUTURES, VIX, CRUDE_OIL, NATURAL_GAS, SILVER]
        data = yf.download(tickers, period="1d", group_by='ticker')
        
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
                        "name": get_friendly_name(ticker),
                        "last_price": float(last_price),
                        "change": float(change),
                        "change_pct": float(change_pct),
                        "timestamp": str(datetime.datetime.now())
                    }
                else:
                    result[ticker] = {"name": get_friendly_name(ticker), "error": "No data available"}
            else:
                result[ticker] = {"name": get_friendly_name(ticker), "error": "Ticker not found in data"}
        
        # Add timestamp
        result["timestamp"] = str(datetime.datetime.now())
        
        return result
    except Exception as e:
        logger.error(f"Error fetching premarket data: {str(e)}")
        return {
            "error": f"Error fetching premarket data: {str(e)}",
            "timestamp": str(datetime.datetime.now())
        }

def get_friendly_name(ticker: str) -> str:
    """Get a friendly name for a given ticker symbol"""
    ticker_names = {
        "ES=F": "S&P 500 E-mini",
        "GC=F": "Gold Futures",
        "^TNX": "10-Year Treasury Yield",
        "US10Y": "10-Year Treasury Yield",
        "ZN=F": "10-Year T-Note Futures",
        "^VIX": "VIX (Volatility Index)",
        "CL=F": "Crude Oil Futures",
        "NG=F": "Natural Gas Futures",
        "SI=F": "Silver Futures"
    }
    return ticker_names.get(ticker, ticker)

def get_gold_term_structure() -> Dict[str, Any]:
    """
    Analyze gold futures term structure (GC1, GC2, GC3) and 
    calculate contango/backwardation metrics
    """
    try:
        # Gold futures contracts
        GC1 = "GC=F"       # Front month
        GC2 = "GCJ24.CMX"  # Second month
        GC3 = "GCK24.CMX"  # Third month
        GOLD_ETF = "GLD"   # SPDR Gold Trust ETF (spot gold proxy)
        
        # Fetch data for gold futures contracts
        tickers = [GC1, GC2, GC3, GOLD_ETF]
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
                    prices[ticker] = float(ticker_data['Close'].iloc[-1])
                    result["contracts"][ticker] = {
                        "name": get_gold_contract_name(ticker),
                        "price": float(ticker_data['Close'].iloc[-1]),
                        "volume": float(ticker_data['Volume'].iloc[-1]) if 'Volume' in ticker_data else 0,
                        "timestamp": str(ticker_data.index[-1])
                    }
                else:
                    result["contracts"][ticker] = {
                        "name": get_gold_contract_name(ticker),
                        "error": "No data available"
                    }
        
        # Calculate term structure metrics
        if GC1 in prices and GC2 in prices:
            # Calculate contango (positive) or backwardation (negative)
            front_next_spread = prices[GC2] - prices[GC1]
            front_next_pct = (front_next_spread / prices[GC1]) * 100
            
            result["term_structure"]["front_next_spread"] = float(front_next_spread)
            result["term_structure"]["front_next_percentage"] = float(front_next_pct)
            result["term_structure"]["structure"] = "contango" if front_next_spread > 0 else "backwardation"
            
            # Add further spreads if we have data for GC3
            if GC3 in prices:
                next_third_spread = prices[GC3] - prices[GC2]
                result["term_structure"]["next_third_spread"] = float(next_third_spread)
                
                # Determine the term structure pattern
                structure_type = determine_term_structure_type(front_next_spread, next_third_spread)
                result["term_structure"]["structure_type"] = structure_type
                
                # Get implications of the structure
                result["analysis"]["market_implications"] = get_term_structure_implications(structure_type)
            
            # Add ETF-futures basis if we have GLD data
            if GOLD_ETF in prices:
                # Approximate relationship between GLD and spot gold
                # 1 share of GLD represents approximately 1/10 oz of gold
                spot_gold_estimate = prices[GOLD_ETF] * 10
                futures_basis = prices[GC1] - spot_gold_estimate
                futures_basis_pct = (futures_basis / spot_gold_estimate) * 100
                
                result["term_structure"]["futures_basis"] = float(futures_basis)
                result["term_structure"]["futures_basis_percentage"] = float(futures_basis_pct)
        
        # Add timestamp
        result["timestamp"] = str(datetime.datetime.now())
        
        return result
    except Exception as e:
        logger.error(f"Error analyzing gold term structure: {str(e)}")
        return {
            "error": f"Error analyzing gold term structure: {str(e)}",
            "timestamp": str(datetime.datetime.now())
        }

def get_gold_contract_name(ticker: str) -> str:
    """Get a descriptive name for gold futures contracts"""
    if ticker == "GC=F":
        return "Gold Front Month"
    elif ticker == "GCJ24.CMX":
        return "Gold April 2024"
    elif ticker == "GCK24.CMX":
        return "Gold May 2024"
    elif ticker == "GLD":
        return "SPDR Gold Trust ETF"
    return ticker

def determine_term_structure_type(front_next_spread: float, next_third_spread: float) -> str:
    """Determine the type of term structure based on spreads"""
    if front_next_spread > 0 and next_third_spread > 0:
        return "Full Contango"
    elif front_next_spread < 0 and next_third_spread < 0:
        return "Full Backwardation"
    elif front_next_spread > 0 and next_third_spread < 0:
        return "Mixed (Contango near-term, Backwardation far-term)"
    elif front_next_spread < 0 and next_third_spread > 0:
        return "Mixed (Backwardation near-term, Contango far-term)"
    else:
        return "Flat Term Structure"

def get_term_structure_implications(structure_type: str) -> List[str]:
    """Get market implications based on term structure type"""
    implications = {
        "Full Contango": [
            "Traditional futures curve indicating adequate physical supply",
            "Storage costs and interest rates influence the premium in deferred contracts",
            "Often seen in well-supplied or surplus markets",
            "May indicate weaker near-term demand"
        ],
        "Full Backwardation": [
            "Indicates potential supply constraints or shortages",
            "Market values immediate delivery more than future delivery",
            "Can signal bullish conditions or supply disruptions",
            "Often associated with strong near-term demand"
        ],
        "Mixed (Contango near-term, Backwardation far-term)": [
            "Near-term supply appears adequate",
            "Potential concerns about longer-term supply disruptions",
            "Complex structure that may indicate transitioning market conditions",
            "Watch for changes in far-month contracts"
        ],
        "Mixed (Backwardation near-term, Contango far-term)": [
            "Current supply tightness or constraints",
            "Expectations that supply will normalize in the longer term",
            "Often seen during temporary supply disruptions",
            "Watch for resolution of short-term constraints"
        ],
        "Flat Term Structure": [
            "Market equilibrium with balanced supply and demand",
            "Little premium for storage or time value",
            "Often transitional between contango and backwardation",
            "May indicate uncertainty in market direction"
        ]
    }
    
    return implications.get(structure_type, ["Unknown term structure pattern"])

def get_interest_rate_impact() -> Dict[str, Any]:
    """
    Analyze the relationship between interest rates (10Y Treasury Yield) and gold prices
    """
    try:
        # Fetch data for gold and 10-year treasury yield
        GC = "GC=F"       # Gold futures
        TNX = "^TNX"      # 10-year treasury yield
        TIP = "TIP"       # iShares TIPS Bond ETF (inflation protected securities)
        
        # Fetch 90 days of data to analyze the relationship
        data = yf.download([GC, TNX, TIP], period="90d", group_by='ticker')
        
        result = {
            "current_data": {},
            "correlation": {},
            "analysis": {},
            "real_rates": {}
        }
        
        # Get current data
        if GC in data and TNX in data:
            gc_data = data[GC]
            tnx_data = data[TNX]
            
            if not gc_data.empty and not tnx_data.empty:
                # Current prices
                current_gold_price = float(gc_data['Close'].iloc[-1])
                current_treasury_yield = float(tnx_data['Close'].iloc[-1])
                
                result["current_data"]["gold_price"] = current_gold_price
                result["current_data"]["treasury_yield"] = current_treasury_yield
                
                # Get inflation expectations (using TIP ETF as a proxy or an estimated value)
                # In a real implementation, this would use market-based inflation expectations from TIPS or swaps
                estimated_inflation = 2.8  # Estimated figure
                if TIP in data and not data[TIP].empty:
                    # Using a simple proxy - in reality would use proper TIPS/Treasury spread calculation
                    tip_data = data[TIP]
                    tip_30d_change = ((tip_data['Close'].iloc[-1] / tip_data['Close'].iloc[-30]) - 1) * 100
                    if tip_30d_change > 0:
                        # Rising TIPS prices often signal higher inflation expectations
                        estimated_inflation = 3.2  # Adjusted higher for rising TIPS prices
                    else:
                        estimated_inflation = 2.4  # Adjusted lower for falling TIPS prices
                
                # Calculate real interest rate
                real_interest_rate = current_treasury_yield - estimated_inflation
                
                # Store real rates data
                result["real_rates"]["nominal_rate"] = round(current_treasury_yield, 2)
                result["real_rates"]["inflation_expectation"] = round(estimated_inflation, 1)
                result["real_rates"]["real_rate"] = round(real_interest_rate, 2)
                
                # Generate market implication
                if real_interest_rate < -1.0:
                    real_rate_implication = "Strong positive for gold. Deeply negative real rates make gold highly attractive as cash is rapidly losing value."
                elif real_interest_rate < 0:
                    real_rate_implication = "Positive for gold. Negative real rates make gold appealing as a store of value."
                elif real_interest_rate < 1.0:
                    real_rate_implication = "Neutral to slightly negative for gold. Slightly positive real rates create modest competition for gold."
                else:
                    real_rate_implication = "Negative for gold. Significantly positive real rates make interest-bearing assets more attractive than gold."
                
                result["real_rates"]["implication"] = real_rate_implication
                
                # Calculate 30-day changes
                gc_30d_change = ((gc_data['Close'].iloc[-1] / gc_data['Close'].iloc[-30]) - 1) * 100
                tnx_30d_change = tnx_data['Close'].iloc[-1] - tnx_data['Close'].iloc[-30]
                
                result["current_data"]["gold_30d_change_pct"] = float(gc_30d_change)
                result["current_data"]["treasury_yield_30d_change"] = float(tnx_30d_change)
                
                # Calculate correlation
                # First, align the data by date
                combined = pd.DataFrame({
                    'gold': gc_data['Close'],
                    'yield': tnx_data['Close']
                })
                combined = combined.dropna()  # Remove any rows with missing data
                
                if len(combined) > 30:  # Ensure we have enough data
                    # Calculate 30-day correlation
                    correlation_30d = combined['gold'].iloc[-30:].corr(combined['yield'].iloc[-30:])
                    result["correlation"]["correlation_30d"] = float(correlation_30d)
                    
                    # Calculate 90-day correlation
                    correlation_90d = combined['gold'].corr(combined['yield'])
                    result["correlation"]["correlation_90d"] = float(correlation_90d)
                    
                    # Interpret correlation
                    if correlation_30d < -0.5:
                        relationship = "Strong negative relationship"
                        implication = "Rising yields have been significantly pressuring gold prices"
                    elif correlation_30d < -0.2:
                        relationship = "Moderate negative relationship"
                        implication = "Rising yields have been moderately pressuring gold prices"
                    elif correlation_30d > 0.5:
                        relationship = "Strong positive relationship"
                        implication = "Gold has been rising with yields, possibly due to inflation concerns"
                    elif correlation_30d > 0.2:
                        relationship = "Moderate positive relationship"
                        implication = "Gold has been moderately rising with yields"
                    else:
                        relationship = "Weak or no relationship"
                        implication = "Gold prices have been showing little sensitivity to yield changes"
                    
                    result["analysis"]["current_relationship"] = relationship
                    result["analysis"]["market_implication"] = implication
                    
                    # Compare 30d vs 90d correlation for trend
                    correlation_change = correlation_30d - correlation_90d
                    if correlation_change > 0.2:
                        trend = "The gold-yield relationship is becoming more positive"
                    elif correlation_change < -0.2:
                        trend = "The gold-yield relationship is becoming more negative"
                    else:
                        trend = "The gold-yield relationship is relatively stable"
                    
                    result["analysis"]["correlation_trend"] = trend
        
        # Add timestamp
        result["timestamp"] = str(datetime.datetime.now())
        
        return result
    except Exception as e:
        logger.error(f"Error analyzing interest rate impact: {str(e)}")
        return {
            "error": f"Error analyzing interest rate impact: {str(e)}",
            "timestamp": str(datetime.datetime.now())
        }

def analyze_market_sentiment() -> Dict[str, Any]:
    """
    Analyze market sentiment using VIX and its relationship to gold
    """
    try:
        # Fetch data for gold and VIX
        GC = "GC=F"       # Gold futures
        VIX = "^VIX"      # Volatility index
        
        # Fetch 90 days of data to analyze the relationship
        data = yf.download([GC, VIX], period="90d", group_by='ticker')
        
        result = {
            "current_data": {},
            "correlation": {},
            "analysis": {}
        }
        
        # Get current data
        if GC in data and VIX in data:
            gc_data = data[GC]
            vix_data = data[VIX]
            
            if not gc_data.empty and not vix_data.empty:
                # Current values
                result["current_data"]["gold_price"] = float(gc_data['Close'].iloc[-1])
                result["current_data"]["vix"] = float(vix_data['Close'].iloc[-1])
                
                # Calculate 30-day changes
                gc_30d_change = ((gc_data['Close'].iloc[-1] / gc_data['Close'].iloc[-30]) - 1) * 100
                vix_30d_change = ((vix_data['Close'].iloc[-1] / vix_data['Close'].iloc[-30]) - 1) * 100
                
                result["current_data"]["gold_30d_change_pct"] = float(gc_30d_change)
                result["current_data"]["vix_30d_change_pct"] = float(vix_30d_change)
                
                # VIX level interpretation
                if vix_data['Close'].iloc[-1] < 15:
                    vix_level = "Very Low"
                    vix_implication = "Market is complacent, potential vulnerability to shocks"
                elif vix_data['Close'].iloc[-1] < 20:
                    vix_level = "Low"
                    vix_implication = "Market relatively calm, moderate risk appetite"
                elif vix_data['Close'].iloc[-1] < 30:
                    vix_level = "Moderate"
                    vix_implication = "Normal market uncertainty, balanced risk perception"
                elif vix_data['Close'].iloc[-1] < 40:
                    vix_level = "Elevated"
                    vix_implication = "Market stress, risk aversion increasing"
                else:
                    vix_level = "High"
                    vix_implication = "Market fear, significant risk aversion"
                
                result["analysis"]["vix_level"] = vix_level
                result["analysis"]["vix_implication"] = vix_implication
                
                # Calculate correlation between gold and VIX
                # First, align the data by date
                combined = pd.DataFrame({
                    'gold': gc_data['Close'],
                    'vix': vix_data['Close']
                })
                combined = combined.dropna()  # Remove any rows with missing data
                
                if len(combined) > 30:  # Ensure we have enough data
                    # Calculate 30-day correlation
                    correlation_30d = combined['gold'].iloc[-30:].corr(combined['vix'].iloc[-30:])
                    result["correlation"]["correlation_30d"] = float(correlation_30d)
                    
                    # Interpret correlation
                    if correlation_30d > 0.5:
                        relationship = "Strong positive relationship"
                        implication = "Gold acting as a safe haven during market stress"
                    elif correlation_30d > 0.2:
                        relationship = "Moderate positive relationship"
                        implication = "Gold somewhat acting as a safe haven"
                    elif correlation_30d < -0.5:
                        relationship = "Strong negative relationship"
                        implication = "Gold moving counter to market fear, unusual pattern"
                    elif correlation_30d < -0.2:
                        relationship = "Moderate negative relationship"
                        implication = "Gold not acting as a traditional safe haven"
                    else:
                        relationship = "Weak or no relationship"
                        implication = "Gold price movements relatively independent of market fear"
                    
                    result["analysis"]["gold_vix_relationship"] = relationship
                    result["analysis"]["market_implication"] = implication
        
        # Add timestamp
        result["timestamp"] = str(datetime.datetime.now())
        
        return result
    except Exception as e:
        logger.error(f"Error analyzing market sentiment: {str(e)}")
        return {
            "error": f"Error analyzing market sentiment: {str(e)}",
            "timestamp": str(datetime.datetime.now())
        }

def detect_gold_cycle_thresholds() -> Dict[str, Any]:
    """
    Detect potential gold cycle turning points based on historical thresholds
    """
    try:
        # Fetch gold price data
        GC = "GC=F"  # Gold futures
        
        # Fetch a longer period for cycle analysis
        data = yf.download(GC, period="2y", interval="1d")
        
        result = {
            "current_data": {},
            "technical_metrics": {},
            "cycle_analysis": {}
        }
        
        if not data.empty:
            # Current price and recent changes
            current_price = float(data['Close'].iloc[-1])
            price_52w_high = float(data['High'].max())
            price_52w_low = float(data['Low'].min())
            
            # Calculate distances from extremes
            pct_from_high = ((current_price / price_52w_high) - 1) * 100
            pct_from_low = ((current_price / price_52w_low) - 1) * 100
            
            result["current_data"]["current_price"] = current_price
            result["current_data"]["price_52w_high"] = price_52w_high
            result["current_data"]["price_52w_low"] = price_52w_low
            result["current_data"]["pct_from_52w_high"] = float(pct_from_high)
            result["current_data"]["pct_from_52w_low"] = float(pct_from_low)
            
            # Calculate moving averages
            data['MA50'] = data['Close'].rolling(window=50).mean()
            data['MA200'] = data['Close'].rolling(window=200).mean()
            
            ma50_current = data['MA50'].iloc[-1]
            ma200_current = data['MA200'].iloc[-1]
            
            result["technical_metrics"]["ma50"] = float(ma50_current)
            result["technical_metrics"]["ma200"] = float(ma200_current)
            result["technical_metrics"]["ma_ratio"] = float(ma50_current / ma200_current)
            
            # Calculate RSI (14-period)
            delta = data['Close'].diff()
            gain = delta.where(delta > 0, 0).rolling(window=14).mean()
            loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            current_rsi = float(rsi.iloc[-1])
            result["technical_metrics"]["rsi_14"] = current_rsi
            
            # Cycle analysis based on thresholds
            if current_rsi > 70 and pct_from_high > -2:
                cycle_position = "Potential cycle top"
                risk_level = "High risk of correction"
                action_recommendation = "Consider reducing exposure or implementing hedges"
            elif current_rsi < 30 and pct_from_low < 10:
                cycle_position = "Potential cycle bottom"
                risk_level = "Oversold conditions"
                action_recommendation = "Potential accumulation opportunity"
            elif ma50_current > ma200_current * 1.1:
                cycle_position = "Strong uptrend"
                risk_level = "Moderate-to-high risk of pullback"
                action_recommendation = "Maintain positions but be alert to reversal signals"
            elif ma50_current < ma200_current * 0.95:
                cycle_position = "Strong downtrend"
                risk_level = "Continued downside pressure possible"
                action_recommendation = "Caution on new positions, wait for stabilization"
            else:
                cycle_position = "Mid-cycle or transitional phase"
                risk_level = "Moderate risk"
                action_recommendation = "Monitor for clear trend development"
            
            result["cycle_analysis"]["cycle_position"] = cycle_position
            result["cycle_analysis"]["risk_level"] = risk_level
            result["cycle_analysis"]["action_recommendation"] = action_recommendation
        
        # Add timestamp
        result["timestamp"] = str(datetime.datetime.now())
        
        return result
    except Exception as e:
        logger.error(f"Error detecting gold cycle thresholds: {str(e)}")
        return {
            "error": f"Error detecting gold cycle thresholds: {str(e)}",
            "timestamp": str(datetime.datetime.now())
        }

def get_economic_expectations() -> Dict[str, Any]:
    """
    Analyze current economic expectations and their impact on gold
    """
    try:
        # For a complete implementation, this would pull data from economic indicators
        # and central bank communications. For now, we'll focus on yield curve as a proxy.
        
        # Fetch treasury yield data
        tickers = ['^IRX', '^FVX', '^TNX', '^TYX']  # 13-week, 5-year, 10-year, 30-year
        data = yf.download(tickers, period="30d", group_by='ticker')
        
        result = {
            "yield_curve": {},
            "inflation_expectations": {},
            "economic_outlook": {}
        }
        
        # Process yield curve data if available
        if all(ticker in data for ticker in tickers):
            latest_date = min(data[ticker]['Close'].index[-1] for ticker in tickers)
            
            # Get latest yields
            t13w = float(data['^IRX']['Close'].loc[latest_date])
            t5y = float(data['^FVX']['Close'].loc[latest_date])
            t10y = float(data['^TNX']['Close'].loc[latest_date])
            t30y = float(data['^TYX']['Close'].loc[latest_date])
            
            result["yield_curve"]["t13w"] = t13w
            result["yield_curve"]["t5y"] = t5y
            result["yield_curve"]["t10y"] = t10y
            result["yield_curve"]["t30y"] = t30y
            
            # Calculate key spreads
            t10y_t13w_spread = t10y - t13w  # 10yr-3mo spread (recession indicator)
            t30y_t10y_spread = t30y - t10y  # Long-end steepness
            t10y_t5y_spread = t10y - t5y    # Belly of the curve
            
            result["yield_curve"]["t10y_t13w_spread"] = float(t10y_t13w_spread)
            result["yield_curve"]["t30y_t10y_spread"] = float(t30y_t10y_spread)
            result["yield_curve"]["t10y_t5y_spread"] = float(t10y_t5y_spread)
            
            # Analyze yield curve shape
            if t10y_t13w_spread < 0:
                curve_shape = "Inverted (10yr-3mo)"
                recession_risk = "Elevated recession risk signal"
            elif t10y_t13w_spread < 0.5:
                curve_shape = "Flat to slightly positive"
                recession_risk = "Moderate recession risk"
            else:
                curve_shape = "Positive slope"
                recession_risk = "Lower recession risk"
            
            result["economic_outlook"]["yield_curve_shape"] = curve_shape
            result["economic_outlook"]["recession_signal"] = recession_risk
            
            # Inflation expectations (simple proxy based on long-end yields)
            if t30y > 4.5:
                inflation_expectation = "Elevated long-term inflation expectations"
            elif t30y > 3.5:
                inflation_expectation = "Moderate long-term inflation expectations"
            else:
                inflation_expectation = "Contained long-term inflation expectations"
            
            result["inflation_expectations"]["long_term_view"] = inflation_expectation
            
            # Gold implications based on the above
            if t10y_t13w_spread < 0 and t30y < 4.0:
                gold_implication = "Potentially supportive for gold: recession concerns with moderate inflation"
            elif t10y_t13w_spread < 0 and t30y > 4.5:
                gold_implication = "Mixed for gold: recession concerns but high inflation expectations may prompt higher real rates"
            elif t10y_t13w_spread > 1.0:
                gold_implication = "Potentially challenging for gold: strong growth outlook may reduce safe haven demand"
            else:
                gold_implication = "Neutral for gold: balanced economic signals"
            
            result["economic_outlook"]["gold_implication"] = gold_implication
        
        # Add timestamp
        result["timestamp"] = str(datetime.datetime.now())
        
        return result
    except Exception as e:
        logger.error(f"Error analyzing economic expectations: {str(e)}")
        return {
            "error": f"Error analyzing economic expectations: {str(e)}",
            "timestamp": str(datetime.datetime.now())
        }

def get_comprehensive_analysis() -> Dict[str, Any]:
    """
    Combine all analyses into a comprehensive market report
    """
    try:
        # Collect data from all analysis functions
        premarket = get_premarket_data()
        term_structure = get_gold_term_structure()
        interest_impact = get_interest_rate_impact()
        sentiment = analyze_market_sentiment()
        cycle = detect_gold_cycle_thresholds()
        economic = get_economic_expectations()
        
        # Create comprehensive report
        report = {
            "summary": {
                "timestamp": str(datetime.datetime.now()),
                "gold_price": None,
                "gold_trend": None,
                "risk_assessment": None,
                "key_insights": []
            },
            "detailed_analysis": {
                "premarket": premarket,
                "term_structure": term_structure,
                "interest_rates": interest_impact,
                "market_sentiment": sentiment,
                "gold_cycle": cycle,
                "economic_outlook": economic
            }
        }
        
        # Extract gold price if available
        if "GC=F" in premarket and "last_price" in premarket["GC=F"]:
            report["summary"]["gold_price"] = premarket["GC=F"]["last_price"]
        
        # Combine insights from all analyses
        insights = []
        
        # Check for cycle insights
        if "cycle_analysis" in cycle and "cycle_position" in cycle["cycle_analysis"]:
            insights.append(f"Gold cycle: {cycle['cycle_analysis']['cycle_position']}")
        
        # Check for term structure insights
        if "term_structure" in term_structure and "structure" in term_structure["term_structure"]:
            insights.append(f"Term structure: {term_structure['term_structure']['structure']}")
        
        # Check for interest rate insights
        if "analysis" in interest_impact and "market_implication" in interest_impact["analysis"]:
            insights.append(f"Interest rates: {interest_impact['analysis']['market_implication']}")
        
        # Check for economic insights
        if "economic_outlook" in economic and "gold_implication" in economic["economic_outlook"]:
            insights.append(f"Economic outlook: {economic['economic_outlook']['gold_implication']}")
        
        # Add insights to summary
        report["summary"]["key_insights"] = insights
        
        # Overall risk assessment (simple aggregation)
        risk_signals = []
        
        # Check cycle risk
        if "cycle_analysis" in cycle and "risk_level" in cycle["cycle_analysis"]:
            risk_signals.append(cycle["cycle_analysis"]["risk_level"])
        
        # Check economic risk
        if "economic_outlook" in economic and "recession_signal" in economic["economic_outlook"]:
            risk_signals.append(economic["economic_outlook"]["recession_signal"])
        
        # Simple risk aggregation
        high_risk_count = sum(1 for signal in risk_signals if "high" in signal.lower())
        moderate_risk_count = sum(1 for signal in risk_signals if "moderate" in signal.lower())
        
        if high_risk_count > 0:
            overall_risk = "High"
        elif moderate_risk_count > 0:
            overall_risk = "Moderate"
        else:
            overall_risk = "Low"
        
        report["summary"]["risk_assessment"] = overall_risk
        
        return report
    except Exception as e:
        logger.error(f"Error generating comprehensive analysis: {str(e)}")
        return {
            "error": f"Error generating comprehensive analysis: {str(e)}",
            "timestamp": str(datetime.datetime.now())
        }