import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

# 1. 餐廳裝潢：設定網頁標題與版面寬度
st.set_page_config(page_title="台灣空氣品質追蹤", layout="wide")
st.title("🇹🇼 台灣空氣品質即時儀表板")

# 2. 去冰箱拿菜：從資料庫讀取所有歷史資料
def load_data():
    conn = sqlite3.connect('taiwan_aqi.db')
    df = pd.read_sql("SELECT * FROM aqi_records", conn)
    conn.close()
    
    # 清除重複的資料！
    # 規則：如果「測站名稱 (sitename)」和「發布時間 (publishtime)」都一樣，就只保留第一筆
    df = df.drop_duplicates(subset=['sitename', 'publishtime'], keep='first')
    
    df['aqi'] = pd.to_numeric(df['aqi'], errors='coerce')
    df['pm2.5'] = pd.to_numeric(df['pm2.5'], errors='coerce')
    return df

# 讀取全部資料
df = load_data()

# 抓出最新的一筆更新時間，並過濾出最新的資料供排行榜使用
latest_time = df['publishtime'].max()
df_latest = df[df['publishtime'] == latest_time]

st.write(f"🔄 資料最後更新時間: **{latest_time}**")
st.divider() # 畫一條分隔線


# 3. 擺盤上桌：將最新資料切成左右兩半 (保留原本的功能)
col1, col2 = st.columns(2)

with col1:
    st.subheader("🚨 全台空氣品質最差 Top 10 測站")
    worst_10 = df_latest.sort_values(by='aqi', ascending=False).head(10)
    fig_bar = px.bar(worst_10, x='sitename', y='aqi', color='aqi', 
                 color_continuous_scale='Reds', text_auto=True,
                 labels={'sitename': '測站名稱', 'aqi': '空氣品質指標 (AQI)'})
    st.plotly_chart(fig_bar, use_container_width=True)

with col2:
    st.subheader("📊 最新詳細數據表 (可點擊排序)")
    st.dataframe(
        df_latest[['county', 'sitename', 'aqi', 'pm2.5']].sort_values(by='aqi', ascending=False), 
        height=400, 
        use_container_width=True
    )


# ================= 新增：歷史趨勢查詢區塊 =================
st.subheader("📈 單一測站歷史趨勢查詢")

# 建立一個下拉式選單，把所有測站名稱列出來讓使用者選
station_list = df['sitename'].unique()
selected_station = st.selectbox("請選擇您想查詢的測站：", station_list)

# 從大表格中，只篩選出使用者選到的那個測站的資料
df_station = df[df['sitename'] == selected_station]

# 畫出折線圖
fig_line = px.line(df_station, x='publishtime', y='aqi', 
                   title=f"{selected_station} 測站 AQI 歷史趨勢",
                   markers=True, # 顯示資料點
                   labels={'publishtime': '更新時間', 'aqi': '空氣品質指標 (AQI)'})
st.plotly_chart(fig_line, use_container_width=True)

st.divider() # 再畫一條分隔線
# =========================================================