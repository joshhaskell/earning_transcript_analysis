from datetime import datetime
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
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    tokens = nltk.word_tokenize(text)
    # Remove stopwords and perform lemmatization
    lemmatizer = WordNetLemmatizer()
    clean_tokens = [lemmatizer.lemmatize(word) for word in tokens if word not in stopwords.words('english')]
    return ' '.join(clean_tokens)

def extract_ngrams(data, num):
    n_grams = ngrams(nltk.word_tokenize(data), num)
    return [' '.join(grams) for grams in n_grams]

def sentiment_polarity(text):
    return TextBlob(text).sentiment.polarity