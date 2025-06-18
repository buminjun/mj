import os
import requests
import yfinance as yf
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
from io import BytesIO
from datetime import datetime, timedelta
from PIL import Image
import nltk

BOT_TOKEN = "7088690019:AAElXpIK04OXWYlEIOEBBbRgoupAH2Zx5V0"
CHAT_ID = "953083803"
DEEPL_API_KEY = "69f88b38-1996-47ec-ad67-e0b0c9072749:fx" 

tickers = {
    "아이온큐": "IONQ",
    "엔비디아": "NVDA",
    "애플": "AAPL",
    "마이크로소프트": "MSFT",
    "AMD": "AMD",
    "테슬라": "TSLA",
    "팔란티어": "PLTR",
    "유나이티드헬스그룹": "UNH",
    "루시드": "LCID",
    "리비안": "RIVN",
    "DECK": "DECK"
}

# 간단한 감성 단어 사전
positive_words = ["soar", "rise", "beat", "profit", "record", "growth", "upgrade"]
negative_words = ["fall", "drop", "loss", "warn", "cut", "down", "plunge"]

def get_sentiment(text):
    text = text.lower()
    if any(word in text for word in positive_words):
        return "😀 긍정"
    elif any(word in text for word in negative_words):
        return "😞 부정"
    else:
        return "😐 중립"

def translate_deepl(text):
    try:
        url = "https://api-free.deepl.com/v2/translate"
        data = {
            "auth_key": DEEPL_API_KEY,
            "text": text,
            "target_lang": "KO"
        }
        res = requests.post(url, data=data)
        return res.json()["translations"][0]["text"]
    except:
        return text

def get_news(symbol):
    rss_url = f"https://news.google.com/rss/search?q={symbol}+stock"
    res = requests.get(rss_url, timeout=5)
    root = ET.fromstring(res.content)
    items = root.findall(".//item")[:3]
    news_list = []
    for item in items:
        title = item.find("title").text
        link = item.find("link").text
        translated = translate_deepl(title)
        sentiment = get_sentiment(title)
        news_list.append(f"{sentiment} {translated}\n🔗 [원문 보기]({link})")
    return "\n\n".join(news_list) if news_list else "💬 관련 뉴스 없음"

def create_chart(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="7d")
        if hist.empty:
            return None

        plt.figure(figsize=(6, 3))
        plt.plot(hist.index, hist["Close"], marker="o")
        plt.title(f"{ticker} 최근 주가")
        plt.xlabel("날짜")
        plt.ylabel("종가")
        plt.grid(True)
        plt.tight_layout()

        buf = BytesIO()
        plt.savefig(buf, format="PNG")
        plt.close()
        buf.seek(0)
        return buf
    except:
        return None

def send_telegram_text(message):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": False
        }
    )

def send_telegram_photo(image_buf, caption=""):
    files = {'photo': ('chart.png', image_buf)}
    data = {'chat_id': CHAT_ID, 'caption': caption}
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
        files=files,
        data=data
    )

def job():
    today = datetime.now().strftime("%Y-%m-%d")
    send_telegram_text(f"📈 오늘의 주식 뉴스 ({today})")

    for name, symbol in tickers.items():
        try:
            stock = yf.Ticker(symbol)
            price = stock.history(period="1d")["Close"][0]

            chart_buf = create_chart(symbol)
            news_summary = get_news(symbol)

            caption = (
                f"🔹 {name} ({symbol})\n"
                f"- 종가: ${price:.2f}\n\n"
                f"{news_summary}"
            )

            if chart_buf:
                send_telegram_photo(chart_buf, caption=caption)
            else:
                send_telegram_text(caption)

        except Exception as e:
            send_telegram_text(f"🔹 {name} ({symbol}) - 오류 발생: {str(e)}")

job()
