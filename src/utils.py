from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import string
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk import ngrams
from textblob import TextBlob
import os
import glob

# Constants
# Set range of years here
timeframe = 5
YEARS = range(datetime.now().year - timeframe, datetime.now().year + 1)  # Last 5 years

def identify_missing_quarters(df):
    """Identifies missing earnings call quarters for each company in the dataframe."""
    expected_quarters = [(q, y) for y in YEARS for q in range(1, 5)]
    current_year = datetime.now().year
    missing_info = {}
    for symbol in df['symbol'].unique():
        company_df = df[df['symbol'] == symbol]
        company_quarters = [(row['quarter'], row['year']) for index, row in company_df.iterrows()]

        # Adjust the expected quarters based on the current date
        adjusted_expected_quarters = expected_quarters.copy()
        if (4, current_year) in adjusted_expected_quarters:
            # Remove Q4 for the current year if the company follows the calendar year
            adjusted_expected_quarters.remove((4, current_year))
        
        # TODO: Add logic here to handle companies that don't follow the calendar year

        missing_quarters = set(adjusted_expected_quarters) - set(company_quarters)
        missing_info[symbol] = sorted(list(missing_quarters), key=lambda x: (x[1], x[0]))
    return missing_info

def preprocess_text(text):
    """Processes the given text by converting to lowercase, removing punctuation, stopwords, and lemmatizing."""
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    tokens = nltk.word_tokenize(text)
    # Remove stopwords and perform lemmatization
    lemmatizer = WordNetLemmatizer()
    clean_tokens = [lemmatizer.lemmatize(word) for word in tokens if word not in stopwords.words('english')]
    return ' '.join(clean_tokens)

def extract_ngrams(data, num):
    """Extracts n-grams from the provided text data."""
    n_grams = ngrams(nltk.word_tokenize(data), num)
    return [' '.join(grams) for grams in n_grams]

def sentiment_polarity(text):
    """Calculates the sentiment polarity of the given text using TextBlob."""
    return TextBlob(text).sentiment.polarity

def count_entity_types(entities):
    """Extracts and Counts occurrences of different types of named entities in a list of tupples of word and entity pairings."""
    entity_types = [ent[1] for ent in entities]
    return pd.Series(entity_types).value_counts()

# functions for looking at volatility around the earnings call periods
def calculate_volatility(data, window=5):
    """Calculate the rolling standard deviation of a given Series."""
    return data.rolling(window=window).std()

def prepare_volatility_data(df, ticker, call_dates):
    """Prepare the volatility data for a given ticker and call dates."""
    summarized_volatility = []
    for call_date in call_dates:
        before = df[(df['symbol'] == ticker) & 
                    (df['date'] < call_date) & 
                    (df['date'] >= call_date - pd.Timedelta(days=5))]
        after = df[(df['symbol'] == ticker) & 
                   (df['date'] > call_date) & 
                   (df['date'] <= call_date + pd.Timedelta(days=5))]
        avg_vol_before = before['volatility'].mean() * 100
        avg_vol_after = after['volatility'].mean() * 100
        summarized_volatility.append({
            'date': call_date,
            'Before Earnings Call': avg_vol_before,
            'After Earnings Call': avg_vol_after
        })
    summarized_df = pd.DataFrame(summarized_volatility)
    return summarized_df

def plot_ticker_volatility(ax, summarized_df, ticker):
    """Plot the average volatility before and after earnings calls for a given ticker."""
    summarized_df.plot(kind='bar', ax=ax, rot=45, title=ticker)
    ax.set_xlabel('Earnings Call Dates')
    ax.set_ylabel('Avg Volatility (Std. Dev. of Daily Returns %)')
    ax.yaxis.set_major_formatter(plt.FuncFormatter('{:.0f}%'.format))


def adjust_to_trading_day(date, trading_dates):
    """Adjust the given date to the nearest trading day if it is not already a trading day."""
    while date not in trading_dates:
        date -= pd.Timedelta(days=1)
    return date

def load_and_prepare_prices(filepath, tickers_to_drop):
    """Loads and preprocesses the stock price data."""
    df = pd.read_csv(filepath)
    df = df[~df['symbol'].isin(tickers_to_drop)]
    df['date'] = pd.to_datetime(df['date']).dt.normalize()
    return df

def load_and_combine_transcripts(directory, tickers_to_drop):
    """Loads and combines transcript data from multiple files."""
    transcript_files = glob.glob(os.path.join(directory, '*_transcripts.json'))
    all_transcripts = [pd.read_json(file) for file in transcript_files]
    combined_df = pd.concat(all_transcripts, ignore_index=True)
    combined_df = combined_df[~combined_df['symbol'].isin(tickers_to_drop)]
    combined_df['date'] = pd.to_datetime(combined_df['date']).dt.normalize()
    return combined_df

def get_pre_call_window_metrics(df, ticker, days_before):
    """Create a window of time before each earnings call date for a given ticker."""
    metrics_data = []
    ticker_df = df[df['symbol'] == ticker]
    call_dates = ticker_df[~ticker_df['content'].isna()]['date'].unique()

    for date in call_dates:
        # Adjust the date if it falls on a weekend or non-trading day
        adjusted_date = date
        while adjusted_date.weekday() > 4 or adjusted_date not in ticker_df['date'].values:
            adjusted_date -= pd.Timedelta(days=1)

        start_date = adjusted_date - pd.Timedelta(days=days_before)

        # Filter data within the time window for the specific ticker
        data_in_window = ticker_df[(ticker_df['date'] >= start_date) & (ticker_df['date'] < adjusted_date)]

        # Calculate metrics
        volatility = data_in_window['close'].std() if len(data_in_window) > 1 else 0
        percent_change = ((data_in_window['close'].iloc[-1] - data_in_window['close'].iloc[0]) / data_in_window['close'].iloc[0]) * 100 if len(data_in_window) > 0 else 0

        metrics_data.append({
            'original_call_date': date,
            'adjusted_call_date': adjusted_date,
            'symbol': ticker,
            'timeframe': f'{days_before}_days_before',
            'volatility': volatility,
            'pre_call_price_percent_change': percent_change
        })

    return pd.DataFrame(metrics_data)

def calculate_post_call_price_direction(original_df, metrics_df, post_call_days):
    """Calculate the price direction after a specified number of days post earnings call."""
    post_call_direction = []

    for index, row in metrics_df.iterrows():
        call_date = row['original_call_date']
        ticker = row['symbol']
        post_call_date = call_date + pd.Timedelta(days=post_call_days)

        # Ensure the post call date doesn't fall on a weekend or non-trading day
        while post_call_date.weekday() > 4 or post_call_date not in original_df['date'].values:
            post_call_date += pd.Timedelta(days=1)

        # Get closing prices on the call date and the post call date
        call_close_price = original_df.loc[(original_df['symbol'] == ticker) & (original_df['date'] == call_date), 'close'].iloc[0]
        post_call_close_price = original_df.loc[(original_df['symbol'] == ticker) & (original_df['date'] == post_call_date), 'close'].iloc[0]

        # Determine the direction (1 if price increased, 0 if decreased or unchanged)
        direction = 1 if post_call_close_price > call_close_price else 0
        post_call_direction.append(direction)

    return post_call_direction

