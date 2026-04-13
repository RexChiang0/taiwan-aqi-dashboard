import os
import requests
import pandas as pd
import sqlite3

# API
API_KEY = os.getenv('MY_API_KEY')
url = f"https://data.moenv.gov.tw/api/v2/aqx_p_432?api_key={API_KEY}"

print("1. 🚚 正在向環境部索取最新空氣資料...")
response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    
    # 【Transform: 資料轉換與清理】
    print("2. 🔪 資料抓取成功！交給 Pandas 整理成表格...")
    df = pd.DataFrame(data)
    
    # 我們只需要這五個欄位，其他的丟掉，保持資料庫輕量乾淨
    columns_to_keep = ['sitename', 'county', 'aqi', 'pm2.5', 'publishtime']
    df_clean = df[columns_to_keep]
    
    print("\n--- 整理好的前五筆資料長這樣 ---")
    print(df_clean.head()) # 只印出前五筆預覽
    
    # 【Load: 存入資料庫】
    print("\n3. ❄️ 準備將資料存入資料庫 (taiwan_aqi.db)...")
    
    # 連線到 SQLite 資料庫 (如果檔案不存在，Python 會自動幫你建立一個)
    conn = sqlite3.connect('taiwan_aqi.db')
    
    # 把表格存進資料庫裡，我們把這張資料表命名為 'aqi_records'
    # if_exists='append' 代表如果表已經存在，就把新資料接在最底下 (這對累積歷史資料很重要！)
    # index=False 代表不要把 Pandas 預設的 0, 1, 2, 3 行號存進去
    df_clean.to_sql('aqi_records', conn, if_exists='append', index=False)
    
    # 關閉資料庫連線 (關冰箱門)
    conn.close()
    
    print("✅ 大功告成！資料已經安全存入 taiwan_aqi.db 囉！")

else:
    print(f"❌ 哎呀，抓取失敗了。錯誤代碼：{response.status_code}")
