import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import json

def get_option_chain_data(symbol, expiry_index=None):
    """Get option chain data for a given symbol and expiry"""
    print(f"Getting option data for {symbol}...")
    ticker = yf.Ticker(symbol)
    
    # Get list of available expiry dates
    expiries = ticker.options
    print(f"Available expiry dates: {len(expiries)}")
    
    # If no specific expiry_index provided, use the nearest expiry
    if expiry_index is None:
        expiry_index = 0
    
    if not expiries:
        print("No options data available")
        return None
        
    expiry = expiries[expiry_index]
    print(f"Using expiry date: {expiry}")
    
    # Get option chain for this expiry
    try:
        opt = ticker.option_chain(expiry)
        print(f"Retrieved {len(opt.calls)} calls and {len(opt.puts)} puts")
        
        # Basic data quality check
        if 'impliedVolatility' not in opt.calls.columns:
            print("WARNING: No implied volatility data available")
        else:
            calls_with_iv = opt.calls[opt.calls.impliedVolatility > 0.001].shape[0]
            puts_with_iv = opt.puts[opt.puts.impliedVolatility > 0.001].shape[0]
            print(f"Calls with valid IV: {calls_with_iv}/{len(opt.calls)}")
            print(f"Puts with valid IV: {puts_with_iv}/{len(opt.puts)}")
            
        # Check volume data
        calls_with_volume = opt.calls[opt.calls.volume > 0].shape[0]
        puts_with_volume = opt.puts[opt.puts.volume > 0].shape[0]
        print(f"Calls with volume: {calls_with_volume}/{len(opt.calls)}")
        print(f"Puts with volume: {puts_with_volume}/{len(opt.puts)}")
            
        return {
            'symbol': symbol,
            'expiry': expiry,
            'calls': opt.calls,
            'puts': opt.puts
        }
    except Exception as e:
        print(f"Error retrieving option chain: {str(e)}")
        return None

def extract_volatility_skew(option_data):
    """Extract volatility skew from option data"""
    if option_data is None:
        return None
        
    calls = option_data['calls']
    puts = option_data['puts']
    
    # Get ATM strike (closest to current price)
    ticker = yf.Ticker(option_data['symbol'])
    current_price = ticker.history(period='1d').iloc[-1].Close
    print(f"Current price: {current_price}")
    
    # Find closest strike to current price
    calls['strike_diff'] = abs(calls.strike - current_price)
    atm_call_idx = calls.strike_diff.idxmin()
    atm_strike = calls.loc[atm_call_idx].strike
    print(f"ATM strike: {atm_strike}")
    
    # Extract volatility skew
    if 'impliedVolatility' in calls.columns:
        # Get the put and call implied volatilities at various distances from ATM
        skew_data = {
            'symbol': option_data['symbol'],
            'expiry': option_data['expiry'],
            'current_price': current_price,
            'atm_strike': atm_strike,
            'skew': []
        }
        
        # Calculate moneyness levels
        moneyness_levels = np.arange(0.8, 1.21, 0.05)
        
        for moneyness in moneyness_levels:
            target_strike = current_price * moneyness
            
            # Find closest strikes
            calls['strike_diff'] = abs(calls.strike - target_strike)
            puts['strike_diff'] = abs(puts.strike - target_strike) 
            
            closest_call_idx = calls.strike_diff.idxmin()
            closest_put_idx = puts.strike_diff.idxmin()
            
            call_strike = calls.loc[closest_call_idx].strike
            put_strike = puts.loc[closest_put_idx].strike
            
            call_iv = calls.loc[closest_call_idx].impliedVolatility
            put_iv = puts.loc[closest_put_idx].impliedVolatility
            
            # Only include if IV is valid
            if call_iv > 0.001 and put_iv > 0.001:
                skew_data['skew'].append({
                    'moneyness': moneyness,
                    'target_strike': target_strike,
                    'call_strike': call_strike,
                    'put_strike': put_strike,
                    'call_iv': call_iv,
                    'put_iv': put_iv,
                    'call_volume': int(calls.loc[closest_call_idx].volume) if calls.loc[closest_call_idx].volume > 0 else 0,
                    'put_volume': int(puts.loc[closest_put_idx].volume) if puts.loc[closest_put_idx].volume > 0 else 0
                })
        
        return skew_data
    else:
        print("No implied volatility data available")
        return None

def analyze_term_structure(symbol, num_expiries=5):
    """Analyze volatility term structure"""
    print(f"\nAnalyzing volatility term structure for {symbol}...")
    ticker = yf.Ticker(symbol)
    
    # Get list of available expiry dates
    expiries = ticker.options
    if not expiries:
        print("No options expiry dates available")
        return None
    
    # Limit to requested number of expiries
    expiries = expiries[:min(num_expiries, len(expiries))]
    print(f"Using expiry dates: {expiries}")
    
    term_structure = {
        'symbol': symbol,
        'current_price': ticker.history(period='1d').iloc[-1].Close,
        'expiries': [],
        'atm_iv': []
    }
    
    for expiry in expiries:
        try:
            # Get option chain for this expiry
            opt = ticker.option_chain(expiry)
            
            # Find ATM option
            calls = opt.calls
            calls['strike_diff'] = abs(calls.strike - term_structure['current_price'])
            atm_idx = calls.strike_diff.idxmin()
            atm_strike = calls.loc[atm_idx].strike
            
            if 'impliedVolatility' in calls.columns:
                atm_iv = calls.loc[atm_idx].impliedVolatility
                
                # Calculate days to expiry
                today = datetime.now()
                expiry_date = datetime.strptime(expiry, '%Y-%m-%d')
                days_to_expiry = (expiry_date - today).days
                
                if days_to_expiry > 0 and atm_iv > 0.001:
                    term_structure['expiries'].append({
                        'date': expiry,
                        'days': days_to_expiry,
                        'atm_strike': atm_strike,
                        'atm_iv': atm_iv
                    })
        except Exception as e:
            print(f"Error analyzing expiry {expiry}: {str(e)}")
    
    return term_structure

def test_implied_volatility_surface(symbol="GLD"):
    """Test retrieving and building an implied volatility surface"""
    
    print(f"\nTesting implied volatility surface for {symbol}...")
    
    # Get first three expiries
    ticker = yf.Ticker(symbol)
    expiries = ticker.options[:3] if len(ticker.options) >= 3 else ticker.options
    
    surface_data = {'symbol': symbol, 'data': []}
    
    for i, expiry in enumerate(expiries):
        print(f"\nProcessing expiry {expiry}...")
        try:
            opt = ticker.option_chain(expiry)
            
            # Get moneyness levels
            current_price = ticker.history(period='1d').iloc[-1].Close
            
            # Create a merged dataframe with calls and puts
            calls = opt.calls.copy()
            calls['option_type'] = 'call'
            puts = opt.puts.copy()
            puts['option_type'] = 'put'
            
            # Calculate moneyness
            calls['moneyness'] = calls.strike / current_price
            puts['moneyness'] = puts.strike / current_price
            
            # Filter to reasonable moneyness range and valid IV
            valid_calls = calls[(calls.moneyness >= 0.8) & 
                               (calls.moneyness <= 1.2) & 
                               (calls.impliedVolatility > 0.001)]
            
            valid_puts = puts[(puts.moneyness >= 0.8) & 
                             (puts.moneyness <= 1.2) & 
                             (puts.impliedVolatility > 0.001)]
            
            print(f"Valid calls: {len(valid_calls)}, Valid puts: {len(valid_puts)}")
            
            if not valid_calls.empty or not valid_puts.empty:
                # Calculate days to expiry
                today = datetime.now()
                expiry_date = datetime.strptime(expiry, '%Y-%m-%d')
                days_to_expiry = (expiry_date - today).days
                
                surface_data['data'].append({
                    'expiry': expiry,
                    'days_to_expiry': days_to_expiry,
                    'calls': valid_calls[['moneyness', 'strike', 'impliedVolatility', 'volume']].to_dict('records'),
                    'puts': valid_puts[['moneyness', 'strike', 'impliedVolatility', 'volume']].to_dict('records')
                })
        except Exception as e:
            print(f"Error processing expiry {expiry}: {str(e)}")
    
    return surface_data

# Test with GLD (Gold ETF)
print("===== Testing GLD options data =====")
option_data = get_option_chain_data("GLD")

print("\n===== Testing implied volatility skew =====")
skew_data = extract_volatility_skew(option_data)
if skew_data and skew_data['skew']:
    print(f"Successfully extracted volatility skew with {len(skew_data['skew'])} data points")
    # Print a few sample points
    print("Sample volatility skew data:")
    for point in skew_data['skew'][:3]:
        print(f"  Moneyness: {point['moneyness']:.2f}, Call IV: {point['call_iv']:.2f}, Put IV: {point['put_iv']:.2f}")
else:
    print("Could not extract volatility skew")

print("\n===== Testing volatility term structure =====")
term_structure = analyze_term_structure("GLD", num_expiries=5)
if term_structure and term_structure['expiries']:
    print(f"Successfully analyzed term structure with {len(term_structure['expiries'])} expiries")
    print("Term structure data:")
    for expiry in term_structure['expiries']:
        print(f"  Expiry: {expiry['date']}, Days: {expiry['days']}, ATM IV: {expiry['atm_iv']:.2f}")
else:
    print("Could not analyze volatility term structure")

print("\n===== Testing volatility surface =====")
surface = test_implied_volatility_surface("GLD")
if surface and surface['data']:
    print(f"Successfully created volatility surface with {len(surface['data'])} expiries")
    for expiry_data in surface['data']:
        print(f"  Expiry: {expiry_data['expiry']}, Days: {expiry_data['days_to_expiry']}")
        print(f"    Calls: {len(expiry_data['calls'])}, Puts: {len(expiry_data['puts'])}")
else:
    print("Could not create volatility surface")