import pandas as pd
import chardet
import numpy as np

def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']

CSV_PATH_AMD = r"C:\Users\VivekPol\OneDrive - ValueAdd Research and Analytics Solutions LLP\Desktop\Project\Vivek Project\Sentigrade_News_Analysis\Demo4\yahooData\AMD_news.csv"

def get_recent_news(csv_path):
    try:
        encoding = detect_encoding(csv_path)
        df = pd.read_csv(csv_path, encoding=encoding)
        df.replace(np.nan, '', inplace=True)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])
        df = df.sort_values(by='Date', ascending=False)
        recent_news = df[['Date', 'NEWS', 'LINK']].head(10).to_dict(orient='records')
        return recent_news
    except Exception as e:
        print(f"Error processing CSV file: {e}")
        return []
