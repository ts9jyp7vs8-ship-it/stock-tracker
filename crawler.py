import requests
import json
import os
from datetime import datetime

# 5大券商分點代碼 (玩股網對應的 ID)
BROKERS = {
    "元大": "9800",
    "美商高盛": "1470",
    "台灣摩根史丹利": "1480",
    "摩根大通": "1540",
    "凱基": "9200"
}

DATA_FILE = "data.json"

# 載入歷史紀錄以計算連續天數
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        history = json.load(f)
else:
    history = {"last_update": "", "consecutive_buys": {}, "daily_records": []}

today_str = datetime.now().strftime("%Y-%m-%d")

# 如果今天已經抓過就不重複執行
if history["last_update"] == today_str:
    print("今日資料已更新，跳過。")
    exit()

current_daily = {}
today_all_buys = set()

for name, broker_id in BROKERS.items():
    # 玩股網券商買賣超的實際資料 API 網址
    url = f"https://wantgoo.com{broker_id}&orderBy=count"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.wantgoo.com/"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        # 假設 API 回傳格式內有 buy 和 sell 陣列
        # 這裡取前 5 大
        top_buys = data.get("buy", [])[:5]
        top_sells = data.get("sell", [])[:5]
        
        current_daily[name] = {
            "buys": [{"id": x["id"], "name": x["name"], "count": x["count"]} for x in top_buys],
            "sells": [{"id": x["id"], "name": x["name"], "count": x["count"]} for x in top_sells]
        }
        
        # 記錄所有今天有被這5家券商買超的股票
        for b in top_buys:
            today_all_buys.add(b["name"])
            
    except Exception as e:
        print(f"抓取 {name} 失敗: {e}")
        current_daily[name] = {"buys": [], "sells": []}

# 更新連續買超天數邏輯
new_consecutive = {}
# 檢查過去有紀錄的股票
for stock_name, days in history.get("consecutive_buys", {}).items():
    if stock_name in today_all_buys:
        new_consecutive[stock_name] = days + 1  # 連續買超，天數加 1
        today_all_buys.remove(stock_name)       # 處理完了，移除
    # 如果今天沒買超，就不放入 new_consecutive (代表中斷，歸零重新計算)

# 剩下來的 today_all_buys 就是今天新進榜的股票，算第 1 天
for stock_name in today_all_buys:
    new_consecutive[stock_name] = 1

# 篩選出連續 3 日與 5 日的股票
streak_3 = [stock for stock, days in new_consecutive.items() if days >= 3]
streak_5 = [stock for stock, days in new_consecutive.items() if days >= 5]

# 更新歷史總結構
history["last_update"] = today_str
history["consecutive_buys"] = new_consecutive
history["streak_3"] = streak_3
history["streak_5"] = streak_5

# 只保留最近 7 天的每日明細，避免檔案過大
history["daily_records"].insert(0, {"date": today_str, "data": current_daily})
history["daily_records"] = history["daily_records"][:7]

# 存回 json 檔
with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(history, f, ensure_ascii=False, indent=2)

print("資料更新成功！")
