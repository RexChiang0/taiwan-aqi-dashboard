import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

# 1. 餐廳裝潢：設定網頁標題與版面寬度
st.set_page_config(page_title="台灣空氣品質追蹤", layout="wide")
st.title("TW 台灣空氣品質即時儀表板")

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

# ================= 3. 側邊欄篩選器 (Sidebar Controls) =================
st.sidebar.header("🔍 篩選與設定")

# 篩選一：縣市選擇 (多選)
all_counties = sorted(df_latest['county'].unique())
selected_counties = st.sidebar.multiselect(
    "選擇顯示縣市：", 
    all_counties, 
    default=all_counties # 預設全選
)

# 篩選二：AQI 門檻 (滑桿)
aqi_threshold = st.sidebar.slider("只顯示 AQI 大於：", 0, 200, 0)

# --- 執行篩選邏輯 ---
# 根據選中的縣市與 AQI 門檻過濾資料
mask = (df_latest['county'].isin(selected_counties)) & (df_latest['aqi'] >= aqi_threshold)
df_filtered = df_latest[mask]
# =====================================================================

st.write(f"🔄 資料最後更新時間: **{latest_time}**")
st.write(f"💡 目前顯示 **{len(df_filtered)}** 個符合條件的測站")
st.divider() # 畫一條分隔線

# ================= 1. 台灣空氣品質分佈地圖 =================
st.subheader("🗺️ 全台即時空氣品質分佈圖")

# 確保經緯度是數字格式
df_filtered['longitude'] = pd.to_numeric(df_filtered['longitude'], errors='coerce')
df_filtered['latitude'] = pd.to_numeric(df_filtered['latitude'], errors='coerce')

# 使用 Plotly 畫出地圖
fig_map = px.scatter_mapbox(
    df_filtered, 
    lat="latitude", 
    lon="longitude", 
    color="aqi",            # 顏色根據 AQI 變化
    size="aqi",             # 點的大小也根據 AQI 變化
    hover_name="sitename",  # 滑鼠移上去顯示測站名稱
    hover_data=["county", "aqi", "pm2.5"], 
    color_continuous_scale=px.colors.sequential.Reds, # 使用紅色漸層
    zoom=6.5,               # 設定初始縮放倍率
    height=500,
    mapbox_style="open-street-map" # 使用免金鑰的開放地圖
)

st.plotly_chart(fig_map, use_container_width=True)
st.divider() 
# =========================================================


# 3. 擺盤上桌：將最新資料切成左右兩半 (保留原本的功能)
col1, col2 = st.columns(2)

with col1:
    st.subheader("🚨 全台空氣品質最差 Top 10 測站")
    worst_10 = df_filtered.sort_values(by='aqi', ascending=False).head(10)
    fig_bar = px.bar(worst_10, x='sitename', y='aqi', color='aqi', 
                 color_continuous_scale='Reds', text_auto=True,
                 labels={'sitename': '測站名稱', 'aqi': '空氣品質指標 (AQI)'})
    st.plotly_chart(fig_bar, use_container_width=True)

with col2:
    st.subheader("📊 最新詳細數據表 (可點擊排序)")
    st.dataframe(
        df_filtered[['county', 'sitename', 'aqi', 'pm2.5']].sort_values(by='aqi', ascending=False), 
        height=400, 
        use_container_width=True
    )
st.divider()


# ================= 2. 縣市平均值進階運算 (Data Aggregation) =================
st.subheader("📊 各縣市空氣品質平均值")

# 使用 Pandas 強大的 groupby 功能：
# 1. 依照 'county' (縣市) 分組
# 2. 針對 'aqi' 欄位計算平均值 (mean)
# 3. reset_index() 是為了讓結果變回乾淨的表格
df_county_avg = df_filtered.groupby('county')['aqi'].mean().reset_index()

# 為了美觀，我們將平均值四捨五入到小數點第一位
df_county_avg['aqi'] = df_county_avg['aqi'].round(1)

# 將結果依照 AQI 由大到小排序 (最差的在前)
df_county_avg = df_county_avg.sort_values(by='aqi', ascending=False)

# 畫出縣市平均值的長條圖
fig_county = px.bar(
    df_county_avg, 
    x='county', 
    y='aqi', 
    color='aqi',
    title="全台各縣市平均 AQI 排行",
    color_continuous_scale='OrRd', # 使用橘紅色系
    text_auto=True,
    labels={'county': '縣市', 'aqi': '平均 AQI'}
)

st.plotly_chart(fig_county, use_container_width=True)
st.divider()
# =========================================================================


# ================= 新增：歷史趨勢查詢區塊 =================
st.subheader("📈 單一測站歷史趨勢查詢")

# 建立一個下拉式選單，把所有測站名稱列出來讓使用者選
station_list = df['sitename'].unique()
selected_station = st.selectbox("請選擇您想查詢的測站：", station_list)

# 從大表格中，只篩選出使用者選到的那個測站的資料
df_station = df[df['sitename'] == selected_station].copy()

# 確保時間是由舊到新正確排序的
df_station['publishtime'] = pd.to_datetime(df_station['publishtime'])
df_station = df_station.sort_values('publishtime')

# 畫出折線圖
fig_line = px.line(df_station, x='publishtime', y='aqi', 
                   title=f"{selected_station} 測站 AQI 歷史趨勢",
                   markers=True, # 顯示資料點
                   labels={'publishtime': '時間', 'aqi': '空氣品質指標 (AQI)'})

fig_line.update_xaxes(
    type='date',                 # 強制使用連續時間軸
    tickformat='%m-%d %H:%M',    # 讓 Plotly 自動把時間縮短顯示
    tickangle=45                 # 標籤傾斜避免擠在一起
)
st.plotly_chart(fig_line, use_container_width=True)

st.divider() # 再畫一條分隔線
# =========================================================