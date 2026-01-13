import streamlit as st
import pandas as pd
import psycopg2
import config 
import time
import redis
import plotly.graph_objects as go # <--- NEEDED FOR CHARTS

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Adaptive Hedge Bot",
    page_icon="📈",
    layout="wide"
)

# --- CONNECTIONS ---
def get_redis_connection():
    return redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=config.REDIS_DB)

def get_connection():
    return psycopg2.connect(
        dbname=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASS,
        host=config.DB_HOST,
        port=config.DB_PORT
    )

# --- DATA FETCHING ---
def get_live_price(symbol):
    try:
        r = get_redis_connection()
        price_bytes = r.get(f"price:{symbol}")
        return float(price_bytes) if price_bytes else 0.00
    except Exception as e:
        return 0.00

def get_historical_signals():
    try:
        conn = get_connection()
        query = "SELECT symbol, signal_type, price, sma, created_at FROM trade_signals ORDER BY created_at DESC LIMIT 10"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except:
        return pd.DataFrame()

def get_bars(symbol):
    """Fetch the latest OHLC bars for the chart"""
    try:
        conn = get_connection()
        # Fetch last 60 minutes of data
        query = f"SELECT * FROM market_bars WHERE symbol = '{symbol}' ORDER BY timestamp DESC LIMIT 60"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except:
        return pd.DataFrame()

# --- DASHBOARD UI ---
st.title("⚡ Real-Time Trading Engine")

# 1. LIVE METRICS ROW (Price + OHLC)
st.markdown("### 🔴 Live Market Data")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    price_placeholder = st.empty() # The Big Price
with col2:
    open_metric = st.empty()
with col3:
    high_metric = st.empty()
with col4:
    low_metric = st.empty()
with col5:
    close_metric = st.empty()

# 2. CHART SECTION
st.markdown("### 📊 Market Structure (1-Min Candles)")
chart_placeholder = st.empty()

# 3. ALERTS SECTION
st.markdown("### 📜 Trade History")
table_placeholder = st.empty()

# --- MAIN LOOP ---
if st.checkbox("Start Live Feed", value=True):
    counter = 0
    prev_price = get_live_price("FAKEPACA")
    
    while True:
        # --- A. FAST UPDATE (0.1s) ---
        current_price = get_live_price("FAKEPACA")
        
        if current_price != prev_price:
            price_change = current_price - prev_price
            price_placeholder.metric(
                label="FAKEPACA Price", 
                value=f"${current_price:.2f}", 
                delta=f"{price_change:.2f}"
            )
            prev_price = current_price

        # --- B. SLOW UPDATE (1.0s) ---
        if counter % 10 == 0:
            
            # 1. Update Chart & OHLC
            df_bars = get_bars("FAKEPACA")
            if not df_bars.empty:
                # Draw Candle Chart
                fig = go.Figure(data=[go.Candlestick(
                    x=df_bars['timestamp'],
                    open=df_bars['open'],
                    high=df_bars['high'],
                    low=df_bars['low'],
                    close=df_bars['close']
                )])
                fig.update_layout(height=400, margin=dict(l=0, r=0, t=0, b=0), xaxis_rangeslider_visible=False)
                chart_placeholder.plotly_chart(fig, use_container_width=True, key=f"chart_{counter}")

                # Update OHLC numbers (Latest Bar)
                latest = df_bars.iloc[0]
                open_metric.metric("Open", f"${latest['open']:.2f}")
                high_metric.metric("High", f"${latest['high']:.2f}")
                low_metric.metric("Low", f"${latest['low']:.2f}")
                close_metric.metric("Close", f"${latest['close']:.2f}")

            # 2. Update Alerts Table
            df_signals = get_historical_signals()
            table_placeholder.dataframe(df_signals, hide_index=True, use_container_width=True)

        counter += 1
        time.sleep(0.1)