import quandl
import pandas as pd
import os

print("Testing Quandl CFTC data access...")

# Check if there's a Quandl API key in the environment
api_key = os.environ.get('QUANDL_API_KEY')
if api_key:
    print(f"Found QUANDL_API_KEY in environment variables, will authenticate")
    quandl.ApiConfig.api_key = api_key
else:
    print("No QUANDL_API_KEY found in environment variables, limited to public datasets")

try:
    # Try to access CFTC Commitment of Traders data for Gold
    # CFTC publishes COT data weekly
    print("\nAttempting to access CFTC COT data for Gold...")
    
    # Example dataset: "CFTC/GC_F_ALL"
    # This dataset contains the Commitment of Traders report for Gold futures
    try:
        gold_cot = quandl.get("CFTC/GC_F_ALL", rows=5)
        print(f"Successfully accessed CFTC Gold COT data, shape: {gold_cot.shape}")
        if not gold_cot.empty:
            print("\nSample CFTC Gold COT data:")
            print(gold_cot.head())
            print("\nColumn names:")
            print(gold_cot.columns.tolist())
    except Exception as e:
        print(f"Error accessing CFTC Gold COT data: {str(e)}")
    
    # Try an alternative dataset format
    try:
        print("\nTrying alternative CFTC dataset format...")
        gold_cot_alt = quandl.get("CFTC/088691_FO_ALL", rows=5)
        print(f"Successfully accessed alternative CFTC dataset, shape: {gold_cot_alt.shape}")
        if not gold_cot_alt.empty:
            print("\nSample alternative CFTC dataset:")
            print(gold_cot_alt.head())
    except Exception as e:
        print(f"Error accessing alternative CFTC dataset: {str(e)}")
        
    # Try searching Quandl for available CFTC datasets
    try:
        print("\nSearching for available CFTC datasets...")
        search_results = quandl.search("CFTC Gold", database_code="CFTC", max_per_page=3)
        print(f"Search returned {len(search_results['datasets'])} results")
        
        for i, dataset in enumerate(search_results['datasets']):
            print(f"\nDataset {i+1}:")
            print(f"  Code: {dataset['database_code']}/{dataset['dataset_code']}")
            print(f"  Name: {dataset['name']}")
            print(f"  Description: {dataset.get('description', 'No description')[:100]}...")
    except Exception as e:
        print(f"Error searching for CFTC datasets: {str(e)}")

except Exception as e:
    print(f"Error testing Quandl CFTC data: {str(e)}")

print("\nQuandl CFTC testing complete.")