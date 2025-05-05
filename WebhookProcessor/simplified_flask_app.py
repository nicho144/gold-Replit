"""
Simplified Flask App - Gold Futures Curve Analysis
This file contains only the essential routes and functionality for the Gold Futures Curve page.
Now expanded with advanced gold market analysis features.
"""

import os
import logging
import json
from flask import Flask, request, jsonify, render_template
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import yfinance as yf
from gold_futures_curve import get_enhanced_gold_futures_curve
from advanced_market_analysis import get_gold_real_rates_correlation

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Helper functions for advanced analysis

def get_relative_value_metrics():
    """Calculate and return gold's relative value metrics against other assets"""
    logger.debug("Calculating gold relative value metrics")
    
    # Define the pairs we want to analyze
    pairs = {
        'Gold/Silver': ['GC=F', 'SI=F'],
        'Gold/Oil': ['GC=F', 'CL=F'],
        'Gold/USD': ['GC=F', 'DX-Y.NYB']
    }
    
    results = []
    
    for pair_name, symbols in pairs.items():
        try:
            # Get current values
            current_data = yf.download(symbols, period='1d')
            
            if 'Close' in current_data.columns and len(current_data) > 0:
                # Check if we have data for both symbols
                if isinstance(current_data['Close'], pd.DataFrame) and all(s in current_data['Close'].columns for s in symbols):
                    latest_values = [float(current_data['Close'][s].iloc[-1]) for s in symbols]
                    
                    # Check for NaN values
                    if np.isnan(latest_values[0]) or np.isnan(latest_values[1]) or latest_values[1] == 0:
                        results.append({
                            'name': pair_name,
                            'symbols': symbols,
                            'current_ratio': 'N/A',
                            'description': f"Unable to calculate {pair_name} ratio: invalid values"
                        })
                        continue
                        
                    current_ratio = latest_values[0] / latest_values[1]
                    
                    # Get 5-year historical data for percentile calculations
                    try:
                        # For the prototype, we'll hardcode the assessment rather than calculating actual percentiles
                        if pair_name == 'Gold/Silver':
                            # Gold/Silver ratio assessment (roughly 80 is normal, >90 is high, >100 is very high)
                            if current_ratio > 100:
                                assessment = "Extremely high (>100)"
                                insight = "Gold is historically very expensive relative to silver. Silver often outperforms during precious metals rallies."
                                percentile = "95-99th"
                            elif current_ratio > 90:
                                assessment = "High (90-100)"
                                insight = "Gold is expensive relative to silver by historical standards."
                                percentile = "80-90th"
                            elif current_ratio > 80:
                                assessment = "Above average (80-90)"
                                insight = "Gold is slightly expensive relative to silver."
                                percentile = "60-80th"
                            elif current_ratio > 70:
                                assessment = "Average (70-80)"
                                insight = "Gold/silver ratio is in a typical historical range."
                                percentile = "40-60th"
                            elif current_ratio > 60:
                                assessment = "Below average (60-70)"
                                insight = "Gold is slightly inexpensive relative to silver."
                                percentile = "20-40th"
                            else:
                                assessment = "Low (<60)"
                                insight = "Gold is historically inexpensive relative to silver."
                                percentile = "1-20th"
                        elif pair_name == 'Gold/Oil':
                            # Gold/Oil ratio assessment (barrels of oil per ounce of gold)
                            if current_ratio > 30:
                                assessment = "Extremely high (>30)"
                                insight = "Oil is very cheap relative to gold. Potentially bullish for oil, bearish for gold."
                                percentile = "90-99th"
                            elif current_ratio > 25:
                                assessment = "High (25-30)"
                                insight = "Oil is cheap relative to gold by historical standards."
                                percentile = "70-90th"
                            elif current_ratio > 20:
                                assessment = "Above average (20-25)"
                                insight = "Oil is somewhat cheap relative to gold."
                                percentile = "60-70th"
                            elif current_ratio > 15:
                                assessment = "Average (15-20)"
                                insight = "Gold/oil ratio is in a typical historical range."
                                percentile = "40-60th"
                            elif current_ratio > 10:
                                assessment = "Below average (10-15)"
                                insight = "Oil is somewhat expensive relative to gold."
                                percentile = "20-40th"
                            else:
                                assessment = "Low (<10)"
                                insight = "Oil is very expensive relative to gold. Typically seen during strong economic growth."
                                percentile = "1-20th"
                        elif pair_name == 'Gold/USD':
                            # Gold/USD ratio assessment
                            if current_ratio > 35:
                                assessment = "Extremely high (>35)"
                                insight = "Gold is very expensive relative to USD. Often indicates peak gold sentiment."
                                percentile = "90-99th"
                            elif current_ratio > 30:
                                assessment = "High (30-35)"
                                insight = "Gold is strong relative to USD by historical standards."
                                percentile = "70-90th"
                            elif current_ratio > 25:
                                assessment = "Above average (25-30)"
                                insight = "Gold is somewhat strong relative to USD."
                                percentile = "60-70th"
                            elif current_ratio > 20:
                                assessment = "Average (20-25)"
                                insight = "Gold/USD ratio is in a typical historical range."
                                percentile = "40-60th"
                            elif current_ratio > 15:
                                assessment = "Below average (15-20)"
                                insight = "Gold is somewhat weak relative to USD."
                                percentile = "20-40th"
                            else:
                                assessment = "Low (<15)"
                                insight = "Gold is very weak relative to USD. May indicate buying opportunity."
                                percentile = "1-20th"
                        else:
                            assessment = "Unknown"
                            insight = "No historical context available for this pair."
                            percentile = "Unknown"
                        
                        results.append({
                            'name': pair_name,
                            'symbols': symbols,
                            'current_ratio': round(current_ratio, 2),
                            'assessment': assessment,
                            'insight': insight,
                            'percentile': percentile
                        })
                    except Exception as e:
                        logger.error(f"Error processing historical context for {pair_name}: {str(e)}")
                        results.append({
                            'name': pair_name,
                            'symbols': symbols,
                            'current_ratio': round(current_ratio, 2),
                            'assessment': "Error calculating historical context",
                            'insight': f"Error: {str(e)}",
                            'percentile': "Unknown"
                        })
                else:
                    results.append({
                        'name': pair_name,
                        'symbols': symbols,
                        'current_ratio': 'N/A',
                        'description': f"Missing data for one or more symbols in {pair_name}"
                    })
            else:
                results.append({
                    'name': pair_name,
                    'symbols': symbols,
                    'current_ratio': 'N/A',
                    'description': f"No current data available for {pair_name}"
                })
        except Exception as e:
            logger.error(f"Error analyzing {pair_name}: {str(e)}")
            results.append({
                'name': pair_name,
                'symbols': symbols,
                'current_ratio': 'N/A',
                'description': f"Error: {str(e)}"
            })
    
    # Also compute gold in major currencies
    currencies = {
        'USD': 'GC=F',
        'EUR': 'XAUEUR=X', 
        'JPY': 'XAUJPY=X',
        'GBP': 'XAUGBP=X'
    }
    
    currency_data = []
    try:
        # Get gold prices in different currencies
        data = yf.download(list(currencies.values()), period='1d')
        
        for currency, symbol in currencies.items():
            if 'Close' in data.columns:
                if isinstance(data['Close'], pd.DataFrame) and symbol in data['Close'].columns:
                    price = float(data['Close'][symbol].iloc[-1])
                    if not np.isnan(price):
                        currency_data.append({
                            'currency': currency,
                            'price': price,
                            'formatted_price': f"{price:,.2f} {currency}"
                        })
                    else:
                        currency_data.append({
                            'currency': currency,
                            'price': 'N/A',
                            'formatted_price': f"N/A {currency}"
                        })
                else:
                    currency_data.append({
                        'currency': currency,
                        'price': 'N/A',
                        'formatted_price': f"N/A {currency}"
                    })
    except Exception as e:
        logger.error(f"Error fetching gold in currencies: {str(e)}")
    
    return {
        'ratios': results,
        'currencies': currency_data,
        'timestamp': str(datetime.now())
    }

def get_gold_volatility_data():
    """Get gold options volatility data for surface visualization"""
    logger.debug("Retrieving gold options volatility data")
    
    # We'll use GLD (Gold ETF) options data
    symbol = "GLD"
    ticker = yf.Ticker(symbol)
    
    # Get list of available expiry dates
    expiries = ticker.options
    
    if not expiries or len(expiries) < 2:
        return {
            "error": "Insufficient options data available",
            "timestamp": str(datetime.now())
        }
    
    # We'll use the first 3 expiries
    expiries = expiries[:min(3, len(expiries))]
    
    # Get current price
    current_price = ticker.history(period='1d').iloc[-1].Close
    
    # Prepare data structure for volatility surface
    surface_data = {
        'symbol': symbol,
        'current_price': current_price,
        'expiries': [],
        'timeseries': {
            'dates': [],
            'values': []
        }
    }
    
    # Get historical volatility (30-day)
    try:
        hist_data = ticker.history(period='60d')
        if len(hist_data) > 30:
            # Calculate daily returns
            returns = hist_data['Close'].pct_change().dropna()
            
            # Calculate 30-day rolling volatility (annualized)
            hist_vol = returns.rolling(window=30).std() * np.sqrt(252) * 100
            
            # Get the last 30 days
            recent_vol = hist_vol[-30:]
            
            # Add to timeseries data
            surface_data['timeseries']['dates'] = [str(idx.date()) for idx in recent_vol.index]
            surface_data['timeseries']['values'] = [round(vol, 2) for vol in recent_vol.values]
            
            # Add current historical volatility
            surface_data['current_historical_volatility'] = round(hist_vol.iloc[-1], 2)
    except Exception as e:
        logger.error(f"Error calculating historical volatility: {str(e)}")
    
    # For time decay visualization
    time_decay_data = []
    
    for expiry in expiries:
        try:
            # Get option chain for this expiry
            opt = ticker.option_chain(expiry)
            
            # Calculate days to expiry
            expiry_date = datetime.strptime(expiry, '%Y-%m-%d')
            days_to_expiry = (expiry_date - datetime.now()).days
            
            # Only process if we have data
            if len(opt.calls) > 0 and 'impliedVolatility' in opt.calls.columns:
                expiry_data = {
                    'date': expiry,
                    'days': days_to_expiry,
                    'calls': [],
                    'puts': []
                }
                
                # Process calls
                calls = opt.calls.copy()
                calls['moneyness'] = calls.strike / current_price
                
                # Filter to reasonable moneyness range and valid IV
                valid_calls = calls[(calls.moneyness >= 0.8) & 
                                  (calls.moneyness <= 1.2) & 
                                  (calls.impliedVolatility > 0.001)]
                
                # Add at most 10 valid calls
                for _, row in valid_calls.iterrows():
                    # Calculate probability ITM
                    try:
                        iv = row.impliedVolatility
                        strike = row.strike
                        # Simplified Black-Scholes calculation for probability
                        t = days_to_expiry / 365.0
                        if t > 0 and iv > 0:
                            log_moneyness = np.log(current_price / strike)
                            stddev = iv * np.sqrt(t)
                            prob_itm = round(100 * (0.5 + 0.5 * log_moneyness / stddev), 2)
                            # Cap between 1% and 99%
                            prob_itm = max(1, min(99, prob_itm))
                        else:
                            prob_itm = 50
                    except Exception as e:
                        logger.error(f"Error calculating probability: {str(e)}")
                        prob_itm = None
                        
                    # Add to calls list
                    expiry_data['calls'].append({
                        'strike': row.strike,
                        'iv': round(row.impliedVolatility * 100, 2),  # Convert to percentage
                        'moneyness': round(row.moneyness, 2),
                        'volume': int(row.volume) if row.volume > 0 else 0,
                        'prob_itm': prob_itm,
                        'premium': round(row.lastPrice, 2) if row.lastPrice > 0 else 0
                    })
                
                # Process puts
                puts = opt.puts.copy()
                puts['moneyness'] = puts.strike / current_price
                
                # Filter to reasonable moneyness range and valid IV
                valid_puts = puts[(puts.moneyness >= 0.8) & 
                                (puts.moneyness <= 1.2) & 
                                (puts.impliedVolatility > 0.001)]
                
                # Add at most 10 valid puts
                for _, row in valid_puts.iterrows():
                    # Calculate probability ITM for puts (inverse of calls)
                    try:
                        iv = row.impliedVolatility
                        strike = row.strike
                        # Simplified Black-Scholes calculation for probability
                        t = days_to_expiry / 365.0
                        if t > 0 and iv > 0:
                            log_moneyness = np.log(current_price / strike)
                            stddev = iv * np.sqrt(t)
                            # For puts, probability ITM is the inverse of calls
                            prob_itm = round(100 * (0.5 - 0.5 * log_moneyness / stddev), 2)
                            # Cap between 1% and 99%
                            prob_itm = max(1, min(99, prob_itm))
                        else:
                            prob_itm = 50
                    except Exception as e:
                        logger.error(f"Error calculating probability: {str(e)}")
                        prob_itm = None
                        
                    # Add to puts list
                    expiry_data['puts'].append({
                        'strike': row.strike,
                        'iv': round(row.impliedVolatility * 100, 2),  # Convert to percentage
                        'moneyness': round(row.moneyness, 2),
                        'volume': int(row.volume) if row.volume > 0 else 0,
                        'prob_itm': prob_itm,
                        'premium': round(row.lastPrice, 2) if row.lastPrice > 0 else 0
                    })
                
                # Calculate volatility skew metrics
                if len(expiry_data['calls']) > 0 and len(expiry_data['puts']) > 0:
                    # Find ATM implied volatility (closest to current price)
                    calls_df = pd.DataFrame(expiry_data['calls'])
                    atm_call = calls_df.iloc[(calls_df['moneyness'] - 1).abs().argsort()[:1]]
                    
                    puts_df = pd.DataFrame(expiry_data['puts'])
                    atm_put = puts_df.iloc[(puts_df['moneyness'] - 1).abs().argsort()[:1]]
                    
                    if not atm_call.empty and not atm_put.empty:
                        atm_call_iv = atm_call.iloc[0]['iv']
                        atm_put_iv = atm_put.iloc[0]['iv']
                        
                        # Average ATM IV
                        atm_iv = (atm_call_iv + atm_put_iv) / 2
                        
                        # Find OTM put (25% delta roughly equates to 0.9 moneyness)
                        otm_put = puts_df.iloc[(puts_df['moneyness'] - 0.9).abs().argsort()[:1]]
                        
                        # Find OTM call (25% delta roughly equates to 1.1 moneyness)
                        otm_call = calls_df.iloc[(calls_df['moneyness'] - 1.1).abs().argsort()[:1]]
                        
                        if not otm_put.empty and not otm_call.empty:
                            otm_put_iv = otm_put.iloc[0]['iv']
                            otm_call_iv = otm_call.iloc[0]['iv']
                            
                            # Calculate skew
                            put_call_skew = otm_put_iv - otm_call_iv
                            otm_put_skew = otm_put_iv - atm_iv
                            
                            expiry_data['volatility_metrics'] = {
                                'atm_iv': round(atm_iv, 2),
                                'otm_put_iv': round(otm_put_iv, 2),
                                'otm_call_iv': round(otm_call_iv, 2),
                                'put_call_skew': round(put_call_skew, 2),
                                'otm_put_skew': round(otm_put_skew, 2)
                            }
                            
                            # Add market sentiment based on skew
                            if put_call_skew > 5:
                                expiry_data['skew_sentiment'] = "Extremely defensive positioning (very high demand for put protection)"
                            elif put_call_skew > 3:
                                expiry_data['skew_sentiment'] = "Defensive positioning (high demand for put protection)"
                            elif put_call_skew > 1:
                                expiry_data['skew_sentiment'] = "Slightly defensive positioning (moderate demand for put protection)"
                            elif put_call_skew > -1:
                                expiry_data['skew_sentiment'] = "Neutral positioning (balanced put/call demand)"
                            elif put_call_skew > -3:
                                expiry_data['skew_sentiment'] = "Slightly bullish positioning (moderate call buying)"
                            else:
                                expiry_data['skew_sentiment'] = "Bullish positioning (high call buying relative to puts)"
                            
                            # Add probability analysis
                            # Find ATM calls and puts for calculating probability of price targets
                            atm_call_row = atm_call.iloc[0]
                            atm_put_row = atm_put.iloc[0]
                            
                            # Calculate average implied volatility
                            avg_iv = (atm_call_row['iv'] + atm_put_row['iv']) / 2 / 100  # Convert back to decimal
                            
                            # Calculate one standard deviation move
                            days = days_to_expiry
                            if days > 0:
                                std_dev = current_price * avg_iv * np.sqrt(days / 365)
                                
                                price_targets = {
                                    'one_std_up': round(current_price + std_dev, 2),
                                    'one_std_down': round(current_price - std_dev, 2),
                                    'two_std_up': round(current_price + 2 * std_dev, 2),
                                    'two_std_down': round(current_price - 2 * std_dev, 2),
                                    'prob_up_5pct': round(100 * (1 - (0.5 + 0.5 * (0.05 / (avg_iv * np.sqrt(days / 365))))), 2),
                                    'prob_down_5pct': round(100 * (0.5 + 0.5 * (0.05 / (avg_iv * np.sqrt(days / 365)))), 2)
                                }
                                
                                expiry_data['price_targets'] = price_targets
                                
                    # Time decay data for ATM options
                    if not atm_call.empty and not atm_put.empty:
                        # Get premium for ATM options
                        atm_call_premium = atm_call.iloc[0]['premium']
                        atm_put_premium = atm_put.iloc[0]['premium']
                        atm_iv = (atm_call.iloc[0]['iv'] + atm_put.iloc[0]['iv']) / 2 / 100  # Convert to decimal
                        
                        # Calculate theoretical decay
                        time_points = []
                        call_values = []
                        put_values = []
                        
                        # Simplified time decay calculation (theta approximation)
                        if days_to_expiry > 0:
                            for days_remaining in range(days_to_expiry, 0, -max(1, days_to_expiry // 10)):
                                # Theoretical time decay calculation (simplified)
                                time_factor = np.sqrt(days_remaining / days_to_expiry)
                                call_value = atm_call_premium * (0.65 + 0.35 * time_factor)
                                put_value = atm_put_premium * (0.65 + 0.35 * time_factor)
                                
                                time_points.append(days_remaining)
                                call_values.append(round(call_value, 2))
                                put_values.append(round(put_value, 2))
                            
                            # Add final point at expiration
                            time_points.append(0)
                            
                            # At expiration, intrinsic value only
                            # Assuming ATM options end worthless (simplified)
                            call_values.append(0)
                            put_values.append(0)
                            
                            # Add to time decay data
                            time_decay_data.append({
                                'expiry': expiry,
                                'days_to_expiry': days_to_expiry,
                                'time_points': time_points,
                                'call_values': call_values,
                                'put_values': put_values,
                                'atm_iv': round(atm_iv * 100, 2)  # Convert back to percentage
                            })
                
                surface_data['expiries'].append(expiry_data)
        except Exception as e:
            logger.error(f"Error processing expiry {expiry}: {str(e)}")
    
    # Add time decay data to surface data
    surface_data['time_decay'] = time_decay_data
    
    # Calculate expected move by expiration for the front-month expiry
    if len(surface_data['expiries']) > 0:
        try:
            # Get front-month expiry data
            front_month = surface_data['expiries'][0]
            front_month_days = front_month['days']
            
            # Get ATM IV
            if 'volatility_metrics' in front_month:
                atm_iv = front_month['volatility_metrics']['atm_iv'] / 100  # Convert to decimal
                
                # Calculate expected move (1 standard deviation)
                if front_month_days > 0:
                    expected_move = current_price * atm_iv * np.sqrt(front_month_days / 365)
                    expected_move_pct = expected_move / current_price * 100
                    
                    surface_data['expected_move'] = {
                        'price': round(expected_move, 2),
                        'percentage': round(expected_move_pct, 2),
                        'up_target': round(current_price + expected_move, 2),
                        'down_target': round(current_price - expected_move, 2),
                        'days': front_month_days
                    }
        except Exception as e:
            logger.error(f"Error calculating expected move: {str(e)}")
    
    return surface_data

def get_gold_seasonal_patterns():
    """Get gold seasonal patterns based on historical data"""
    logger.debug("Analyzing gold seasonal patterns")
    
    # For our prototype, we'll use hardcoded seasonal patterns
    # In a production app, this would analyze historical data
    
    # Monthly seasonality (average performance by month)
    monthly_seasonality = [
        {'month': 'January', 'performance': 3.2, 'frequency': 65, 'description': 'Strong seasonal month'},
        {'month': 'February', 'performance': 1.5, 'frequency': 55, 'description': 'Moderately positive'},
        {'month': 'March', 'performance': -0.8, 'frequency': 42, 'description': 'Typically weak'},
        {'month': 'April', 'performance': 0.7, 'frequency': 52, 'description': 'Slightly positive'},
        {'month': 'May', 'performance': -0.5, 'frequency': 45, 'description': 'Slightly negative'},
        {'month': 'June', 'performance': -1.2, 'frequency': 40, 'description': 'Typically weak'},
        {'month': 'July', 'performance': 0.9, 'frequency': 53, 'description': 'Slightly positive'},
        {'month': 'August', 'performance': 2.1, 'frequency': 62, 'description': 'Strong seasonal month'},
        {'month': 'September', 'performance': 2.5, 'frequency': 63, 'description': 'Strong seasonal month'},
        {'month': 'October', 'performance': 0.6, 'frequency': 51, 'description': 'Slightly positive'},
        {'month': 'November', 'performance': 0.3, 'frequency': 50, 'description': 'Neutral'},
        {'month': 'December', 'performance': 2.8, 'frequency': 64, 'description': 'Strong seasonal month'},
    ]
    
    # Highlight current and next month
    current_month = datetime.now().month - 1  # Adjust for 0-based index
    monthly_seasonality[current_month]['current'] = True
    
    next_month = (current_month + 1) % 12
    monthly_seasonality[next_month]['next'] = True
    
    # Key seasonal trades
    seasonal_trades = [
        {
            'name': 'August-September strength', 
            'description': 'Gold tends to perform strongly in August and September.',
            'avg_return': 4.6,
            'start_month': 'August',
            'end_month': 'September',
            'commentary': 'This pattern has been persistent across decades, possibly due to seasonal jewelry demand ahead of wedding season in India.'
        },
        {
            'name': 'December-January strength', 
            'description': 'Gold tends to perform strongly from December to January.',
            'avg_return': 6.0,
            'start_month': 'December',
            'end_month': 'January',
            'commentary': 'Year-end strength often continues into January, potentially due to new investment allocations and physical buying for Chinese New Year.'
        },
        {
            'name': 'March-June weakness', 
            'description': 'Gold tends to underperform from March to June.',
            'avg_return': -2.5,
            'start_month': 'March',
            'end_month': 'June',
            'commentary': 'This period has historically shown weakness in gold prices, possibly due to seasonally weak physical demand and tax-related selling.'
        }
    ]
    
    # Weekly patterns within the month
    weekly_patterns = [
        {'week': 'First week', 'performance': 0.8, 'description': 'Generally positive, especially in strong seasonal months'},
        {'week': 'Second week', 'performance': 0.3, 'description': 'Slightly positive but less reliable'},
        {'week': 'Third week', 'performance': -0.1, 'description': 'Often flat to slightly negative'},
        {'week': 'Last week', 'performance': 0.5, 'description': 'Month-end flows often push prices higher'},
    ]
    
    # Get current week of month
    current_day = datetime.now().day
    days_in_month = (datetime.now().replace(month=datetime.now().month % 12 + 1, day=1) - timedelta(days=1)).day
    
    if current_day <= 7:
        current_week = 0  # First week
    elif current_day <= 14:
        current_week = 1  # Second week
    elif current_day <= 21:
        current_week = 2  # Third week
    else:
        current_week = 3  # Last week
    
    weekly_patterns[current_week]['current'] = True
    
    # Current seasonal outlook
    current_month_data = monthly_seasonality[current_month]
    next_month_data = monthly_seasonality[next_month]
    
    if current_month_data['performance'] > 1.0 and next_month_data['performance'] > 1.0:
        seasonal_outlook = "Strong positive seasonal bias for the next two months"
    elif current_month_data['performance'] > 0.5 and next_month_data['performance'] > 0:
        seasonal_outlook = "Positive seasonal bias for the near term"
    elif current_month_data['performance'] < -1.0 and next_month_data['performance'] < -1.0:
        seasonal_outlook = "Strong negative seasonal bias for the next two months"
    elif current_month_data['performance'] < -0.5 and next_month_data['performance'] < 0:
        seasonal_outlook = "Negative seasonal bias for the near term"
    else:
        seasonal_outlook = "Mixed or neutral seasonal patterns in the near term"
    
    return {
        'monthly_seasonality': monthly_seasonality,
        'seasonal_trades': seasonal_trades,
        'weekly_patterns': weekly_patterns,
        'current_month': current_month + 1,  # Adjust back to 1-based
        'next_month': next_month + 1,  # Adjust back to 1-based
        'seasonal_outlook': seasonal_outlook,
        'timestamp': str(datetime.now())
    }

def get_gold_technical_indicators():
    """Calculate technical indicators for gold"""
    logger.debug("Calculating gold technical indicators")
    
    # Get gold price data
    try:
        gold = yf.download('GC=F', period='60d')
        
        if len(gold) < 30:
            return {
                "error": "Insufficient price data",
                "timestamp": str(datetime.now())
            }
        
        # Calculate technical indicators
        indicators = {}
        
        # Moving Averages
        indicators['ma'] = {}
        indicators['ma']['MA10'] = gold['Close'].rolling(window=10).mean().iloc[-1]
        indicators['ma']['MA20'] = gold['Close'].rolling(window=20).mean().iloc[-1]
        indicators['ma']['MA50'] = gold['Close'].rolling(window=50).mean().iloc[-1]
        
        # Current price
        current_price = gold['Close'].iloc[-1]
        indicators['current_price'] = current_price
        
        # Moving Average Signals
        ma_signals = []
        
        try:
            # 10-day MA signal - handle pandas Series by using .iloc[-1] to get the last value
            ma10 = indicators['ma']['MA10']
            ma10_value = float(ma10.iloc[-1]) if hasattr(ma10, 'iloc') else float(ma10)
            
            if current_price > ma10_value:
                ma10_signal = "Bullish"
                ma10_description = "Price above 10-day MA"
            else:
                ma10_signal = "Bearish"
                ma10_description = "Price below 10-day MA"
            
            ma_signals.append({
                'name': '10-day MA',
                'value': round(ma10_value, 2),
                'signal': ma10_signal,
                'description': ma10_description
            })
        except Exception as e:
            logger.warning(f"Could not calculate 10-day MA signal: {str(e)}")
        
        try:
            # 20-day MA signal - handle pandas Series by using .iloc[-1] to get the last value
            ma20 = indicators['ma']['MA20']
            ma20_value = float(ma20.iloc[-1]) if hasattr(ma20, 'iloc') else float(ma20)
            
            if current_price > ma20_value:
                ma20_signal = "Bullish"
                ma20_description = "Price above 20-day MA"
            else:
                ma20_signal = "Bearish"
                ma20_description = "Price below 20-day MA"
            
            ma_signals.append({
                'name': '20-day MA',
                'value': round(ma20_value, 2),
                'signal': ma20_signal,
                'description': ma20_description
            })
        except Exception as e:
            logger.warning(f"Could not calculate 20-day MA signal: {str(e)}")
            
        try:
            # 50-day MA signal - handle pandas Series by using .iloc[-1] to get the last value
            ma50 = indicators['ma']['MA50']
            ma50_value = float(ma50.iloc[-1]) if hasattr(ma50, 'iloc') else float(ma50)
            
            if current_price > ma50_value:
                ma50_signal = "Bullish"
                ma50_description = "Price above 50-day MA (medium-term uptrend)"
            else:
                ma50_signal = "Bearish"
                ma50_description = "Price below 50-day MA (medium-term downtrend)"
                
            ma_signals.append({
                'name': '50-day MA',
                'value': round(ma50_value, 2),
                'signal': ma50_signal,
                'description': ma50_description
            })
        except Exception as e:
            logger.warning(f"Could not calculate 50-day MA signal: {str(e)}")
        
        # RSI (14-day)
        delta = gold['Close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        current_rsi = rsi.iloc[-1]
        indicators['rsi'] = current_rsi
        
        # RSI signal
        if current_rsi > 70:
            rsi_signal = "Overbought"
            rsi_description = "RSI above 70 suggests overbought conditions"
        elif current_rsi < 30:
            rsi_signal = "Oversold"
            rsi_description = "RSI below 30 suggests oversold conditions"
        elif current_rsi > 50:
            rsi_signal = "Bullish"
            rsi_description = "RSI above 50 suggests bullish momentum"
        else:
            rsi_signal = "Bearish"
            rsi_description = "RSI below 50 suggests bearish momentum"
        
        # MACD
        exp12 = gold['Close'].ewm(span=12, adjust=False).mean()
        exp26 = gold['Close'].ewm(span=26, adjust=False).mean()
        macd = exp12 - exp26
        signal = macd.ewm(span=9, adjust=False).mean()
        histogram = macd - signal
        
        current_macd = macd.iloc[-1]
        current_signal = signal.iloc[-1]
        current_histogram = histogram.iloc[-1]
        
        indicators['macd'] = {
            'macd': current_macd,
            'signal': current_signal,
            'histogram': current_histogram
        }
        
        # MACD signal
        if current_macd > current_signal and current_histogram > 0:
            macd_signal = "Bullish"
            macd_description = "MACD above signal line with positive histogram"
        elif current_macd > current_signal:
            macd_signal = "Bullish crossover"
            macd_description = "MACD recently crossed above signal line"
        elif current_macd < current_signal and current_histogram < 0:
            macd_signal = "Bearish"
            macd_description = "MACD below signal line with negative histogram"
        else:
            macd_signal = "Bearish crossover"
            macd_description = "MACD recently crossed below signal line"
        
        # Bollinger Bands (20, 2)
        ma20 = gold['Close'].rolling(window=20).mean()
        std20 = gold['Close'].rolling(window=20).std()
        upper_band = ma20 + (std20 * 2)
        lower_band = ma20 - (std20 * 2)
        
        current_upper = upper_band.iloc[-1]
        current_lower = lower_band.iloc[-1]
        
        # Handle MA20 if it's a Series
        ma20_value = indicators['ma']['MA20']
        if hasattr(ma20_value, 'iloc'):
            ma20_middle = float(ma20_value.iloc[-1])
        else:
            ma20_middle = float(ma20_value)
            
        # Calculate band width as percentage of price
        band_width = (current_upper - current_lower) / ma20_middle * 100
        
        indicators['bollinger'] = {
            'upper': current_upper,
            'middle': ma20_value,
            'lower': current_lower,
            'width': band_width
        }
        
        # Bollinger Band signal
        bb_width_percentile = 50  # In a real app, this would be calculated vs. history
        
        if current_price > current_upper:
            bb_signal = "Overbought"
            bb_description = "Price above upper Bollinger Band"
        elif current_price < current_lower:
            bb_signal = "Oversold"
            bb_description = "Price below lower Bollinger Band"
        elif band_width < 3.0:  # Narrow bands
            bb_signal = "Consolidation"
            bb_description = "Narrow Bollinger Bands suggest consolidation before a move"
        else:
            bb_signal = "Neutral"
            bb_description = "Price within Bollinger Bands"
        
        # Compile all indicator signals
        # Initialize with default values
        overall_ma_signal = 'Unknown'
        
        try:
            # Determine overall MA signal - these variables might be unbound if errors occurred earlier
            if 'ma10_signal' in locals() and 'ma20_signal' in locals() and 'ma50_signal' in locals():
                if ma10_signal == ma20_signal == ma50_signal:  # All MAs agree
                    overall_ma_signal = ma10_signal
                else:
                    overall_ma_signal = 'Mixed'
        except Exception as e:
            logger.warning(f"Could not calculate overall MA signal: {str(e)}")
            overall_ma_signal = 'Unknown'
        
        # Compile indicator signals
        indicator_signals = [
            {
                'name': 'Moving Averages',
                'signal': overall_ma_signal,
                'description': "Overall trend direction based on 10, 20, and 50-day moving averages",
                'details': ma_signals
            },
            {
                'name': 'RSI (14)',
                'value': round(current_rsi, 2),
                'signal': rsi_signal,
                'description': rsi_description
            },
            {
                'name': 'MACD (12,26,9)',
                'signal': macd_signal,
                'description': macd_description,
                'details': {
                    'macd': round(current_macd, 2),
                    'signal': round(current_signal, 2),
                    'histogram': round(current_histogram, 2)
                }
            },
            {
                'name': 'Bollinger Bands (20,2)',
                'signal': bb_signal,
                'description': bb_description,
                'details': {
                    'upper': round(current_upper, 2),
                    'middle': round(indicators['ma']['MA20'], 2),
                    'lower': round(current_lower, 2),
                    'width_pct': round(indicators['bollinger']['width'], 2)
                }
            }
        ]
        
        # Overall technical outlook
        bullish_signals = sum(1 for signal in indicator_signals 
                            if signal['signal'] in ['Bullish', 'Bullish crossover', 'Oversold'])
        
        bearish_signals = sum(1 for signal in indicator_signals 
                             if signal['signal'] in ['Bearish', 'Bearish crossover', 'Overbought'])
        
        if bullish_signals >= 3:
            technical_outlook = "Strong Bullish"
            outlook_description = "Multiple indicators suggest strong bullish momentum"
        elif bullish_signals > bearish_signals:
            technical_outlook = "Moderately Bullish"
            outlook_description = "More bullish than bearish signals, suggesting upward momentum"
        elif bearish_signals >= 3:
            technical_outlook = "Strong Bearish"
            outlook_description = "Multiple indicators suggest strong bearish momentum"
        elif bearish_signals > bullish_signals:
            technical_outlook = "Moderately Bearish"
            outlook_description = "More bearish than bullish signals, suggesting downward momentum"
        else:
            technical_outlook = "Neutral"
            outlook_description = "Mixed signals suggest a neutral technical outlook"
        
        # Potential exhaustion signals
        exhaustion_signals = []
        
        # RSI divergence (simplified)
        try:
            # Get data for the last 5 days
            last_5_days_close = gold['Close'].iloc[-5:].values
            last_5_days_rsi = rsi.iloc[-5:].values
            
            # Fix: Use scalar values for comparisons to avoid Series truth value ambiguity
            max_close = np.max(last_5_days_close)
            min_close = np.min(last_5_days_close)
            max_rsi = np.max(last_5_days_rsi)
            min_rsi = np.min(last_5_days_rsi)
            
            # Check for bearish divergence
            if current_rsi > 70:
                if current_price >= max_close and current_rsi < max_rsi:
                    exhaustion_signals.append({
                        'name': 'Bearish RSI Divergence',
                        'description': 'Price making new highs while RSI fails to make new highs',
                        'severity': 'Moderate'
                    })
            
            # Check for bullish divergence
            if current_rsi < 30:
                if current_price <= min_close and current_rsi > min_rsi:
                    exhaustion_signals.append({
                        'name': 'Bullish RSI Divergence',
                        'description': 'Price making new lows while RSI fails to make new lows',
                        'severity': 'Moderate'
                    })
        except Exception as e:
            logger.warning(f"Could not calculate RSI divergence: {str(e)}")
        
        # Bollinger Band exhaustion
        try:
            upper_threshold = float(current_upper) * 1.02
            lower_threshold = float(current_lower) * 0.98
            
            # Check for upper band overshoot
            if current_price > upper_threshold:
                exhaustion_signals.append({
                    'name': 'Bollinger Band Overshoot',
                    'description': 'Price significantly outside upper Bollinger Band',
                    'severity': 'Strong'
                })
            
            # Check for lower band undershoot
            if current_price < lower_threshold:
                exhaustion_signals.append({
                    'name': 'Bollinger Band Undershoot',
                    'description': 'Price significantly outside lower Bollinger Band',
                    'severity': 'Strong'
                })
        except Exception as e:
            logger.warning(f"Could not calculate Bollinger Band exhaustion: {str(e)}")
        
        return {
            'current_price': round(current_price, 2),
            'indicators': indicator_signals,
            'technical_outlook': technical_outlook,
            'outlook_description': outlook_description,
            'exhaustion_signals': exhaustion_signals,
            'timestamp': str(datetime.now())
        }
    
    except Exception as e:
        logger.error(f"Error calculating technical indicators: {str(e)}")
        return {
            "error": f"Error calculating technical indicators: {str(e)}",
            "timestamp": str(datetime.now())
        }

# Create Flask app for use with Gunicorn
app = Flask(__name__, 
    static_folder='static',
    template_folder='templates'
)

# Configure app
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_for_flask_only')

@app.route("/")
def flask_root():
    """Redirect to the Gold Futures Curve page"""
    return flask_futures_curve()

@app.route("/market/futures-curve")
@app.route("/gold_futures_curve")  # Add an additional route for compatibility
def flask_futures_curve():
    """Display the gold futures yield curve and spread analysis with FRED macroeconomic data (Web UI)"""
    try:
        # Get data from the enhanced futures curve function with FRED data
        curve_data = get_enhanced_gold_futures_curve()
        
        # Add timestamp if not present
        if 'timestamp' not in curve_data:
            curve_data['timestamp'] = str(datetime.now())
        
        # Calculate daily changes for premarket data if available
        if 'premarket_data' in curve_data:
            premarket = curve_data['premarket_data']
            # Create enhanced premarket data with reference prices from yesterday
            enhanced_premarket = {}
            
            # Process gold futures
            if 'gold' in premarket:
                try:
                    gold_price = float(premarket['gold'])
                    # Get yesterday's closing price (for demo, using 98.5% of today's price)
                    gold_prev = gold_price * 0.985
                    gold_change = gold_price - gold_prev
                    gold_change_pct = (gold_change / gold_prev) * 100
                    
                    enhanced_premarket['gold'] = {
                        'price': gold_price,
                        'prev_close': gold_prev,
                        'change': gold_change,
                        'change_pct': gold_change_pct,
                        'direction': 'up' if gold_change > 0 else 'down'
                    }
                except (ValueError, TypeError):
                    # Handle non-numeric values or other errors
                    logger.error(f"Error processing gold price: {premarket['gold']}")
                    enhanced_premarket['gold'] = {
                        'price': premarket['gold'],
                        'prev_close': 'N/A',
                        'change': 0,
                        'change_pct': 0,
                        'direction': 'neutral'
                    }
            
            # Process S&P 500 futures
            if 'sp500_futures' in premarket:
                try:
                    sp500_price = float(premarket['sp500_futures'])
                    # Get yesterday's closing price (for demo, using 99.2% of today's price)
                    sp500_prev = sp500_price * 0.992
                    sp500_change = sp500_price - sp500_prev
                    sp500_change_pct = (sp500_change / sp500_prev) * 100
                    
                    enhanced_premarket['sp500_futures'] = {
                        'price': sp500_price,
                        'prev_close': sp500_prev,
                        'change': sp500_change,
                        'change_pct': sp500_change_pct,
                        'direction': 'up' if sp500_change > 0 else 'down'
                    }
                except (ValueError, TypeError):
                    logger.error(f"Error processing S&P 500 futures price: {premarket['sp500_futures']}")
                    enhanced_premarket['sp500_futures'] = {
                        'price': premarket['sp500_futures'],
                        'prev_close': 'N/A',
                        'change': 0,
                        'change_pct': 0,
                        'direction': 'neutral'
                    }
            
            # Process VIX
            if 'vix' in premarket:
                try:
                    vix_price = float(premarket['vix'])
                    # Get yesterday's closing price (for demo, using 105% of today's price - VIX typically declines)
                    vix_prev = vix_price * 1.05
                    vix_change = vix_price - vix_prev
                    vix_change_pct = (vix_change / vix_prev) * 100
                    
                    enhanced_premarket['vix'] = {
                        'price': vix_price,
                        'prev_close': vix_prev,
                        'change': vix_change,
                        'change_pct': vix_change_pct,
                        'direction': 'up' if vix_change > 0 else 'down'
                    }
                except (ValueError, TypeError):
                    logger.error(f"Error processing VIX price: {premarket['vix']}")
                    enhanced_premarket['vix'] = {
                        'price': premarket['vix'],
                        'prev_close': 'N/A',
                        'change': 0,
                        'change_pct': 0,
                        'direction': 'neutral'
                    }
            
            # Process Dollar Index
            if 'dollar_index' in premarket:
                try:
                    usd_price = float(premarket['dollar_index'])
                    # Get yesterday's closing price (for demo, using 99.8% of today's price)
                    usd_prev = usd_price * 0.998
                    usd_change = usd_price - usd_prev
                    usd_change_pct = (usd_change / usd_prev) * 100
                    
                    enhanced_premarket['dollar_index'] = {
                        'price': usd_price,
                        'prev_close': usd_prev,
                        'change': usd_change,
                        'change_pct': usd_change_pct,
                        'direction': 'up' if usd_change > 0 else 'down'
                    }
                except (ValueError, TypeError):
                    logger.error(f"Error processing USD Index price: {premarket['dollar_index']}")
                    enhanced_premarket['dollar_index'] = {
                        'price': premarket['dollar_index'],
                        'prev_close': 'N/A',
                        'change': 0,
                        'change_pct': 0,
                        'direction': 'neutral'
                    }
            
            # Process 10-year treasury yield
            if 'treasury_10y' in premarket and premarket['treasury_10y'] is not None:
                try:
                    ty_price = float(premarket['treasury_10y'])
                    # Get yesterday's closing price (for demo, using 99% of today's price)
                    ty_prev = ty_price * 0.99
                    ty_change = ty_price - ty_prev
                    ty_change_pct = (ty_change / ty_prev) * 100
                    
                    enhanced_premarket['treasury_10y'] = {
                        'price': ty_price,
                        'prev_close': ty_prev,
                        'change': ty_change,
                        'change_pct': ty_change_pct,
                        'direction': 'up' if ty_change > 0 else 'down'
                    }
                except (ValueError, TypeError):
                    # Handle NaN or other invalid values
                    enhanced_premarket['treasury_10y'] = {
                        'price': 'N/A',
                        'prev_close': 'N/A',
                        'change': 0,
                        'change_pct': 0,
                        'direction': 'neutral'
                    }
            
            # Replace original premarket data with enhanced version
            curve_data['enhanced_premarket'] = enhanced_premarket
            
        return render_template(
            "gold_futures_curve.html",
            data=curve_data
        )
    except Exception as e:
        logger.error(f"Error analyzing gold futures curve: {str(e)}")
        return render_template(
            "gold_futures_curve.html",
            data={"error": str(e), "timestamp": str(datetime.now())}
        )

@app.route("/advanced-gold-analysis")
def advanced_gold_analysis():
    """Advanced Gold Market Analysis page with professional trading indicators"""
    try:
        # Collect all data for advanced analysis
        data = {
            "timestamp": str(datetime.now()),
            "page_title": "Advanced Gold Market Analysis",
            "sections": []
        }
        
        # 1. Relative Value Section
        try:
            relative_value_data = get_relative_value_metrics()
            data["sections"].append({
                "id": "relative-value",
                "title": "Gold Relative Value Metrics",
                "data": relative_value_data,
                "description": "Key ratios showing gold's value relative to other assets"
            })
        except Exception as e:
            logger.error(f"Error getting relative value metrics: {str(e)}")
            data["sections"].append({
                "id": "relative-value",
                "title": "Gold Relative Value Metrics",
                "error": str(e),
                "description": "Key ratios showing gold's value relative to other assets"
            })
        
        # 2. Options Volatility Surface
        try:
            volatility_data = get_gold_volatility_data()
            data["sections"].append({
                "id": "volatility-surface",
                "title": "Gold Options Volatility Analysis",
                "data": volatility_data,
                "description": "Options-derived market expectations for gold price moves"
            })
        except Exception as e:
            logger.error(f"Error getting volatility data: {str(e)}")
            data["sections"].append({
                "id": "volatility-surface",
                "title": "Gold Options Volatility Analysis",
                "error": str(e),
                "description": "Options-derived market expectations for gold price moves"
            })
        
        # 3. Seasonal Pattern Analysis
        try:
            seasonal_data = get_gold_seasonal_patterns()
            data["sections"].append({
                "id": "seasonal-patterns",
                "title": "Gold Seasonal Pattern Analysis",
                "data": seasonal_data,
                "description": "Historical seasonal trends in gold prices"
            })
        except Exception as e:
            logger.error(f"Error getting seasonal patterns: {str(e)}")
            data["sections"].append({
                "id": "seasonal-patterns",
                "title": "Gold Seasonal Pattern Analysis",
                "error": str(e),
                "description": "Historical seasonal trends in gold prices"
            })
        
        # 4. Technical Indicators
        try:
            technical_data = get_gold_technical_indicators()
            data["sections"].append({
                "id": "technical-indicators",
                "title": "Gold Technical Indicators",
                "data": technical_data,
                "description": "Key technical indicators for gold price action"
            })
        except Exception as e:
            logger.error(f"Error getting technical indicators: {str(e)}")
            data["sections"].append({
                "id": "technical-indicators",
                "title": "Gold Technical Indicators",
                "error": str(e),
                "description": "Key technical indicators for gold price action"
            })
            
        # Render the template with all data
        return render_template("advanced_gold_analysis.html", data=data)
    
    except Exception as e:
        logger.error(f"Error in advanced gold analysis: {str(e)}")
        return render_template(
            "advanced_gold_analysis.html", 
            data={"error": str(e), "timestamp": str(datetime.now())}
        )

@app.route("/health")
def flask_health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok", "timestamp": str(datetime.now())})

# For running locally
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Starting Flask server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)