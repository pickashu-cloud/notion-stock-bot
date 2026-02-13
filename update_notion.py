import os
import requests

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
DATABASE_ID = os.environ["NOTION_DATABASE_ID"]  # ใช้ id เดิมของคุณได้

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def get_stock_price(symbol):
    url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"
    r = requests.get(url).json()
    return r["quoteResponse"]["result"][0]["regularMarketPrice"]

def query_any(id_):
    # ลอง query เป็น database ก่อน
    url_db = f"https://api.notion.com/v1/databases/{id_}/query"
    r = requests.post(url_db, headers=headers)
    if r.status_code == 200 and "results" in r.json():
        return r.json()["results"]

    # ถ้าไม่ใช่ database ให้มองเป็น page แล้วดึง children blocks
    url_blk = f"https://api.notion.com/v1/blocks/{id_}/children?page_size=100"
    r = requests.get(url_blk, headers=headers).json()

    # หา block ที่เป็น child_database
    for b in r.get("results", []):
        if b.get("type") == "child_database":
            real_db_id = b["id"]
            r2 = requests.post(f"https://api.notion.com/v1/databases/{real_db_id}/query", headers=headers).json()
            return r2.get("results", [])
    return []

def update_database():
    pages = query_any(DATABASE_ID)

    for page in pages:
        props = page["properties"]
        ticker = props["Ticker"]["rich_text"][0]["text"]["content"]
        price = get_stock_price(ticker)

        update_url = f"https://api.notion.com/v1/pages/{page['id']}"
        body = {"properties": {"Price": {"number": price}}}
        requests.patch(update_url, headers=headers, json=body)
        print(ticker, price)

if __name__ == "__main__":
    update_database()
