import os
import requests

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
DATABASE_ID = os.environ["DATABASE_ID"]

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def get_stock_price(symbol):
    url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"
    r = requests.get(url).json()
    return r["quoteResponse"]["result"][0]["regularMarketPrice"]

def update_database():
    query_url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    data = requests.post(query_url, headers=headers).json()

    for page in data["results"]:
        ticker = page["properties"]["Ticker"]["rich_text"][0]["text"]["content"]
        price = get_stock_price(ticker)

        update_url = f"https://api.notion.com/v1/pages/{page['id']}"
        body = {
            "properties": {
                "Price": {
                    "number": price
                }
            }
        }

        requests.patch(update_url, headers=headers, json=body)
        print(ticker, price)

if __name__ == "__main__":
    update_database()
