import os
import requests

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
DATABASE_ID = os.environ["NOTION_DATABASE_ID"]  # ใช้ id เดิมของคุณได้

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def debug_database():
    # 1) ตรวจว่า ID นี้เป็น "database" จริงและเราเข้าถึงได้
    r = requests.get(f"https://api.notion.com/v1/databases/{DATABASE_ID}", headers=headers)
    print("GET database:", r.status_code)
    if r.status_code != 200:
        print(r.text)
        return False

    title = r.json().get("title", [])
    name = title[0].get("plain_text") if title else "(no title)"
    print("Database title:", name)

    # 2) ลอง query แล้วพิมพ์จำนวนแถวที่เห็น
    r2 = requests.post(f"https://api.notion.com/v1/databases/{DATABASE_ID}/query", headers=headers)
    print("QUERY database:", r2.status_code)
    if r2.status_code != 200:
        print(r2.text)
        return False

    print("Rows visible:", len(r2.json().get("results", [])))
    return True

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
        props = page.get("properties", {})
        ticker_prop = props.get("Ticker", {})

        ticker = None
        ptype = ticker_prop.get("type")

        if ptype == "rich_text":
            rt = ticker_prop.get("rich_text", [])
            if rt:
                ticker = rt[0].get("plain_text")

        elif ptype == "title":
            tt = ticker_prop.get("title", [])
            if tt:
                ticker = tt[0].get("plain_text")

        # เผื่อกรณีเป็น plain_text ตรง ๆ (บางรูปแบบ/บอทอื่น)
        elif "plain_text" in ticker_prop:
            ticker = ticker_prop.get("plain_text")

        if not ticker:
            continue

        ticker = ticker.strip()
        if not ticker:
            continue

        price = get_stock_price(ticker)

        update_url = f"https://api.notion.com/v1/pages/{page['id']}"
        body = {"properties": {"Price": {"number": price}}}
        requests.patch(update_url, headers=headers, json=body)
        print(ticker, price)


if __name__ == "__main__":
    if debug_database():
        update_database()

