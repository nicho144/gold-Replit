import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import json

print("Testing relative value pairs:")
pairs = {
    'Gold/Silver': ['GC=F', 'SI=F'], 
    'Gold/Oil': ['GC=F', 'CL=F'], 
    'Gold/SP500': ['GC=F', '^GSPC'],
    'Gold/USD': ['GC=F', 'DX-Y.NYB'],
    'Gold/10Y': ['GC=F', '^TNX']
}

for name, symbols in pairs.items():
    print(f"\nTesting {name}: {symbols[0]} vs {symbols[1]}")
    try:
        data = yf.download(symbols, period='1mo', interval='1d')
        print(f"  Downloaded data shape: {data.shape}")
        if 'Close' in data.columns:
            for s in symbols:
                if isinstance(data['Close'], pd.DataFrame) and s in data['Close'].columns:
                    latest = data['Close'][s].iloc[-1] if not data['Close'][s].empty else None
                    print(f"  Latest {s}: {latest}")
                else:
                    print(f"  {s} not in columns or empty")
            
            # Try to calculate ratio
            if isinstance(data['Close'], pd.DataFrame):
                if all(s in data['Close'].columns for s in symbols):
                    if not data['Close'][symbols[0]].empty and not data['Close'][symbols[1]].empty:
                        latest_values = [data['Close'][s].iloc[-1] for s in symbols]
                        if None not in latest_values and 0 not in latest_values:
                            ratio = latest_values[0]/latest_values[1]
                            print(f"  {name} Ratio: {ratio:.4f}")
                        else:
                            print(f"  Could not calculate {name} ratio: invalid values")
                    else:
                        print(f"  Could not calculate {name} ratio: empty data")
                else:
                    print(f"  Could not calculate {name} ratio: missing columns")
            else:
                print(f"  Could not calculate {name} ratio: data format issue")
        else:
            print("  No Close data available")
    except Exception as e:
        print(f"  Error testing {name}: {str(e)}")

# Test options data more thoroughly
print("\n\nTesting options data for GLD:")
try:
    ticker = yf.Ticker('GLD')
    print(f"Options expiry dates: {ticker.options}")
    
    if ticker.options:
        # Get first expiry date
        expiry = ticker.options[0]
        print(f"\nOptions chain for {expiry}:")
        opt = ticker.option_chain(expiry)
        
        print(f"Calls available: {len(opt.calls)}")
        print(f"Puts available: {len(opt.puts)}")
        
        # Print column names
        print(f"\nOptions data columns: {list(opt.calls.columns)}")
        
        # Calculate implied volatility surface data availability
        if 'impliedVolatility' in opt.calls.columns:
            print("\nImplied Volatility data is available for options")
            iv_data = opt.calls[['strike', 'impliedVolatility']].head(5)
            print(iv_data)
        else:
            print("\nImplied Volatility data NOT available")
except Exception as e:
    print(f"Error testing options: {str(e)}")

# Test Volume and Open Interest for futures
print("\n\nTesting Volume and Open Interest for Gold Futures:")
try:
    gold_futures = ['GC=F', 'GCJ24.CMX', 'GCK24.CMX', 'GCM24.CMX', 'GCQ24.CMX', 'GCZ24.CMX']
    print(f"Attempting to get data for: {gold_futures}")
    
    data = yf.download(gold_futures, period='1mo')
    print(f"Data shape: {data.shape}")
    
    if 'Volume' in data.columns:
        print("\nVolume data available:")
        vol_data = data['Volume'].tail(3)
        print(vol_data)
    else:
        print("\nVolume data NOT available in standard format")
        
    # Check for other volume-related columns
    all_cols = [col for col in data.columns.get_level_values(0)]
    print(f"\nAll available columns: {all_cols}")
    
except Exception as e:
    print(f"Error testing volume/OI: {str(e)}")