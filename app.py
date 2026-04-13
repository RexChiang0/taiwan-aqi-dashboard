import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

# 1. 餐廳裝潢：設定網頁標題與版面寬度
st.set_page_config(page_title="台灣空氣品質追蹤", layout="wide")
st.title("TW 台灣空氣品質即時儀表板")

# 2. 去冰箱拿菜：從資料庫讀取資料的函數
def load_data():
    # 連線到我們剛剛建立的資料庫
    conn = sqlite3.connect('taiwan_aqi.db')
    df = pd.read_sql("SELECT * FROM aqi_records", conn)
    conn.close()
    
    # 將 aqi 和 pm2.5 轉換成數字格式，方便畫圖
    df['aqi'] = pd.to_numeric(df['aqi'], errors='coerce')
    df['pm2.5'] = pd.to_numeric(df['pm2.5'], errors='coerce')
    
    # 抓出最新的一筆更新時間，並過濾出最新的資料
    latest_time = df['publishtime'].max()
    latest_df = df[df['publishtime'] == latest_time]
    
    return latest_df, latest_time

# 執行讀取資料
df_latest, update_time = load_data()

st.write(f"🔄 資料最後更新時間: **{update_time}**")
st.divider() # 畫一條分隔線

# 3. 擺盤上桌：將網頁切成左右兩半
col1, col2 = st.columns(2)

with col1:
    st.subheader("🚨 全台空氣品質最差 Top 10 測站")
    # 將資料依 AQI 由大到小排序，取前 10 名
    worst_10 = df_latest.sort_values(by='aqi', ascending=False).head(10)
    
    # 畫出互動式長條圖
    fig = px.bar(worst_10, x='sitename', y='aqi', color='aqi', 
                 color_continuous_scale='Reds', text_auto=True,
                 labels={'sitename': '測站名稱', 'aqi': '空氣品質指標 (AQI)'})
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("📊 詳細數據表 (可點擊欄位排序)")
    # 顯示 DataFrame 讓教授可以自己操作查看
    st.dataframe(
        df_latest[['county', 'sitename', 'aqi', 'pm2.5']].sort_values(by='aqi', ascending=False), 
        height=400, 
        use_container_width=True
    )