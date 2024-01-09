from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import string
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk import ngrams
from textblob import TextBlob

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