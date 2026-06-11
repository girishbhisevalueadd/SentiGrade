from flask import Flask, render_template, request, send_from_directory, url_for, jsonify, session
import os
from market_sentiment import analyze_sentiment, create_stock_chart, get_recent_news, news_sentiment, extract_news, generate_sentiment_visuals

app = Flask(__name__)
app.static_folder = 'static'

# Specify your CSV dataset path here
CSV_PATH = r"C:\Users\VivekPol\OneDrive - ValueAdd Research and Analytics Solutions LLP\Desktop\Project\Vivek Project\Sentigrade_News_Analysis\Demo4\yahooData\testPairsTrading_news.csv"

# Mapping of ticker symbols to their respective CSV file paths
TICKER_CSV_MAP = {
    'AMD': r"C:\Users\VivekPol\OneDrive - ValueAdd Research and Analytics Solutions LLP\Desktop\Project\Vivek Project\Sentigrade_News_Analysis\Demo4\yahooData\AMD_news.csv",
    'AAPL': r"C:\Users\VivekPol\OneDrive - ValueAdd Research and Analytics Solutions LLP\Desktop\Project\Vivek Project\Sentigrade_News_Analysis\Demo4\yahooData\AAPL_news.csv",
    'EBAY': r"C:\Users\VivekPol\OneDrive - ValueAdd Research and Analytics Solutions LLP\Desktop\Project\Vivek Project\Sentigrade_News_Analysis\Demo4\yahooData\EBAY_news.csv",
    'HPQ': r"C:\Users\VivekPol\OneDrive - ValueAdd Research and Analytics Solutions LLP\Desktop\Project\Vivek Project\Sentigrade_News_Analysis\Demo4\yahooData\HPQ_news.csv",
    'IBM': r"C:\Users\VivekPol\OneDrive - ValueAdd Research and Analytics Solutions LLP\Desktop\Project\Vivek Project\Sentigrade_News_Analysis\Demo4\yahooData\IBM_news.csv",
    'JNPR': r"C:\Users\VivekPol\OneDrive - ValueAdd Research and Analytics Solutions LLP\Desktop\Project\Vivek Project\Sentigrade_News_Analysis\Demo4\yahooData\JNPR_news.csv",
    'MSFT': r"C:\Users\VivekPol\OneDrive - ValueAdd Research and Analytics Solutions LLP\Desktop\Project\Vivek Project\Sentigrade_News_Analysis\Demo4\yahooData\MSFT_news.csv",
    'QCOM': r"C:\Users\VivekPol\OneDrive - ValueAdd Research and Analytics Solutions LLP\Desktop\Project\Vivek Project\Sentigrade_News_Analysis\Demo4\yahooData\QCOM_news.csv",
    # Add more mappings as needed
}
 
# Update these routes in your app.py file

# Update these routes in your app.py file to handle AJAX requests correctly

@app.route('/', methods=['GET', 'POST'])
def home():
    """
    Home route that handles the Company sentiment analysis section.
    """
    ticker = None
    gauge_html = None
    wordcloud_base64 = None
    news_headline = None
    news_link = None
 
    if request.method == 'POST':
        ticker = request.form.get('ticker', '').upper()
        if ticker:
            try:
                # Call our sentiment analysis function 
                gauge_html, wordcloud_base64 = analyze_sentiment(CSV_PATH, ticker)
                
                # Debug to ensure gauge_html has content
                print(f"DEBUG HOME ROUTE: gauge_html type: {type(gauge_html)}")
                print(f"DEBUG HOME ROUTE: gauge_html length: {len(gauge_html) if gauge_html else 0}")
                
                # Get news items for the ticker
                news_result = news_sentiment(CSV_PATH, ticker)
                if news_result:
                    news_headline, news_link = news_result
                
                # Log success for debugging
                print(f"Successfully processed company sentiment for {ticker}")
            except Exception as e:
                print(f"Error processing company sentiment: {str(e)}")
                # In case of error, still return partial results
                pass
                
    # Check if this is an AJAX request
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if is_ajax:
        print(f"Responding to AJAX request for ticker: {ticker}")
    
    # Return the complete template
    return render_template('index.html',  
                          gauge_html=gauge_html,  
                          wordcloud_base64=wordcloud_base64,  
                          ticker=ticker,
                          news_headline=news_headline,
                          news_link=news_link)

@app.route('/extract_news', methods=['GET', 'POST'])
def extract_news_route():
    """
    Route for news extraction that also generates sentiment visuals.
    """
    news_ticker = None
    news_data = None
    news_gauge_html = None
    news_wordcloud_base64 = None
    news_headline = None
    news_link = None
    news_text = None

    if request.method == 'POST':
        news_ticker = request.form.get('symbol', '').upper()
        if news_ticker:
            try:
                print(f"Processing news sentiment for {news_ticker}")
                news_data = extract_news(news_ticker)
                # If news extraction was successful and news_text exists
                if news_data and "news_text" in news_data and not news_data.get("error"):
                    news_gauge_html, news_wordcloud_base64 = generate_sentiment_visuals(news_ticker, news_data["news_text"])
                    news_text = news_data["news_text"]
                    print(f"Generated news sentiment visuals for {news_ticker}")
                # For the news section, we use the title as headline and source_url as link
                if news_data and "title" in news_data and "source_url" in news_data:
                    news_headline = news_data["title"]
                    news_link = news_data["source_url"]
            except Exception as e:
                print(f"Error processing news sentiment: {str(e)}")
                # In case of error, still return partial results
                pass
        else:
            news_data = {'error': 'Ticker symbol is required.'}
    
    # Check if this is an AJAX request  
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if is_ajax:
        print(f"Responding to AJAX request for news ticker: {news_ticker}")
    
    # Return the complete template
    return render_template('index.html',
                          news_ticker=news_ticker,
                          news_data=news_data,
                          news_gauge_html=news_gauge_html,
                          news_wordcloud_base64=news_wordcloud_base64,
                          news_headline=news_headline,
                          news_link=news_link,
                          news_text=news_text)

    
@app.route("/stockchart", methods=['GET', 'POST'])
def stockchart():
    if request.method == 'POST':
        ticker = request.form.get('ticker')
        date_from = request.form.get('date_from')
        date_to = request.form.get('date_to')

        if not ticker or not date_from or not date_to:
            return jsonify({'success': False, 'error': 'Missing required parameters'}), 400

        # Ensure the static folder exists
        if not os.path.exists(app.static_folder):
            try:
                os.makedirs(app.static_folder)
                print(f"Created static folder: {app.static_folder}")
            except Exception as e:
                return jsonify({'success': False, 'error': f'Cannot create static folder: {str(e)}'}), 500

        # Create a clean filename (remove special characters)
        clean_ticker = ''.join(c for c in ticker if c.isalnum())
        chart_filename = f"{clean_ticker}_{date_from}_{date_to}.html"
        chart_path = os.path.join(app.static_folder, chart_filename)
        
        print(f"Preparing to generate chart for {ticker} from {date_from} to {date_to}")
        print(f"Chart will be saved to: {chart_path}")

        try:
            # Call the chart generation function
            success = create_stock_chart(ticker, date_from, date_to, chart_path)
            
            if not success:
                return jsonify({'success': False, 'error': 'Error generating chart'}), 500
            
            # Verify the file exists after generation
            if not os.path.exists(chart_path):
                return jsonify({'success': False, 'error': 'Chart file was not created'}), 500
                
            # Return file information and success
            file_size = os.path.getsize(chart_path)
            print(f"Chart successfully created: {chart_path}, size: {file_size} bytes")
            
            # Return JSON response with chart filename
            return jsonify({
                'success': True, 
                'chart_filename': chart_filename,
                'file_size': file_size
            }), 200

        except Exception as e:
            print(f"Error generating chart: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    return render_template('index.html')

@app.route('/recent_news', methods=['POST'])
def recent_news():
    """Fetches recent news based on the ticker and date range."""
    ticker = request.form.get('ticker', '').upper()
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')

    if not ticker or not start_date or not end_date:
        return render_template('index.html', error="Ticker, start date, and end date are required")

    csv_path = TICKER_CSV_MAP.get(ticker)
    
    if not csv_path or not os.path.exists(csv_path):
        return render_template('index.html', error=f"No data available for ticker symbol: {ticker}")

    recent_news_items = get_recent_news(csv_path, start_date, end_date)

    if not recent_news_items:
        return render_template('index.html', error=f"No recent news found for ticker symbol: {ticker}")

    # Return the results with the ticker symbol
    return render_template('index.html', ticker=ticker, recent_news=recent_news_items)
    


@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)



if __name__ == '__main__':
    # Ensure the static directory exists
    os.makedirs('static', exist_ok=True)
    app.run(debug=True)
