import requests
import os
import io
import json
import pandas as pd
from datetime import datetime, timedelta
import time

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# API Key
FMP_API_KEY = os.getenv('FMP_API_KEY')

# Constants
YEARS = range(datetime.now().year - 5, datetime.now().year + 1)  # Last 5 years

def fetch_us_airline_tickers(fmp_api_key):
    """Fetch US airline tickers using the bulk profile endpoint."""
    url = f"https://financialmodelingprep.com/api/v4/profile/all?apikey={fmp_api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        data = pd.read_csv(io.BytesIO(response.content))
        us_airlines = data[(data['country'] == 'US') & (data['industry'] == 'Airlines')]
        return us_airlines['Symbol'].tolist()
    else:
        print(f"Failed to fetch bulk profiles: HTTP {response.status_code}")
        return []

def fetch_available_transcripts_metadata(ticker, fmp_api_key):
    url = f"https://financialmodelingprep.com/api/v4/earning_call_transcript?symbol={ticker}&apikey={fmp_api_key}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
    except requests.RequestException as e:
        print(f"Failed to fetch transcript metadata for {ticker}: HTTP {response.status_code}")
        return []
    return None

def fetch_earning_transcripts(ticker, fmp_api_key):
    """Fetch earning call transcripts for a given ticker based on available metadata."""
    transcripts = []
    metadata = fetch_available_transcripts_metadata(ticker, fmp_api_key)
    for entry in metadata:
        quarter, year, _ = entry
        if year in YEARS:
            transcript_url = f"https://financialmodelingprep.com/api/v3/earning_call_transcript/{ticker}?year={year}&quarter={quarter}&apikey={fmp_api_key}"
            try:
                response = requests.get(transcript_url)
                if response.status_code == 200:
                    data = response.json()
                    if data: 
                        transcripts.extend(data)
                else:
                    print(f"Failed to fetch transcripts for {ticker} in {year} Q{quarter}: HTTP {response.status_code}")
            except Exception as e:
                print(f"Error fetching transcripts for {ticker} in {year} Q{quarter}: {e}")
    return transcripts

def fetch_historical_prices(tickers, fmp_api_key, start_year, end_year):
    """Fetch historical end-of-day prices for list of tickers."""
    historical_prices = []
    start_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 12, 31)
    current_date = start_date

    while current_date <= end_date:
        url = f"https://financialmodelingprep.com/api/v4/batch-request-end-of-day-prices?date={current_date.strftime('%Y-%m-%d')}&apikey={fmp_api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            data = pd.read_csv(io.BytesIO(response.content))
            # Filter for our tickers of interest
            filtered_data = data[data['symbol'].isin(tickers)]
            if not filtered_data.empty:
                filtered_data.loc[:,'date'] = current_date
                historical_prices.append(filtered_data)
        else:
            print(f"Failed to fetch price data for date {current_date.strftime('%Y-%m-%d')}: HTTP {response.status_code}")

        time.sleep(.5) # slow down for rate limit
        current_date += timedelta(days=1)

    # Combine into a single DataFrame
    historical_prices_df = pd.concat(historical_prices, ignore_index=True)
    return historical_prices_df

def save_data(data, filename):
    """Save data to a file in the data/raw directory."""
    current_directory = os.path.dirname(os.path.abspath(__file__)) # getting current directory absolute path
    data_directory = os.path.join(current_directory, '..', 'data', 'raw') # adding current directory to the path
    file_path = os.path.join(data_directory, filename)
    with open(file_path, 'w') as file:
        json.dump(data, file)

def main():
    print("Getting list of tickers")
    tickers = fetch_us_airline_tickers(FMP_API_KEY)
    if not tickers:
        print("No US airline tickers found. Exiting.")
        return
    # Getting transcripts
    for ticker in tickers:
        print(f"Fetching data for {ticker}...")
        transcripts = fetch_earning_transcripts(ticker, FMP_API_KEY)
        if not transcripts:
            print(f"No transcripts available for {ticker}. Skipping.")
        else:
            save_data(transcripts, f"{ticker}_transcripts.json")

    # Getting historical prices
    print("Fetching historical prices")
    historical_prices_df = fetch_historical_prices(tickers, FMP_API_KEY, YEARS[0], YEARS[-1])
    historical_prices_file_path = os.path.join('data', 'raw', 'historical_prices.csv')
    historical_prices_df.to_csv(historical_prices_file_path, index=False)
    print(f"Historical prices data saved to {historical_prices_file_path}")

if __name__ == "__main__":
    main()
