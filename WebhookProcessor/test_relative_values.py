import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def get_relative_value_data():
    """Get data for relative value calculations"""
    print("Fetching data for relative value calculations...")
    
    # Define the pairs we want to analyze
    pairs = {
        'Gold/Silver': ['GC=F', 'SI=F'],
        'Gold/Oil': ['GC=F', 'CL=F'],
        'Gold/SP500': ['GC=F', '^GSPC'],
        'Gold/TenYearYield': ['GC=F', '^TNX'],
        'Gold/Dollar': ['GC=F', 'DX-Y.NYB']
    }
    
    # Dictionary to store results
    results = {}
    
    # Get historical data for calculating percentiles
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365*5)  # 5 years of data
    
    for pair_name, symbols in pairs.items():
        print(f"\nAnalyzing {pair_name}: {symbols[0]} vs {symbols[1]}")
        
        try:
            # Get current values
            current_data = yf.download(symbols, period='1d')
            
            if 'Close' in current_data.columns and len(current_data) > 0:
                # Check if we have data for both symbols
                if isinstance(current_data['Close'], pd.DataFrame) and all(s in current_data['Close'].columns for s in symbols):
                    latest_values = [float(current_data['Close'][s].iloc[-1]) for s in symbols]
                    
                    # Make sure we don't have NaN values
                    if np.isnan(latest_values[0]) or np.isnan(latest_values[1]):
                        print(f"  Warning: NaN values detected for {pair_name}")
                        continue
                        
                    current_ratio = latest_values[0] / latest_values[1]
                    print(f"  Current ratio: {current_ratio:.4f}")
                    
                    # Get historical data for percentile calculations
                    try:
                        hist_data = yf.download(symbols, start=start_date, end=end_date)
                        
                        if 'Close' in hist_data.columns and len(hist_data) > 30:  # Ensure we have enough data
                            # Calculate historical ratios
                            ratios = pd.Series(index=hist_data.index)
                            
                            for i in range(len(hist_data)):
                                if isinstance(hist_data['Close'], pd.DataFrame) and all(s in hist_data['Close'].columns for s in symbols):
                                    val1 = hist_data['Close'][symbols[0]].iloc[i]
                                    val2 = hist_data['Close'][symbols[1]].iloc[i]
                                    
                                    if not (np.isnan(val1) or np.isnan(val2) or val2 == 0):
                                        ratios.iloc[i] = val1 / val2
                            
                            # Remove NaN values
                            ratios = ratios.dropna()
                            
                            if len(ratios) > 30:  # Ensure we have enough data after cleaning
                                percentile = stats.percentileofscore(ratios.values, current_ratio)
                                
                                # Statistical properties
                                mean_ratio = np.mean(ratios)
                                median_ratio = np.median(ratios)
                                std_ratio = np.std(ratios)
                                min_ratio = np.min(ratios)
                                max_ratio = np.max(ratios)
                                
                                # Z-score (how many standard deviations from mean)
                                z_score = (current_ratio - mean_ratio) / std_ratio
                                
                                print(f"  Current percentile: {percentile:.2f}%")
                                print(f"  Z-score: {z_score:.2f}")
                                
                                results[pair_name] = {
                                    'symbols': symbols,
                                    'current_ratio': current_ratio,
                                    'percentile': percentile,
                                    'z_score': z_score,
                                    'mean': mean_ratio,
                                    'median': median_ratio,
                                    'std': std_ratio,
                                    'min': min_ratio,
                                    'max': max_ratio,
                                    'data_points': len(ratios)
                                }
                            else:
                                print(f"  Insufficient clean historical data for {pair_name}")
                        else:
                            print(f"  Insufficient historical data for {pair_name}")
                    except Exception as e:
                        print(f"  Error calculating historical data for {pair_name}: {str(e)}")
                else:
                    print(f"  Missing data for one or more symbols in {pair_name}")
            else:
                print(f"  No current data available for {pair_name}")
        except Exception as e:
            print(f"  Error analyzing {pair_name}: {str(e)}")
    
    return results

def calculate_cross_asset_correlations():
    """Calculate correlations between gold and other assets"""
    print("\nCalculating cross-asset correlations with gold...")
    
    # Define assets to correlate with gold
    assets = ['GC=F', 'SI=F', 'CL=F', '^GSPC', '^TNX', 'DX-Y.NYB', '^VIX']
    asset_names = ['Gold', 'Silver', 'Oil', 'S&P500', '10Y Yield', 'Dollar Index', 'VIX']
    
    # Get data for the past year
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    try:
        # Download data
        data = yf.download(assets, start=start_date, end=end_date)
        
        if 'Close' in data.columns and len(data) > 30:
            # Extract close prices
            closes = data['Close']
            
            # Calculate returns
            returns = closes.pct_change().dropna()
            
            # Calculate correlations with gold
            if 'GC=F' in returns.columns:
                gold_correlations = {}
                
                for i, asset in enumerate(assets):
                    if asset != 'GC=F' and asset in returns.columns:
                        # Calculate rolling correlations (30-day window)
                        rolling_corr = returns['GC=F'].rolling(window=30).corr(returns[asset])
                        
                        # Current correlation
                        current_corr = rolling_corr.iloc[-1]
                        
                        # 30-day high and low
                        corr_30d_high = rolling_corr[-30:].max()
                        corr_30d_low = rolling_corr[-30:].min()
                        
                        print(f"Gold correlation with {asset_names[i]}: {current_corr:.3f}")
                        print(f"  30-day range: {corr_30d_low:.3f} to {corr_30d_high:.3f}")
                        
                        gold_correlations[asset_names[i]] = {
                            'current': current_corr,
                            '30d_high': corr_30d_high,
                            '30d_low': corr_30d_low,
                            'trend': 'strengthening' if current_corr > rolling_corr[-10:].mean() else 'weakening'
                        }
                
                return gold_correlations
            else:
                print("Gold data not available in returns dataset")
        else:
            print("Insufficient data for correlation analysis")
    except Exception as e:
        print(f"Error calculating correlations: {str(e)}")
    
    return None

def calculate_reversion_potential():
    """Calculate potential mean reversion in gold ratios"""
    print("\nCalculating mean reversion potential...")
    
    # Pairs with strong mean-reverting tendencies
    pairs = {
        'Gold/Silver Ratio': ['GC=F', 'SI=F'],
        'Gold/Oil Ratio': ['GC=F', 'CL=F']
    }
    
    results = {}
    
    for pair_name, symbols in pairs.items():
        print(f"\nAnalyzing {pair_name} reversion potential...")
        
        try:
            # Get 5 years of data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365*5)
            
            data = yf.download(symbols, start=start_date, end=end_date)
            
            if 'Close' in data.columns and len(data) > 252:  # At least a year of data
                # Calculate ratio
                if isinstance(data['Close'], pd.DataFrame) and all(s in data['Close'].columns for s in symbols):
                    # Create ratio series
                    ratio = data['Close'][symbols[0]] / data['Close'][symbols[1]]
                    
                    # Calculate current values
                    current_ratio = ratio.iloc[-1]
                    
                    # Calculate statistics
                    mean_ratio = ratio.mean()
                    median_ratio = ratio.median()
                    std_ratio = ratio.std()
                    
                    # Calculate z-score
                    z_score = (current_ratio - mean_ratio) / std_ratio
                    
                    # Calculate percentiles
                    percentile_5 = ratio.quantile(0.05)
                    percentile_95 = ratio.quantile(0.95)
                    
                    # Check if current ratio is near extremes
                    is_extreme = current_ratio < percentile_5 or current_ratio > percentile_95
                    
                    # Reversion potential
                    reversion_to_mean = ((mean_ratio / current_ratio) - 1) * 100  # Percentage move to mean
                    
                    print(f"Current {pair_name}: {current_ratio:.2f}")
                    print(f"Mean: {mean_ratio:.2f}, Median: {median_ratio:.2f}")
                    print(f"Z-score: {z_score:.2f}")
                    print(f"Reversion potential to mean: {reversion_to_mean:.2f}%")
                    print(f"Is at extreme: {is_extreme}")
                    
                    results[pair_name] = {
                        'current': current_ratio,
                        'mean': mean_ratio,
                        'median': median_ratio,
                        'std': std_ratio,
                        'z_score': z_score,
                        'reversion_potential_pct': reversion_to_mean,
                        'is_extreme': is_extreme
                    }
                else:
                    print(f"Missing data for one or both symbols in {pair_name}")
            else:
                print(f"Insufficient data for {pair_name}")
        except Exception as e:
            print(f"Error analyzing {pair_name}: {str(e)}")
    
    return results

try:
    # Try running the relative value calculation without stats module
    print("Testing relative value data...")
    
    # Define the pairs we want to analyze
    pairs = {
        'Gold/Silver': ['GC=F', 'SI=F'],
        'Gold/Oil': ['GC=F', 'CL=F'],
        'Gold/SP500': ['GC=F', '^GSPC'],
        'Gold/TenYearYield': ['GC=F', '^TNX'],
        'Gold/Dollar': ['GC=F', 'DX-Y.NYB']
    }
    
    for pair_name, symbols in pairs.items():
        print(f"\nAnalyzing {pair_name}: {symbols[0]} vs {symbols[1]}")
        
        # Get current values
        current_data = yf.download(symbols, period='1d')
        
        if 'Close' in current_data.columns:
            if isinstance(current_data['Close'], pd.DataFrame):
                for s in symbols:
                    if s in current_data['Close'].columns:
                        latest = current_data['Close'][s].iloc[-1] if not current_data['Close'][s].empty else None
                        print(f"  Latest {s}: {latest}")
                    else:
                        print(f"  {s} not in columns")
                
                # Try to calculate ratio
                if all(s in current_data['Close'].columns for s in symbols):
                    values = [current_data['Close'][s].iloc[-1] for s in symbols]
                    if not (np.isnan(values[0]) or np.isnan(values[1]) or values[1] == 0):
                        ratio = values[0]/values[1]
                        print(f"  {pair_name} Ratio: {ratio:.4f}")
                    else:
                        print(f"  Could not calculate {pair_name} ratio: invalid values")
                else:
                    print(f"  Could not calculate {pair_name} ratio: missing columns")
            else:
                print(f"  'Close' is not a DataFrame")
        else:
            print("  No Close data available")

    # Also test data availability for gold price vs various stocks
    print("\nTesting gold price relative to stock indices...")
    indices = ['GC=F', '^GSPC', '^DJI', '^IXIC', '^RUT']
    index_data = yf.download(indices, period='1mo')
    
    if 'Close' in index_data.columns:
        print(f"Successfully retrieved stock indices data, shape: {index_data.shape}")
        
        # Check most recent values
        latest_values = {}
        for idx in indices:
            if idx in index_data['Close'].columns:
                val = index_data['Close'][idx].iloc[-1]
                latest_values[idx] = val
                print(f"  Latest {idx}: {val}")
            else:
                print(f"  No data for {idx}")
        
        # Calculate gold/s&p ratio if available
        if 'GC=F' in latest_values and '^GSPC' in latest_values:
            gold_sp_ratio = latest_values['GC=F'] / latest_values['^GSPC'] 
            print(f"  Gold/S&P500 ratio: {gold_sp_ratio:.6f}")
            
            # How many gold ounces to buy S&P
            sp_in_gold_oz = latest_values['^GSPC'] / latest_values['GC=F']
            print(f"  S&P500 in gold ounces: {sp_in_gold_oz:.4f} oz")
    else:
        print("No Close data available for indices")
        
except Exception as e:
    print(f"Error in test: {str(e)}")