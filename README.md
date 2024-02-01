# Earnings Call Analysis and Stock Prediction

## Project Overview

This project aims to analyze earnings call transcripts and stock price data to model predictions of stock price movements post-earnings calls. I conducted extensive exploratory data analysis and built machine learning models to predict the direction of stock price changes based on the sentiment expressed in earnings calls.

## Data Description

The dataset includes earnings call transcripts and historical stock prices spanning from 2018 to 2023 for the Airline industry. Features extracted from the transcripts include polarity, subjectivity, and word count. Stock price features include volatility and price percent changes before and after the earnings calls.

## Methodology

The analysis followed these steps:

1. **Data Collection**: Collecting transcript and prices data from Financial Modeling Prep API.
2. **Data Preprocessing**: Data cleaning, handling missing values, and feature engineering to prepare the dataset for modeling.
3. **Exploratory Data Analysis**: Investigating distributions, trends, and relationships within the data looking generally, at the call level scope as well as the stock prices in separate notebooks.
4. **Feature Engineering**: Generating new features such as sentiment scores from earnings call transcripts.
5. **Modeling**: Building and tuning various machine learning models to predict the direction of stock price movement.
6. **Evaluation**: Assessing model performance using metrics like accuracy, precision, recall, and ROC-AUC.

## Key Insights from EDA

- Sentiment analysis revealed a correlation between the tone of earnings calls and subsequent stock price movement.
- Word count and certain keywords were indicative of stock price volatility post-earnings calls.
- Demonstrates that further work is needed to extract the relevant text from the transcripts and reduce the noise.

## Modeling Results

The best-performing model was a Gaussian Naive Bayes classifier, achieving a test accuracy of approximately 67%. Other models such as Random Forest, XGBoost, and Gradient Boosting were also evaluated. 

## Repository Structure

- `notebooks/`: Jupyter notebooks containing detailed analysis and modeling steps.
- `src/`: Source code for data collection, custom functions and utilities used in the notebooks.
- `data/raw/`: Directory containing transcripts and prices collected using the data_collection file.
- `README.md`: Provides an overview of the project.

## Conclusions and Next Steps

The findings suggest that sentiment analysis of earnings calls can be predictive of stock price movements. Future work will include incorporating more data, refining feature engineering, and exploring further NLP techniques and utilizing LLMs into extracting and processing the text in a more relevant way.