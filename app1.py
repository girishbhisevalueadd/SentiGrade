from flask import Flask, render_template
from main import get_recent_news, CSV_PATH_AMD

app = Flask(__name__)


@app.route('/')
def display_news():
    recent_news = get_recent_news(CSV_PATH_AMD)
    return render_template('news.html', news_data=recent_news)

if __name__ == '__main__':
    app.run(debug=True)
