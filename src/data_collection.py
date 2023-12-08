import requests
import os
import io
import json
import pandas as pd
from datetime import datetime

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# API Key
FMP_API_KEY = os.getenv('FMP_API_KEY')

# Constants
YEARS = range(datetime.now().year - 5, datetime.now().year + 1)  # Last 5 years

def fetch_us_airline_tickers():
    """Fetch US airline tickers using the bulk profile endpoint."""
    url = f"https://financialmodelingprep.com/api/v4/profile/all?apikey={FMP_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = pd.read_csv(io.BytesIO(response.content))
        us_airlines = data[(data['country'] == 'US') & (data['industry'] == 'Airlines')]
        return us_airlines['Symbol'].tolist()
    else:
        print(f"Failed to fetch bulk profiles: HTTP {response.status_code}")
        return []

def fetch_earning_transcripts(ticker):
    """Fetch earning call transcripts for a given ticker."""
    transcripts = []
    for year in YEARS:
        url = f"https://financialmodelingprep.com/api/v3/earning_call_transcript/{ticker}?year={year}&apikey={FMP_API_KEY}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if data: 
                    transcripts.extend(data)
            else:
                print(f"Failed to fetch transcripts for {ticker}: HTTP {response.status_code}")
        except Exception as e:
            print(f"Error fetching transcripts for {ticker}: {e}")
    return transcripts

def fetch_financial_data(ticker):
    """Fetch financial data for a given ticker."""
    url = f"https://financialmodelingprep.com/api/v3/financials/income-statement/{ticker}?apikey={FMP_API_KEY}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch financial data for {ticker}: HTTP {response.status_code}")
    except Exception as e:
        print(f"Error fetching financial data for {ticker}: {e}")
    return None

def save_data(data, filename):
    """Save data to a file in the data/raw directory."""
    current_directory = os.path.dirname(os.path.abspath(__file__)) # getting absolute path
    data_directory = os.path.join(current_directory, '..', 'data', 'raw') # adding current directory to the path
    file_path = os.path.join(data_directory, filename)

    with open(file_path, 'w') as file:
        json.dump(data, file)

def main():
    print("Getting list of tickers")
    tickers = fetch_us_airline_tickers()
    if not tickers:
        print("No US airline tickers found. Exiting.")
        return

    for ticker in tickers:
        print(f"Fetching data for {ticker}...")
        transcripts = fetch_earning_transcripts(ticker)
        if not transcripts:
            print(f"No transcripts available for {ticker}. Skipping.")
            continue
        financial_data = fetch_financial_data(ticker)

        save_data(transcripts, f"{ticker}_transcripts.json")
        save_data(financial_data, f"{ticker}_financials.json")

if __name__ == "__main__":
    main()
