import requests
from datetime import datetime
import yfinance as yf
import xml.etree.ElementTree as ET
import os

BOT_TOKEN = "7088690019:AAEhoGxvJ7JehXatg6aCyBtU8cALi7vvFuQ"
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

def translate_deepl(text):
    try:
        url = "https://api-free.deepl.com/v2/translate"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "auth_key": DEEPL_API_KEY,
            "text": text,
            "target_lang": "KO"
        }
        res = requests.post(url, headers=headers, data=data)
        result = res.json()
        return result["translations"][0]["text"]
    except:
        return text  # 번역 실패 시 원문 그대로 출력

def get_news_summary(symbol):
    try:
        rss_url = f"https://news.google.com/rss/search?q={symbol}+stock"
        res = requests.get(rss_url, timeout=5)
        root = ET.fromstring(res.content)
        item = root.find(".//item")
        if item is not None:
            title = item.find("title").text
            link = item.find("link").text
            translated_title = translate_deepl(title)
            return f'💬 {translated_title}\n🔗 [원문 보기]({link})'
    except:
        return "💬 뉴스 가져오기 오류"
    return "💬 관련 뉴스 없음"

def send_telegram(message):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": False
        }
    )

def job():
    today = datetime.now().strftime("%Y-%m-%d")
    full_message = f"📈 오늘의 주식 뉴스 ({today})\n\n"

    for name, symbol in tickers.items():
        try:
            stock = yf.Ticker(symbol)
            price = stock.history(period="1d")["Close"][0]
            news = get_news_summary(symbol)
            full_message += (
                f"🔹 {name} ({symbol})\n"
                f"- 종가: ${price:.2f}\n"
                f"{news}\n\n"
            )
        except Exception as e:
            full_message += f"🔹 {name} ({symbol}) - 오류 발생: {str(e)}\n\n"

    send_telegram(full_message)

job()
