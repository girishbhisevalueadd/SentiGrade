import pandas as pd
import numpy as np
import chardet
import logging
import traceback
import matplotlib

# Module-level logger; configuration is set up in app.py. If market_sentiment is
# imported standalone, basicConfig provides a sensible default.
logger = logging.getLogger('sentigrade.market_sentiment')
if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# Use a non-interactive backend for Matplotlib (no GUI)
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from wordcloud import WordCloud 
import datetime
import time
from datetime import timedelta
from cachetools import cached, TTLCache
from typing import Tuple
import nltk
from nltk.corpus import stopwords
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
import stopwordsiso as swiso  # For more comprehensive stopwords
import plotly.graph_objects as go
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import os
import io
import base64
import json
import plotly.io as pio
 
# Initialize stopwords and sentiment analyzer
stop_words = set(stopwords.words('english'))
analyzer = SentimentIntensityAnalyzer()
# Merge multiple stopword lists
nltk_stopwords = set(stopwords.words('english'))
sklearn_stopwords = ENGLISH_STOP_WORDS
iso_stopwords = swiso.stopwords('en')  # English stopwords from stopwordsiso

# Combine all stopwords into a single set
combined_stopwords = nltk_stopwords | sklearn_stopwords | iso_stopwords


def fetch_news_headline(date, ticker):
    """
    Fetches one or multiple news headlines for a given date and stock ticker for stock chart hover It is For Stock Chart Section.
    
    Parameters:
    - date: Date string in 'YYYY-MM-DD' format.
    - ticker: Stock ticker symbol.
    
    Returns:
    - List of headlines or an empty list if no news is available.
    """
    headlines = []
    
    # Define the file paths for each ticker
    file_paths = {
        "AAPL": r"C:\Users\VivekPol\OneDrive - ValueAdd Research and Analytics Solutions LLP\Desktop\Project\Vivek Project\Sentigrade_News_Analysis\Demo4\yahooData\AAPL_news.csv",
        "AMD": r"C:\Users\VivekPol\OneDrive - ValueAdd Research and Analytics Solutions LLP\Desktop\Project\Vivek Project\Sentigrade_News_Analysis\Demo4\yahooData\AMD_news.csv",
        "EBAY": r"C:\Users\VivekPol\OneDrive - ValueAdd Research and Analytics Solutions LLP\Desktop\Project\Vivek Project\Sentigrade_News_Analysis\Demo4\yahooData\EBAY_news.csv",
        "HPQ": r"C:\Users\VivekPol\OneDrive - ValueAdd Research and Analytics Solutions LLP\Desktop\Project\Vivek Project\Sentigrade_News_Analysis\Demo4\yahooData\HPQ_news.csv",
        "IBM": r"C:\Users\VivekPol\OneDrive - ValueAdd Research and Analytics Solutions LLP\Desktop\Project\Vivek Project\Sentigrade_News_Analysis\Demo4\yahooData\IBM_news.csv",
        "JNPR": r"C:\Users\VivekPol\OneDrive - ValueAdd Research and Analytics Solutions LLP\Desktop\Project\Vivek Project\Sentigrade_News_Analysis\Demo4\yahooData\JNPR_news.csv",
        "MSFT": r"C:\Users\VivekPol\OneDrive - ValueAdd Research and Analytics Solutions LLP\Desktop\Project\Vivek Project\Sentigrade_News_Analysis\Demo4\yahooData\MSFT_news.csv",
        "QCOM": r"C:\Users\VivekPol\OneDrive - ValueAdd Research and Analytics Solutions LLP\Desktop\Project\Vivek Project\Sentigrade_News_Analysis\Demo4\yahooData\QCOM_news.csv"
    }
    
    # Check if the ticker exists in the file paths
    if ticker not in file_paths:
        print(f"Ticker '{ticker}' not found.")
        return []

    # Convert the input date to datetime format
    try:
        date_obj = pd.to_datetime(date, format='%d-%m-%Y', errors='coerce')
        if pd.isna(date_obj):
            print(f"Invalid date format: {date}")
            return []
    except Exception as e:
        print(f"Error parsing input date: {e}")
        return []

    # Load the dataset
    file_path = file_paths[ticker]
    
    try:
        dataset = pd.read_csv(file_path, 
                              quotechar='"', 
                              skipinitialspace=True, 
                              usecols=['Date', 'NEWS'], 
                              encoding='ISO-8859-1')

        # **Ensure 'Date' column is properly converted to datetime**
        dataset['Date'] = pd.to_datetime(dataset['Date'], errors='coerce')

        # Filter for the matching date
        filtered_data = dataset[dataset['Date'].dt.date == date_obj.date()]

        # Extract the news headlines
        if not filtered_data.empty:
            headlines = filtered_data['NEWS'].dropna().tolist()

    except Exception as e:
        print(f"Error fetching news for {ticker} on {date}: {e}")
    
    return headlines




  
    
    
def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']


def get_recent_news(csv_path, start_date, end_date):
    """Fetches recent news within the specified date range from the CSV file. It is for Company news section"""
    try:
        encoding = detect_encoding(csv_path)
        df = pd.read_csv(csv_path, encoding=encoding)
        
        if df.empty:
            return []

        df.replace(np.nan, '', inplace=True)

        if 'Date' not in df.columns or 'NEWS' not in df.columns or 'LINK' not in df.columns:
            print("Missing required columns in CSV file.")
            return []

        # Convert date column to datetime
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])

        # Convert input dates to datetime
        start_date = pd.to_datetime(start_date, errors='coerce')
        end_date = pd.to_datetime(end_date, errors='coerce')

        if pd.isna(start_date) or pd.isna(end_date):
            print("Invalid date format provided.")
            return []

        # Filter data based on the provided date range
        mask = (df['Date'] >= start_date) & (df['Date'] <= end_date)
        df_filtered = df.loc[mask]

        if df_filtered.empty:
            print(f"No news data available between {start_date.date()} and {end_date.date()}.")
            return []

        df_filtered = df_filtered.sort_values(by='Date', ascending=False)
        recent_news = df_filtered[['Date', 'NEWS', 'LINK']].to_dict(orient='records')

        return recent_news

    except Exception as e:
        print(f"Error processing CSV file: {e}")
        return []
    
    


def create_stock_chart(symbol, date_from, date_to, chart_path):
    """
    Generates a stock price chart with news headlines on hover for the Stock Chart Section.
    Handles dates in DD/MM/YYYY format from the source CSV.
    """
    import pandas as pd
    import numpy as np
    import plotly.graph_objects as go
    import os
    from datetime import timedelta

    logger.info("create_stock_chart called symbol=%r date_from=%r date_to=%r chart_path=%r",
                symbol, date_from, date_to, chart_path)

    prices_csv = r"C:\Users\VivekPol\OneDrive - ValueAdd Research and Analytics Solutions LLP\Desktop\Project\Vivek Project\Sentigrade_News_Analysis\Demo4\yahooData\testPairsTrading_prices.csv"
    try:
        df = pd.read_csv(prices_csv)
        logger.debug("loaded prices CSV rows=%d cols=%s path=%s",
                     len(df), df.columns.tolist(), prices_csv)
    except Exception as e:
        logger.exception("failed loading prices CSV at %s", prices_csv)
        raise ValueError(f"Could not load price data: {e}")

    # Normalize ticker symbol (the CSV uses uppercase column headers)
    symbol = (symbol or "").strip().upper()

    # Check if symbol exists in the dataframe
    if symbol not in df.columns:
        available = [c for c in df.columns if c != 'Date']
        logger.warning("ticker not found symbol=%r available=%s", symbol, available)
        raise ValueError(f"Ticker '{symbol}' not found. Available tickers: {', '.join(available)}")

    # Convert Date column with explicit format DD/MM/YYYY
    try:
        df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')
        df = df.dropna(subset=['Date'])
        logger.debug("date column converted, rows remaining=%d, span=%s..%s",
                     len(df),
                     df['Date'].min().strftime('%Y-%m-%d') if not df.empty else 'N/A',
                     df['Date'].max().strftime('%Y-%m-%d') if not df.empty else 'N/A')
    except Exception as e:
        logger.warning("DD/MM/YYYY parse failed (%s); falling back to dayfirst=True", e)
        try:
            df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
            df = df.dropna(subset=['Date'])
        except Exception as e2:
            logger.exception("dayfirst date parse also failed")
            raise ValueError(f"Could not parse Date column in price CSV: {e2}")

    # Parse input dates for filtering. The HTML <input type="date"> always submits
    # YYYY-MM-DD, so parse ISO-first and fall back to dayfirst for any other format.
    def _parse_input_date(value):
        try:
            return pd.to_datetime(value, format='%Y-%m-%d')
        except (ValueError, TypeError):
            return pd.to_datetime(value, dayfirst=True)

    try:
        date_from_dt = _parse_input_date(date_from)
        date_to_dt = _parse_input_date(date_to)
        logger.info("parsed input dates from=%s -> %s, to=%s -> %s",
                    date_from, date_from_dt.strftime('%Y-%m-%d'),
                    date_to, date_to_dt.strftime('%Y-%m-%d'))
    except Exception as e:
        logger.exception("input date parse failed")
        raise ValueError(f"Could not parse input dates '{date_from}' / '{date_to}': {e}")

    if date_from_dt > date_to_dt:
        logger.warning("invalid range: from %s > to %s", date_from_dt, date_to_dt)
        raise ValueError(f"Invalid date range: start date {date_from} is after end date {date_to}.")

    # Filter by date range
    mask = (df['Date'] >= date_from_dt) & (df['Date'] <= date_to_dt)
    df_filtered = df.loc[mask].copy()
    logger.info("filter result rows=%d range=%s..%s symbol=%s",
                len(df_filtered),
                date_from_dt.strftime('%Y-%m-%d'),
                date_to_dt.strftime('%Y-%m-%d'),
                symbol)
    
    if df_filtered.empty:
        data_min = df['Date'].min().strftime('%Y-%m-%d') if not df.empty else 'N/A'
        data_max = df['Date'].max().strftime('%Y-%m-%d') if not df.empty else 'N/A'
        raise ValueError(
            f"No price data for {symbol} between {date_from} and {date_to}. "
            f"Available data spans {data_min} to {data_max}."
        )

    # Ensure data is sorted by date
    df_filtered = df_filtered.sort_values('Date')

    # Check for and handle NaN values in price data
    nan_count = df_filtered[symbol].isna().sum()
    if nan_count:
        logger.warning("%d missing values for %s; interpolating", nan_count, symbol)
        df_filtered[symbol] = df_filtered[symbol].interpolate(method='linear')

    # Convert prices to numeric explicitly
    try:
        df_filtered[symbol] = pd.to_numeric(df_filtered[symbol], errors='coerce')
        bad = df_filtered[symbol].isna().sum()
        if bad:
            logger.warning("%d non-numeric price values for %s; dropping", bad, symbol)
            df_filtered = df_filtered.dropna(subset=[symbol])
    except Exception as e:
        logger.exception("price->numeric conversion failed")
        raise ValueError(f"Could not convert prices to numeric: {e}")

    if df_filtered.empty:
        logger.error("no valid data remaining after cleaning for %s", symbol)
        raise ValueError(f"No valid price data for {symbol} after cleaning the {date_from}..{date_to} window.")

    dates = df_filtered['Date'].tolist()
    prices = df_filtered[symbol].tolist()

    logger.info("plot input prepared symbol=%s points=%d span=%s..%s",
                symbol, len(dates),
                dates[0].strftime('%Y-%m-%d'),
                dates[-1].strftime('%Y-%m-%d'))

    # Generate hover texts with date, price, and news headlines
    hover_texts = []

    for date, price in zip(dates, prices):
        # Convert date to the format required by the `fetch_news_headline` function
        formatted_date = date.strftime('%d-%m-%Y')  

        # Try to fetch news headlines - use a try/except block to handle the function not existing
        try:
            # When calling fetch_news_headline, we're now using a properly formatted date string
            # No need to parse the date inside that function again
            headlines = fetch_news_headline(formatted_date, symbol)
        except NameError:
            # fetch_news_headline isn't defined in this environment; degrade gracefully
            headlines = []
        except Exception as e:
            logger.warning("news lookup failed date=%s symbol=%s err=%s",
                           formatted_date, symbol, e)
            headlines = []

        # Join multiple headlines with line breaks
        news_text = "<br>".join(headlines) if headlines else "No news available"

        hover_text = (
            f"<b>Date:</b> {date.strftime('%d-%m-%Y')}<br>"
            f"<b>Price:</b> {price:.2f}<br>"
            f"<b>News:</b> {news_text}"
        )
        hover_texts.append(hover_text)

    # Create Plotly chart
    fig = go.Figure()

    # Stock price line with hover text
    fig.add_trace(go.Scatter(
        x=dates,
        y=prices,
        mode='lines+markers',
        name=f"{symbol} Close",
        hovertext=hover_texts,
        hoverinfo='text',
        line=dict(width=2, color='blue'),
    ))

    # Only add trendline if we have enough data points
    if len(prices) > 1:
        # Create x values for polyfit as indices
        x_indices = np.arange(len(prices))
        # Calculate trendline
        z = np.polyfit(x_indices, prices, deg=1)
        trendline = np.polyval(z, x_indices)
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=trendline,
            mode='lines',
            name="Trendline",
            line=dict(dash='dash', color='orange', width=1.5),
            hoverinfo='skip'
        ))

    # Layout adjustments
    fig.update_layout(
        title=f"{symbol} Stock Price with News ({date_from} to {date_to})",
        xaxis_title="Date",
        yaxis_title="Closing Price",
        hovermode="x unified",
        margin=dict(l=50, r=20, t=50, b=50),
        autosize=True,
        height=450,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        template="plotly_white"
    )

    # Calculate date range for dynamic tick formatting
    date_range = date_to_dt - date_from_dt
    
    # Determine tick interval dynamically
    if date_range <= timedelta(days=30):
        tick_format = "%b %d\n%Y"  # Daily format
        n_ticks = min(len(dates), 15)  # Limit number of ticks for readability
    elif date_range <= timedelta(days=180):
        tick_format = "%b %d\n%Y"  # Weekly format
        n_ticks = min(len(dates), 10)
    else:
        tick_format = "%b\n%Y"     # Monthly format
        n_ticks = min(len(dates), 8)

    # Apply dynamic tick spacing
    fig.update_xaxes(
        type="date",
        tickformat=tick_format,
        tickangle=-45,
        showgrid=True,
        nticks=n_ticks
    )
    
    # Update y-axis to match price range with a bit of padding
    if prices:
        min_price = min(prices)
        max_price = max(prices)
        price_range = max_price - min_price
        padding = price_range * 0.05  # 5% padding
        
        fig.update_yaxes(
            range=[min_price - padding, max_price + padding]
        )

    # Save the chart to the specified path
    try:
        os.makedirs(os.path.dirname(chart_path), exist_ok=True)
        fig.write_html(chart_path, include_plotlyjs=True, full_html=True)

        if os.path.exists(chart_path):
            file_size = os.path.getsize(chart_path)
            logger.info("chart written path=%s bytes=%d", chart_path, file_size)
            return True
        logger.error("chart file missing after write: %s", chart_path)
        return False
    except Exception as e:
        logger.exception("error writing chart to %s", chart_path)
        raise ValueError(f"Could not save chart: {e}")
    
    
    
def news_sentiment(csv_path, ticker):
    """
    Extract the news headline and hyperlink for a specific ticker from the dataset It is for Sentiment Analysis Section.
    
    Parameters:
    csv_path (str): Path to the CSV file containing news data.
    ticker (str): Ticker symbol to filter news for.
    
    Returns:
    dict: Dictionary containing the news headline and link, or an empty dictionary if not found.
    """
    try:
        # Read the CSV file
        encoding = detect_encoding(csv_path)
        df = pd.read_csv(csv_path, encoding=encoding)        
        # Ensure the dataset contains the required columns
        if 'TICKER' not in df.columns or 'NEWS' not in df.columns or 'LINK' not in df.columns:
            print("Missing required columns in CSV file.")
            return {}

        # Filter by ticker (case-insensitive)
        ticker = ticker.upper()
        ticker_row = df[df['TICKER'].str.upper() == ticker].head(1)  # Fetch only the first match

        if ticker_row.empty:
            print(f"No news found for ticker: {ticker}")
            return {}

        # Extract the first news item
        news_headline = ticker_row['NEWS'].values[0]
        news_link = ticker_row['LINK'].values[0]

        return news_headline, news_link

    except Exception as e:
        print(f"Error processing CSV file: {e}")
        return {}
    
    


def create_sentiment_gauge(ticker, gauge_value):
    """
    Create a sentiment gauge using Plotly.
    
    Args:
        ticker (str): The ticker symbol
        gauge_value (int): The gauge value (0-100)
        
    Returns:
        str: HTML for the gauge
    """
    logger.debug("gauge: starting generation ticker=%s value=%s", ticker, gauge_value)

    try:
        # Validate gauge value
        if gauge_value is None:
            gauge_value = 50  # Default to neutral

        # Ensure gauge value is within range
        gauge_value = max(0, min(100, gauge_value))

        # Create a unique ID for this gauge
        gauge_id = f"gauge-{ticker.lower()}-{int(time.time())}"
        logger.debug("gauge: gauge_id=%s", gauge_id)

        # Render a single Plotly gauge into a self-sizing container. The earlier
        # version emitted a CSS-bar fallback above the gauge and stacked them in a
        # fixed-height box, which made the gauge overflow its card; it also embedded
        # a literal "</script>" substring inside a JS comment, which prematurely
        # terminated the <script> element and leaked the trailing JS as visible text.
        # Both issues are fixed here.
        fn_name = "createGauge_" + gauge_id.replace('-', '_')
        wrapped_html = f'''
        <div id="{gauge_id}-container" class="gauge-container" style="width:100%; min-height:280px; position:relative;">
            <div id="{gauge_id}" style="width:100%; height:280px;"></div>
            <div id="{gauge_id}-fallback" style="display:none; text-align:center; padding:20px; color:#a00;">
                Plotly library not loaded — cannot render gauge.
            </div>
            <script>
                (function() {{
                    function {fn_name}() {{
                        if (typeof Plotly === 'undefined') {{
                            var f = document.getElementById('{gauge_id}-fallback');
                            if (f) f.style.display = 'block';
                            return;
                        }}
                        // No in-gauge "title" — the surrounding card already shows
                        // "Sentiment Gauge for <ticker>" as an h2; an internal title
                        // shifts Plotly's value text off-center to make room for it.
                        var data = [{{
                            type: "indicator",
                            mode: "gauge+number",
                            value: {gauge_value},
                            number: {{ font: {{ size: 40 }}, valueformat: "d" }},
                            gauge: {{
                                shape: "angular",
                                axis: {{ range: [0, 100], tickwidth: 1, tickcolor: "#444" }},
                                bar: {{ color: "#333" }},
                                steps: [
                                    {{ range: [0, 30], color: "#ff6b6b" }},
                                    {{ range: [30, 70], color: "#ffe066" }},
                                    {{ range: [70, 100], color: "#69db7c" }}
                                ],
                                threshold: {{
                                    line: {{ color: "black", width: 4 }},
                                    thickness: 0.75,
                                    value: {gauge_value}
                                }}
                            }},
                            domain: {{ x: [0, 1], y: [0, 1] }}
                        }}];
                        var layout = {{
                            autosize: true,
                            height: 280,
                            margin: {{ l: 30, r: 30, t: 20, b: 20 }},
                            paper_bgcolor: "white",
                            font: {{ size: 12 }}
                        }};
                        try {{
                            Plotly.newPlot('{gauge_id}', data, layout, {{
                                displayModeBar: false,
                                responsive: true
                            }});
                        }} catch (e) {{
                            console.error('Error creating gauge {gauge_id}:', e);
                        }}
                    }}
                    if (document.readyState === 'loading') {{
                        document.addEventListener('DOMContentLoaded', {fn_name});
                    }} else {{
                        {fn_name}();
                    }}
                    window.addEventListener('load', function() {{
                        if (typeof Plotly !== 'undefined') {{
                            try {{ Plotly.relayout('{gauge_id}', {{}}); }} catch (e) {{}}
                        }}
                    }});
                }})();
            </script>
        </div>
        '''
        
        logger.info("gauge: generated for %s value=%d", ticker, gauge_value)
        return wrapped_html

    except Exception:
        logger.exception("gauge: generation failed for %s", ticker)
        
        # Return a fallback visualization
        return f'''
        <div class="alert alert-warning">
            <p>Unable to generate gauge visualization for {ticker}.</p>
            <p style="color:red;">Error: {str(e)}</p>
        </div>
        '''
    
    
    
    

def analyze_sentiment(csv_path, ticker):
    """
    It is for Secntiment Analysis Section.
    Reads the CSV dataset, filters for the given ticker, computes the sentiment gauge value,
    generates a Plotly gauge chart and a Matplotlib word cloud, and returns both as in-memory objects.
    
    Returns:
        gauge_html (str): HTML representation of the Plotly gauge chart.
        wordcloud_base64 (str): Base64 string of the word cloud image, suitable for embedding.
    """
    try:
        
        # Load dataset and filter by ticker
        print(f"Loading CSV from {csv_path} for ticker {ticker}")
        
        # Load dataset and filter by ticker
        df = pd.read_csv(csv_path, encoding='cp1252', skipinitialspace=True)
        print(f"CSV loaded successfully, shape: {df.shape}")
        
        # Print available tickers for debugging
        if 'TICKER' in df.columns:
            available_tickers = df['TICKER'].unique()
            print(f"Available tickers in CSV: {available_tickers}")
        
        df = df[['TICKER', 'NEWS']]
        df_filtered = df[df['TICKER'].str.upper() == ticker.upper()]
        
        print(f"Filtered data for {ticker}: {len(df_filtered)} rows")
        
        if df_filtered.empty:
            print(f"No data found for ticker {ticker}")
            return None, None  # No data for this ticker
        
        # Concatenate news articles into one text
        news_text = " ".join(df_filtered["NEWS"].astype(str).tolist())
        
        # Split text into items and calculate compound scores using VADER
        news_items = news_text.split(".")
        compound_scores = [analyzer.polarity_scores(item.strip())["compound"] 
                        for item in news_items if item.strip()]
        
        # Calculate average compound score and map it to a 0-100 gauge value
        if compound_scores:
            avg_compound = np.mean(compound_scores)
            gauge_value = int(((avg_compound + 1) / 2) * 100)
        else:
            gauge_value = 50  # Neutral fallback
        
        # Use the improved gauge creation function
        gauge_html = create_sentiment_gauge(ticker, gauge_value)
        
        # Word cloud generation with proper error handling
        wordcloud_base64 = None
        try:
        
            # Prepare text for word cloud: remove stopwords and the ticker itself
            banned_words = {ticker.lower(), "shares", "stocks", "company", "stock"}  # Banned words in lowercase
            # Clean the text
            words = [word for word in news_text.lower().split() if word.isalpha() 
                    and word not in combined_stopwords and word.lower() not in banned_words]

            cleaned_text = " ".join(words)
            
            if cleaned_text.strip():
                # Generate the word cloud image
                wc = WordCloud(width=800, height=400, background_color="white", colormap="viridis").generate(cleaned_text)
                # Save image to an in-memory bytes buffer
                img_buffer = io.BytesIO()
                plt.figure(figsize=(10, 5))
                plt.imshow(wc, interpolation="bilinear")
                plt.axis("off")
                plt.tight_layout(pad=0)
                plt.savefig(img_buffer, format="png")
                plt.close()  # Close the figure to free memory
                img_buffer.seek(0)
                # Encode image to base64 for direct embedding 
                wordcloud_base64 = base64.b64encode(img_buffer.getvalue()).decode("utf8")
        except Exception as e:
            print(f"Error generating word cloud: {str(e)}")
            # Continue without word cloud

        return gauge_html, wordcloud_base64
    
    except Exception as e:
        print(f"Error in analyze_sentiment: {str(e)}")
        traceback.print_exc()
        # Return empty values that won't break the template
        return None, None

    
    
    


# -----------------------------------------------------------------------------
# Shared sentiment + word-cloud helpers (used by the Sentiment tab AND the new
# One-Page-Report tab).
# -----------------------------------------------------------------------------

# Words to exclude from word clouds — generic financial filler, common verbs of
# attribution, and the ticker universe itself. None of these tell the reader
# anything about *what* the news said; keeping them just adds noise.
_KNOWN_TICKERS = {'AAPL', 'AMD', 'EBAY', 'HPQ', 'IBM', 'JNPR', 'MSFT', 'QCOM'}
_FINANCIAL_FILLER = {
    # generic finance/business words that carry no sentiment
    "stock", "stocks", "share", "shares", "shareholder", "shareholders",
    "company", "companies", "corp", "corporation", "inc", "ltd",
    "market", "markets", "price", "prices", "trading", "trade", "trader",
    "investor", "investors", "investment", "investments",
    "quarter", "quarterly", "year", "yearly", "annual", "fiscal",
    "earnings", "revenue", "revenues",  # neutral magnitudes
    "report", "reported", "reports", "reporting",
    "said", "says", "according", "stated", "told", "noted",
    "ceo", "cfo", "executive", "executives",
    "billion", "million", "thousand", "percent", "percentage",
    "today", "yesterday", "tomorrow", "week", "weeks", "month", "months",
    "monday", "tuesday", "wednesday", "thursday", "friday",
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
    "yahoo", "finance", "news", "nasdaq", "nyse",
}


def _build_impactful_wordcloud_base64(news_text: str, ticker: str) -> str:
    """Build a word-cloud image (base64 PNG) keeping only impactful, sentiment-bearing
    words. Stopwords, ticker symbols, generic financial filler, and short tokens are
    removed; the remaining words are preferentially restricted to VADER's sentiment
    lexicon so the cloud actually reflects emotional tone of the news.
    Returns None if no usable words remain or rendering fails.
    """
    if not news_text or not news_text.strip():
        return None

    try:
        import re

        banned = (
            combined_stopwords
            | _FINANCIAL_FILLER
            | {t.lower() for t in _KNOWN_TICKERS}
            | {ticker.lower(), ticker.upper()}
        )

        tokens = re.findall(r"[a-z']{4,}", news_text.lower())
        candidates = [w for w in tokens if w not in banned]

        sentiment_words = [w for w in candidates if w in analyzer.lexicon]
        chosen = sentiment_words if len(sentiment_words) >= 8 else candidates
        cleaned_text = " ".join(chosen)
        if not cleaned_text.strip():
            logger.info("wordcloud: no impactful words remained after filtering")
            return None

        wc = WordCloud(
            width=800, height=400,
            background_color="white", colormap="viridis",
            collocations=False,
        ).generate(cleaned_text)

        img_buffer = io.BytesIO()
        plt.figure(figsize=(10, 5))
        plt.imshow(wc, interpolation="bilinear")
        plt.axis("off")
        plt.tight_layout(pad=0)
        plt.savefig(img_buffer, format="png")
        plt.close()
        img_buffer.seek(0)
        return base64.b64encode(img_buffer.getvalue()).decode("utf8")
    except Exception:
        logger.exception("impactful wordcloud generation failed")
        return None


def score_news_sentiment_with_claude(news_text: str, ticker: str) -> int:
    """Score the news text using Claude Haiku 4.5 (lowest-cost, fastest tier).
    Returns a sentiment score as an integer in [0, 100], where 0 = very negative,
    50 = neutral, 100 = very positive. Falls back to VADER if the API call fails
    or no key is configured (VADER's [-1,+1] compound is mapped to [0,100]).
    """
    def _vader_fallback(text):
        compound = float(analyzer.polarity_scores(text)["compound"])
        return int(round(((compound + 1.0) / 2.0) * 100))

    if not news_text or not news_text.strip():
        return 50

    # Cap input to keep cost bounded — ~40K chars is roughly 10K tokens.
    text = news_text[:40000]

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not set; falling back to VADER for %s", ticker)
        return _vader_fallback(text)

    try:
        import anthropic
    except ImportError:
        logger.error("anthropic SDK not installed; falling back to VADER")
        return _vader_fallback(text)

    # NB: structured outputs don't support `minimum`/`maximum` on numeric types —
    # the API rejects them with a 400. Range is conveyed in the description and
    # the system prompt; the value is post-clamped to [0, 100] below.
    schema = {
        "type": "object",
        "properties": {
            "score": {
                "type": "integer",
                "description": "Sentiment score in the inclusive range 0..100. 0 = very negative for the company, 50 = neutral, 100 = very positive.",
            },
            "label": {
                "type": "string",
                "enum": ["very negative", "negative", "neutral", "positive", "very positive"],
            },
            "rationale": {"type": "string"},
        },
        "required": ["score", "label", "rationale"],
        "additionalProperties": False,
    }

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=512,
            system=(
                "You are a financial-news sentiment analyzer. Given news text about a "
                "publicly traded company, return a single sentiment score in [0, 100] "
                "reflecting the tone with respect to the company's prospects: 0 is very "
                "negative for the company, 50 is neutral, 100 is very positive. "
                "Calibrate roughly: 0-30 negative, 30-70 neutral/mixed, 70-100 positive. "
                "Consider the aggregate tone across all snippets provided."
            ),
            messages=[{"role": "user", "content": f"Ticker: {ticker}\n\nNews snippets:\n{text}"}],
            output_config={"format": {"type": "json_schema", "schema": schema}},
        )
        for block in response.content:
            if block.type == "text":
                data = json.loads(block.text)
                raw = data.get("score", 50)
                score = int(round(float(raw)))
                score = max(0, min(100, score))
                logger.info("Claude sentiment for %s: score=%d/100 label=%s",
                            ticker, score, data.get("label"))
                return score
        logger.warning("Claude returned no text block for %s; falling back to VADER", ticker)
        return _vader_fallback(text)
    except Exception:
        logger.exception("Claude sentiment scoring failed for %s; falling back to VADER", ticker)
        return _vader_fallback(text)


def generate_one_page_report_visuals(ticker, news_csv_path, date_from, date_to):
    """Read the per-ticker news CSV, filter to [date_from, date_to], score the
    aggregate sentiment using Claude Haiku 4.5, and build a gauge + impactful-words
    word cloud. Returns (gauge_html, wordcloud_base64, score, news_count).
    Raises ValueError on missing data.
    """
    if not os.path.exists(news_csv_path):
        raise ValueError(f"No news data file for {ticker}")

    encoding = detect_encoding(news_csv_path)
    df = pd.read_csv(news_csv_path, encoding=encoding)
    if 'Date' not in df.columns or 'NEWS' not in df.columns:
        raise ValueError("News CSV is missing the Date or NEWS column.")

    df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['Date'])

    try:
        date_from_dt = pd.to_datetime(date_from, format='%Y-%m-%d')
        date_to_dt = pd.to_datetime(date_to, format='%Y-%m-%d')
    except (ValueError, TypeError):
        date_from_dt = pd.to_datetime(date_from, dayfirst=True)
        date_to_dt = pd.to_datetime(date_to, dayfirst=True)

    mask = (df['Date'] >= date_from_dt) & (df['Date'] <= date_to_dt)
    df_filt = df.loc[mask].copy()
    df_filt = df_filt[df_filt['NEWS'].astype(str).str.strip().astype(bool)]
    if df_filt.empty:
        raise ValueError(
            f"No news headlines for {ticker} between {date_from} and {date_to}."
        )

    combined_text = "\n".join(df_filt['NEWS'].astype(str).tolist())
    logger.info("one-page report: ticker=%s news_rows=%d chars=%d range=%s..%s",
                ticker, len(df_filt), len(combined_text), date_from, date_to)

    # Claude returns a 0..100 score directly — feed it straight to the gauge.
    score = score_news_sentiment_with_claude(combined_text, ticker)
    gauge_html = create_sentiment_gauge(ticker, score)
    wordcloud_base64 = _build_impactful_wordcloud_base64(combined_text, ticker)
    return gauge_html, wordcloud_base64, score, len(df_filt)


def generate_sentiment_visuals(ticker: str, news_text: str) -> Tuple[str, str]:
    """
    Generates a sentiment gauge (Plotly) and a word cloud (base64 PNG) from the
    provided news text. Used by the existing Sentiment tab (single-article path).
    The word cloud now filters to impactful, sentiment-bearing words (shared
    helper); the gauge still uses VADER here so the existing tab's behavior is
    preserved.
    """
    try:
        news_items = [item for item in news_text.split('\n') if item.strip()]
        if not news_items:
            news_items = [item.strip() for item in news_text.split('.') if item.strip()]

        compound_scores = [analyzer.polarity_scores(item)["compound"]
                           for item in news_items if item.strip()]
        if compound_scores:
            avg_compound = np.mean(compound_scores)
            gauge_value = int(((avg_compound + 1) / 2) * 100)
        else:
            gauge_value = 50

        gauge_html = create_sentiment_gauge(ticker, gauge_value)
        wordcloud_base64 = _build_impactful_wordcloud_base64(news_text, ticker)
        return gauge_html, wordcloud_base64

    except Exception:
        logger.exception("generate_sentiment_visuals failed")
        return None, None
    
    
    
def extract_news(symbol: str) -> dict:
    """
    This function for sentiment analysis news section.
    Fetches and parses news data for the given stock symbol.
    Args:
        symbol (str): The stock symbol to search for (e.g., "AMD").
    Returns:
        dict: A dictionary containing the symbol, title, news text, and source URL,
              or an error message if something went wrong.
    """
    try:
        base_url = "https://stockanalysis.com/stocks/"
        search_url = f"{base_url}{symbol}/"

        response = requests.get(search_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        # Extract the page title (if available)
        title_tag = soup.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else "No title found"

        # Attempt to locate a container with news; if not found, fallback to all <p> tags.
        news_container = soup.find("div", class_="news-content")
        if news_container:
            paragraphs = news_container.find_all("p")
        else:
            paragraphs = soup.find_all("p")

        news_text = " ".join(p.get_text(strip=True) for p in paragraphs)

        return {
            "symbol": symbol,
            "title": title,
            "news_text": news_text,
            "source_url": search_url
        }
    except Exception as e:
        return {
            "symbol": symbol,
            "error": str(e)
        }
