import streamlit as st
import yfinance as yf
import pandas as pd

# 網頁設定
st.set_page_config(page_title="TSLA vs BTC 關聯性分析", layout="wide")
st.title("⚡ Tesla (TSLA) 與 Bitcoin (BTC) 聯動性監控平台")
st.markdown("觀測指標：**30 天滾動相關係數 (Rolling Correlation)**。探討 TSLA 是否具備數位資產儲備公司 (DAT.co) 的市場特性。")

# 側邊欄設定
st.sidebar.header("參數設定")
days = st.sidebar.slider("選擇歷史天數", min_value=90, max_value=730, value=365)

@st.cache_data
def load_data(days):
    # 1. 抓取資料
    tsla = yf.download("TSLA", period=f"{days}d")['Close']
    btc = yf.download("BTC-USD", period=f"{days}d")['Close']

    # 2. 強制轉為一維度並「移除時區」，避免雲端新版 Pandas 對齊失敗
    tsla = tsla.squeeze()
    btc = btc.squeeze()
    if hasattr(tsla.index, 'tz_localize'):
        tsla.index = tsla.index.tz_localize(None)
    if hasattr(btc.index, 'tz_localize'):
        btc.index = btc.index.tz_localize(None)

    # 3. 合併數據
    df = pd.DataFrame({'TSLA': tsla, 'BTC': btc})

    # 4. 關鍵修復：特斯拉六日沒開盤會有空值，用禮拜五的價格補上 (ffill)
    df['TSLA'] = df['TSLA'].ffill()
    df = df.dropna()

    # 5. 計算相關係數
    if not df.empty:
        returns = df.pct_change().dropna()
        df['30D_Correlation'] = returns['TSLA'].rolling(window=30).corr(returns['BTC'])
    else:
        returns = pd.DataFrame()

    return df, returns

# 載入並處理資料
df, returns = load_data(days)

# 防呆機制：確保資料不是空的才畫圖
if df.empty:
    st.error("⚠️ 無法從 Yahoo Finance 獲取資料，這可能是套件對齊或伺服器連線問題。請重新整理或稍後再試。")
else:
    # --- 視覺化圖表區塊 ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 價格走勢對比 (標準化)")
        # 將兩者價格標準化至同一起跑點方便比較
        normalized_df = (df[['TSLA', 'BTC']] / df[['TSLA', 'BTC']].iloc[0]) * 100
        st.line_chart(normalized_df)

    with col2:
        st.subheader("🔗 30天滾動相關係數")
        st.markdown("數值越接近 1，代表連動性越強。")
        st.line_chart(df['30D_Correlation'].dropna())

    # --- 原始數據區塊 ---
    st.subheader("📊 近期原始數據")
    st.dataframe(df.tail(10))

