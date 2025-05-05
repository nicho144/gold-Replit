"""
Improved Market Data Utilities
This module provides functions for retrieving and analyzing market data
with enhanced error handling and reliability features.
"""
import os
import logging
import datetime
import random
from typing import Dict, List, Any, Optional, Union, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Constants for retry mechanism
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2
JITTER_MAX_MS = 500  # Add random jitter to avoid synchronized retries

# Try to import yfinance with fallback
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    logger.warning("yfinance not installed, market data functions will be limited")
    YFINANCE_AVAILABLE = False

def get_price_with_retry(ticker: str, max_retries: int = MAX_RETRIES) -> Optional[float]:
    """
    Attempts to retrieve the market price for a given ticker with retry logic
    
    Parameters:
    - ticker: The ticker symbol to look up
    - max_retries: Maximum number of retry attempts
    
    Returns:
    - Float price or None if unsuccessful after retries
    """
    if not YFINANCE_AVAILABLE:
        logger.error("yfinance not available, cannot retrieve price")
        return None
    
    for attempt in range(max_retries):
        try:
            # Add jitter to avoid synchronized retries
            if attempt > 0:
                jitter_ms = random.randint(0, JITTER_MAX_MS) / 1000.0
                time.sleep(RETRY_DELAY_SECONDS + jitter_ms)
                logger.info(f"Retry attempt {attempt+1}/{max_retries} for ticker {ticker}")
            
            ticker_obj = yf.Ticker(ticker)
            hist = ticker_obj.history(period="1d")
            
            if hist.empty:
                logger.warning(f"Empty history returned for {ticker}, attempt {attempt+1}/{max_retries}")
                continue
            
            if "Close" in hist.columns:
                price = float(hist["Close"].iloc[-1])
                logger.info(f"Successfully retrieved price for {ticker}: {price}")
                return price
            else:
                logger.warning(f"No Close column in history for {ticker}, attempt {attempt+1}/{max_retries}")
        except Exception as e:
            logger.error(f"Error retrieving price for {ticker}, attempt {attempt+1}/{max_retries}: {str(e)}")
            if attempt == max_retries - 1:
                logger.error(f"All {max_retries} attempts failed for {ticker}")
    
    # Try an alternative method if all direct attempts failed
    try:
        logger.info(f"Trying alternative method for {ticker}")
        ticker_data = yf.download(ticker, period="1d", progress=False)
        if not ticker_data.empty and "Close" in ticker_data.columns:
            price = float(ticker_data["Close"].iloc[-1])
            logger.info(f"Alternative method success for {ticker}: {price}")
            return price
    except Exception as e:
        logger.error(f"Alternative method failed for {ticker}: {str(e)}")
    
    return None

def get_ticker_info_with_retry(ticker: str, max_retries: int = MAX_RETRIES) -> Optional[Dict[str, Any]]:
    """
    Retrieves ticker information with retry logic
    
    Parameters:
    - ticker: The ticker symbol to look up
    - max_retries: Maximum number of retry attempts
    
    Returns:
    - Dictionary with ticker information or None if unsuccessful
    """
    if not YFINANCE_AVAILABLE:
        logger.error("yfinance not available, cannot retrieve ticker info")
        return None
    
    for attempt in range(max_retries):
        try:
            # Add jitter to avoid synchronized retries
            if attempt > 0:
                jitter_ms = random.randint(0, JITTER_MAX_MS) / 1000.0
                time.sleep(RETRY_DELAY_SECONDS + jitter_ms)
                logger.info(f"Retry attempt {attempt+1}/{max_retries} for ticker info {ticker}")
            
            ticker_obj = yf.Ticker(ticker)
            info = ticker_obj.info
            
            if info and len(info) > 0:
                logger.info(f"Successfully retrieved info for {ticker}")
                return info
            else:
                logger.warning(f"Empty info returned for {ticker}, attempt {attempt+1}/{max_retries}")
        except Exception as e:
            logger.error(f"Error retrieving info for {ticker}, attempt {attempt+1}/{max_retries}: {str(e)}")
            if attempt == max_retries - 1:
                logger.error(f"All {max_retries} attempts failed for {ticker} info")
    
    return None

def get_price_history_with_retry(ticker: str, period: str = "1y", interval: str = "1d", max_retries: int = MAX_RETRIES) -> Optional[pd.DataFrame]:
    """
    Retrieves historical price data with retry logic
    
    Parameters:
    - ticker: The ticker symbol to look up
    - period: Time period to retrieve (e.g., "1d", "5d", "1mo", "3mo", "1y", "2y", "5y", "10y", "ytd", "max")
    - interval: Data interval (e.g., "1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo")
    - max_retries: Maximum number of retry attempts
    
    Returns:
    - DataFrame with price history or None if unsuccessful
    """
    if not YFINANCE_AVAILABLE:
        logger.error("yfinance not available, cannot retrieve price history")
        return None
    
    for attempt in range(max_retries):
        try:
            # Add jitter to avoid synchronized retries
            if attempt > 0:
                jitter_ms = random.randint(0, JITTER_MAX_MS) / 1000.0
                time.sleep(RETRY_DELAY_SECONDS + jitter_ms)
                logger.info(f"Retry attempt {attempt+1}/{max_retries} for price history {ticker}")
            
            ticker_obj = yf.Ticker(ticker)
            history = ticker_obj.history(period=period, interval=interval)
            
            if not history.empty:
                logger.info(f"Successfully retrieved history for {ticker} with {len(history)} data points")
                return history
            else:
                logger.warning(f"Empty history returned for {ticker}, attempt {attempt+1}/{max_retries}")
        except Exception as e:
            logger.error(f"Error retrieving history for {ticker}, attempt {attempt+1}/{max_retries}: {str(e)}")
            if attempt == max_retries - 1:
                logger.error(f"All {max_retries} attempts failed for {ticker} history")
    
    # Try an alternative method if all direct attempts failed
    try:
        logger.info(f"Trying alternative method for {ticker} history")
        ticker_data = yf.download(ticker, period=period, interval=interval, progress=False)
        if not ticker_data.empty:
            logger.info(f"Alternative method success for {ticker} history: {len(ticker_data)} data points")
            return ticker_data
    except Exception as e:
        logger.error(f"Alternative method failed for {ticker} history: {str(e)}")
    
    return None

def get_multiple_tickers_with_retry(tickers: List[str], period: str = "1d", max_retries: int = MAX_RETRIES) -> Dict[str, Optional[float]]:
    """
    Retrieves prices for multiple tickers with optimized batch retrieval
    
    Parameters:
    - tickers: List of ticker symbols to look up
    - period: Time period to retrieve
    - max_retries: Maximum number of retry attempts
    
    Returns:
    - Dictionary mapping ticker symbols to their prices or None if unsuccessful
    """
    if not YFINANCE_AVAILABLE:
        logger.error("yfinance not available, cannot retrieve prices")
        return {ticker: None for ticker in tickers}
    
    results = {}
    
    # Try batch download first (more efficient)
    for attempt in range(max_retries):
        try:
            # Add jitter to avoid synchronized retries
            if attempt > 0:
                jitter_ms = random.randint(0, JITTER_MAX_MS) / 1000.0
                time.sleep(RETRY_DELAY_SECONDS + jitter_ms)
                logger.info(f"Retry attempt {attempt+1}/{max_retries} for batch ticker download")
            
            tickers_str = " ".join(tickers)
            data = yf.download(tickers_str, period=period, progress=False)
            
            # If we have multiple tickers, Close will be a DataFrame
            if isinstance(data.get('Close', None), pd.DataFrame):
                for ticker in tickers:
                    if ticker in data['Close'].columns:
                        last_value = data['Close'][ticker].iloc[-1]
                        if not pd.isna(last_value):
                            results[ticker] = float(last_value)
            # If we only have one ticker, Close will be a Series
            elif 'Close' in data.columns:
                if len(tickers) == 1:
                    last_value = data['Close'].iloc[-1]
                    if not pd.isna(last_value):
                        results[tickers[0]] = float(last_value)
            
            logger.info(f"Batch download retrieved {len(results)} prices out of {len(tickers)} tickers")
            
            # If we got all tickers, we're done
            if len(results) == len(tickers):
                return results
            
            # Otherwise, let's continue to the next attempt or individual fallback
            if attempt == max_retries - 1:
                logger.warning(f"Batch download couldn't retrieve all tickers after {max_retries} attempts")
        except Exception as e:
            logger.error(f"Error in batch ticker download, attempt {attempt+1}/{max_retries}: {str(e)}")
            if attempt == max_retries - 1:
                logger.error(f"All {max_retries} batch attempts failed")
    
    # For any tickers we couldn't get, try individual retrieval
    missing_tickers = [ticker for ticker in tickers if ticker not in results]
    for ticker in missing_tickers:
        price = get_price_with_retry(ticker, max_retries)
        results[ticker] = price
    
    logger.info(f"Final results: retrieved {sum(1 for v in results.values() if v is not None)} prices out of {len(tickers)} tickers")
    return results

def get_gold_futures_chain() -> Dict[str, Any]:
    """
    Retrieves the gold futures chain data from Yahoo Finance
    
    Returns:
    - Dictionary with gold futures data or empty dict if unavailable
    """
    if not YFINANCE_AVAILABLE:
        logger.error("yfinance not available, cannot retrieve gold futures chain")
        return {}
    
    # Define common gold futures root symbols
    gold_roots = ["GC", "MGC"]
    futures_chain = {}
    
    for root in gold_roots:
        try:
            # Get the front month contract
            front_month = f"{root}=F"
            front_month_data = yf.Ticker(front_month)
            
            # Try to get options expiration dates which can help identify future contracts
            try:
                expirations = front_month_data.options
                if expirations:
                    logger.info(f"Found {len(expirations)} expiration dates for {front_month}")
                    futures_chain[f"{root}_expirations"] = expirations
            except:
                logger.warning(f"Could not retrieve options data for {front_month}")
            
            # Try to get contract months from the front month ticker info
            try:
                info = front_month_data.info
                if "contractSymbol" in info:
                    futures_chain[f"{root}_front_contract"] = info["contractSymbol"]
                    logger.info(f"Front month contract for {root}: {info['contractSymbol']}")
            except:
                logger.warning(f"Could not retrieve contract info for {front_month}")
            
            # Get price data for current front month
            try:
                price = get_price_with_retry(front_month)
                if price:
                    futures_chain[f"{root}_front_price"] = price
                    logger.info(f"Front month price for {root}: {price}")
            except:
                logger.warning(f"Could not retrieve price for {front_month}")
                
        except Exception as e:
            logger.error(f"Error retrieving gold futures chain for {root}: {str(e)}")
    
    # For COMEX gold futures, try specific contract months
    # Current year and next year codes
    current_year = datetime.now().year % 100
    next_year = (datetime.now().year + 1) % 100
    
    # Month codes: F(Jan), G(Feb), H(Mar), J(Apr), K(May), M(Jun), N(Jul), Q(Aug), U(Sep), V(Oct), X(Nov), Z(Dec)
    month_codes = {
        1: "F", 2: "G", 3: "H", 4: "J", 5: "K", 6: "M",
        7: "N", 8: "Q", 9: "U", 10: "V", 11: "X", 12: "Z"
    }
    
    # Current month and next few months
    current_month = datetime.now().month
    
    contract_months = []
    for i in range(6):  # Get current month and next 5 months
        month_idx = ((current_month - 1 + i) % 12) + 1
        year = current_year if month_idx >= current_month else next_year
        contract_months.append((month_idx, year))
    
    # Create contract symbols and get prices
    comex_prices = {}
    for month_idx, year in contract_months:
        month_code = month_codes[month_idx]
        contract = f"GC{month_code}{year}.CMX"
        price = get_price_with_retry(contract)
        if price:
            comex_prices[contract] = price
            logger.info(f"COMEX contract {contract}: {price}")
    
    if comex_prices:
        futures_chain["comex_prices"] = comex_prices
    
    return futures_chain

def get_gold_term_structure_data() -> Dict[str, Any]:
    """
    Analyzes gold futures term structure
    
    Returns:
    - Dictionary with term structure data and analysis
    """
    result = {
        "prices": {},
        "spreads": {},
        "open_interest": {},
        "analysis": {},
        "timestamp": str(datetime.now())
    }
    
    try:
        # Get futures chain data
        futures_chain = get_gold_futures_chain()
        if not futures_chain:
            logger.warning("Could not retrieve gold futures chain data")
            result["error"] = "Could not retrieve gold futures data"
            return result
        
        # Process COMEX prices if available
        if "comex_prices" in futures_chain and futures_chain["comex_prices"]:
            comex_contracts = sorted(futures_chain["comex_prices"].keys())
            
            # Front month
            if len(comex_contracts) > 0:
                front_month = comex_contracts[0]
                result["prices"]["front_month"] = {
                    "contract": front_month,
                    "price": futures_chain["comex_prices"][front_month]
                }
            
            # Second month
            if len(comex_contracts) > 1:
                second_month = comex_contracts[1]
                result["prices"]["second_month"] = {
                    "contract": second_month,
                    "price": futures_chain["comex_prices"][second_month]
                }
            
            # Third month
            if len(comex_contracts) > 2:
                third_month = comex_contracts[2]
                result["prices"]["third_month"] = {
                    "contract": third_month,
                    "price": futures_chain["comex_prices"][third_month]
                }
            
            # Calculate spreads
            if "front_month" in result["prices"] and "second_month" in result["prices"]:
                front_price = result["prices"]["front_month"]["price"]
                second_price = result["prices"]["second_month"]["price"]
                result["spreads"]["gc1_gc2"] = round(front_price - second_price, 2)
            
            if "second_month" in result["prices"] and "third_month" in result["prices"]:
                second_price = result["prices"]["second_month"]["price"]
                third_price = result["prices"]["third_month"]["price"]
                result["spreads"]["gc2_gc3"] = round(second_price - third_price, 2)
        else:
            # Fallback to GC=F for front month
            front_price = get_price_with_retry("GC=F")
            if front_price:
                result["prices"]["front_month"] = {
                    "contract": "GC=F",
                    "price": front_price
                }
        
        # For open interest, we'd ideally use an API that provides this data
        # For now, we can estimate it based on volume or provide placeholder for demonstration
        if "GC_front_contract" in futures_chain and "GC_front_price" in futures_chain:
            # Placeholder for open interest data
            # In a real implementation, this would come from a data provider API
            result["open_interest"]["front_month_oi"] = "Data not available"
            result["open_interest"]["front_month_oi_change"] = "Data not available"
            result["open_interest"]["exhaustion_signal"] = "Cannot determine without open interest data"
        
        # Analyze term structure
        if "gc1_gc2" in result["spreads"]:
            gc1_gc2_spread = result["spreads"]["gc1_gc2"]
            
            if gc1_gc2_spread < -5:
                structure_type = "Steep contango"
                implication = "Significant carrying costs and/or weak immediate demand relative to future expectations"
            elif gc1_gc2_spread < 0:
                structure_type = "Contango"
                implication = "Normal market structure with modest carrying costs"
            elif gc1_gc2_spread < 5:
                structure_type = "Mild backwardation"
                implication = "Tight physical supply or increased immediate demand"
            else:
                structure_type = "Steep backwardation"
                implication = "Significant supply shortage or strong immediate demand"
            
            result["analysis"]["structure_type"] = structure_type
            result["analysis"]["implication"] = implication
        
        return result
    except Exception as e:
        logger.error(f"Error analyzing gold term structure: {str(e)}")
        result["error"] = str(e)
        return result

def get_premarket_data() -> Dict[str, Any]:
    """
    Retrieves premarket data for key market indicators
    
    Returns:
    - Dictionary with premarket data for key futures, ETFs, etc.
    """
    result = {
        "equities": {},
        "metals": {},
        "treasuries": {},
        "volatility": {},
        "timestamp": str(datetime.now())
    }
    
    try:
        # Equity futures
        equity_tickers = ["ES=F", "NQ=F", "YM=F", "RTY=F"]  # S&P, Nasdaq, Dow, Russell
        equity_prices = get_multiple_tickers_with_retry(equity_tickers)
        
        for ticker, price in equity_prices.items():
            if price is not None:
                symbol_map = {
                    "ES=F": "S&P 500 Futures",
                    "NQ=F": "Nasdaq Futures",
                    "YM=F": "Dow Futures",
                    "RTY=F": "Russell 2000 Futures"
                }
                result["equities"][ticker] = {
                    "price": price,
                    "name": symbol_map.get(ticker, ticker)
                }
        
        # Metal futures
        metal_tickers = ["GC=F", "SI=F", "PL=F", "HG=F"]  # Gold, Silver, Platinum, Copper
        metal_prices = get_multiple_tickers_with_retry(metal_tickers)
        
        for ticker, price in metal_prices.items():
            if price is not None:
                symbol_map = {
                    "GC=F": "Gold Futures",
                    "SI=F": "Silver Futures",
                    "PL=F": "Platinum Futures",
                    "HG=F": "Copper Futures"
                }
                result["metals"][ticker] = {
                    "price": price,
                    "name": symbol_map.get(ticker, ticker)
                }
        
        # Treasury futures/rates
        treasury_tickers = ["ZN=F", "ZT=F", "TLT", "IEF"]  # 10Y, 5Y Futures, 20Y ETF, 7-10Y ETF
        treasury_prices = get_multiple_tickers_with_retry(treasury_tickers)
        
        for ticker, price in treasury_prices.items():
            if price is not None:
                symbol_map = {
                    "ZN=F": "10-Year Treasury Futures",
                    "ZT=F": "5-Year Treasury Futures",
                    "TLT": "20+ Year Treasury ETF",
                    "IEF": "7-10 Year Treasury ETF"
                }
                result["treasuries"][ticker] = {
                    "price": price,
                    "name": symbol_map.get(ticker, ticker)
                }
        
        # Volatility
        volatility_tickers = ["^VIX", "VIXY", "SVXY"]  # VIX, Long VIX ETF, Short VIX ETF
        volatility_prices = get_multiple_tickers_with_retry(volatility_tickers)
        
        for ticker, price in volatility_prices.items():
            if price is not None:
                symbol_map = {
                    "^VIX": "CBOE Volatility Index",
                    "VIXY": "Long VIX ETF",
                    "SVXY": "Short VIX ETF"
                }
                result["volatility"][ticker] = {
                    "price": price,
                    "name": symbol_map.get(ticker, ticker)
                }
        
        return result
    except Exception as e:
        logger.error(f"Error retrieving premarket data: {str(e)}")
        result["error"] = str(e)
        return result

def detect_market_exhaustion(ticker: str, lookback_days: int = 20) -> Dict[str, Any]:
    """
    Detects potential market exhaustion signals for a given ticker
    
    Parameters:
    - ticker: The ticker symbol to analyze
    - lookback_days: Number of days to look back for analysis
    
    Returns:
    - Dictionary with exhaustion analysis
    """
    result = {
        "ticker": ticker,
        "signals": [],
        "current_price": None,
        "lookback_days": lookback_days,
        "timestamp": str(datetime.now())
    }
    
    try:
        # Get historical data
        hist = get_price_history_with_retry(ticker, period=f"{lookback_days+10}d", interval="1d")
        if hist is None or hist.empty:
            logger.warning(f"Could not retrieve historical data for {ticker}")
            result["error"] = f"Could not retrieve historical data for {ticker}"
            return result
        
        # Ensure we have enough data
        if len(hist) < lookback_days:
            logger.warning(f"Insufficient historical data for {ticker}: {len(hist)} days")
            result["error"] = f"Insufficient historical data: {len(hist)} days"
            return result
        
        # Work with the most recent data
        hist = hist.iloc[-lookback_days:]
        
        # Store current price
        if "Close" in hist.columns:
            result["current_price"] = float(hist["Close"].iloc[-1])
        
        # Calculate price change
        if "Close" in hist.columns:
            first_price = float(hist["Close"].iloc[0])
            last_price = float(hist["Close"].iloc[-1])
            price_change_pct = (last_price / first_price - 1) * 100
            result["price_change_pct"] = round(price_change_pct, 2)
        
        # Detect potential exhaustion signals
        
        # 1. Check for consecutive price moves in same direction
        if "Close" in hist.columns:
            daily_returns = hist["Close"].pct_change().dropna()
            positive_days = sum(1 for r in daily_returns.iloc[-5:] if r > 0)
            negative_days = 5 - positive_days
            
            if positive_days >= 5:
                result["signals"].append({
                    "type": "consecutive_moves",
                    "description": "5 consecutive up days may indicate buying exhaustion"
                })
            elif negative_days >= 5:
                result["signals"].append({
                    "type": "consecutive_moves",
                    "description": "5 consecutive down days may indicate selling exhaustion"
                })
        
        # 2. Check for price extremes relative to moving averages
        if "Close" in hist.columns:
            hist["MA20"] = hist["Close"].rolling(window=20).mean()
            last_close = float(hist["Close"].iloc[-1])
            last_ma20 = float(hist["MA20"].iloc[-1]) if not pd.isna(hist["MA20"].iloc[-1]) else None
            
            if last_ma20 and last_close < last_ma20 * 0.9:
                result["signals"].append({
                    "type": "oversold",
                    "description": "Price is more than 10% below 20-day moving average"
                })
            elif last_ma20 and last_close > last_ma20 * 1.1:
                result["signals"].append({
                    "type": "overbought",
                    "description": "Price is more than 10% above 20-day moving average"
                })
        
        # 3. Check for high/low volume days
        if "Volume" in hist.columns and not hist["Volume"].isna().all():
            avg_volume = hist["Volume"].mean()
            last_volume = float(hist["Volume"].iloc[-1])
            
            if last_volume > avg_volume * 2:
                result["signals"].append({
                    "type": "high_volume",
                    "description": "Volume spike may indicate exhaustion or capitulation"
                })
        
        # 4. Check for price gaps
        if "Open" in hist.columns and "Close" in hist.columns:
            for i in range(1, min(5, len(hist))):
                prev_close = float(hist["Close"].iloc[-i-1])
                curr_open = float(hist["Open"].iloc[-i])
                
                gap_pct = (curr_open / prev_close - 1) * 100
                
                if abs(gap_pct) > 1.5:  # 1.5% gap
                    gap_direction = "up" if gap_pct > 0 else "down"
                    result["signals"].append({
                        "type": f"{gap_direction}_gap",
                        "description": f"Price gap {gap_direction} of {round(abs(gap_pct), 2)}% on day -{i}",
                        "gap_pct": round(gap_pct, 2)
                    })
        
        # Summarize findings
        if result["signals"]:
            bullish_signals = sum(1 for s in result["signals"] if s["type"] in ["oversold", "high_volume"] or "down" in s["type"])
            bearish_signals = sum(1 for s in result["signals"] if s["type"] in ["overbought", "high_volume"] or "up" in s["type"])
            
            if bullish_signals > bearish_signals:
                result["summary"] = "Potential bullish exhaustion signals detected"
                result["bias"] = "bullish"
            elif bearish_signals > bullish_signals:
                result["summary"] = "Potential bearish exhaustion signals detected"
                result["bias"] = "bearish"
            else:
                result["summary"] = "Mixed exhaustion signals detected"
                result["bias"] = "neutral"
        else:
            result["summary"] = "No clear exhaustion signals detected"
            result["bias"] = "neutral"
        
        return result
    except Exception as e:
        logger.error(f"Error detecting market exhaustion for {ticker}: {str(e)}")
        result["error"] = str(e)
        return result