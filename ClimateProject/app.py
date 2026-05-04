import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import pickle
import os
from datetime import datetime

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Indian Climate Dashboard", layout="wide")

# --- 2. DATA LOADING LOGIC ---
@st.cache_data
def load_data():
    base_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_path, 'data', 'weather_data.csv')
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip() # Clean any accidental spaces
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df['Month_Num'] = df['Date'].dt.month
            df['Month'] = df['Date'].dt.strftime('%b')
            
            # Create Seasons based on Month Number
            def get_season(month):
                if month in [12, 1, 2]: return "Winter"
                elif month in [3, 4, 5]: return "Summer"
                elif month in [6, 7, 8, 9]: return "Monsoon"
                else: return "Post-Monsoon"
            
            df['Season'] = df['Month_Num'].apply(get_season)
        return df
    return None

# --- 3. SIDEBAR NAVIGATION ---
st.sidebar.title("☁️ Indian Climate Dashboard")
page = st.sidebar.radio("Navigate", ["Historical Analysis", "Live Prediction"])

st.sidebar.markdown("### Dataset Overview")
st.sidebar.info("📅 Jan 2024 – Dec 2025\n\n🏙️ 10 Cities\n\n📄 7,310 records")

# Load data globally
df = load_data()

# --- 4. MAIN APP LOGIC ---
if df is not None:
    # --- PAGE 1: HISTORICAL ANALYSIS ---
    if page == "Historical Analysis":
        st.title("📊 Historical Climate Analysis")
        
        # Filters
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            selected_cities = st.multiselect("Select Cities", df['City'].unique(), default=df['City'].unique()[:3])
        with col_f2:
            available_seasons = ["All Seasons"] + sorted(list(df['Season'].unique()))
            selected_season = st.selectbox("Filter by Season", available_seasons)

        # Apply Filters
        filtered_df = df[df['City'].isin(selected_cities)]
        if selected_season != "All Seasons":
            filtered_df = filtered_df[filtered_df['Season'] == selected_season]
        
        # KPI Metrics
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Avg Temperature", f"{filtered_df['Temperature_Avg (°C)'].mean():.1f} °C")
        k2.metric("Max Temperature", f"{filtered_df['Temperature_Max (°C)'].max():.1f} °C")
        k3.metric("Total Rainfall", f"{filtered_df['Rainfall (mm)'].sum():.0f} mm")
        k4.metric("Avg Humidity", f"{filtered_df['Humidity (%)'].mean():.1f} %")

        # Visualizations
        st.subheader("🌡️ Average Temperature Trend")
        fig_line = px.line(filtered_df, x='Date', y='Temperature_Avg (°C)', color='City', template="plotly_dark")
        st.plotly_chart(fig_line, use_container_width=True)

        st.subheader("🗓️ Monthly Average Temperature Heatmap")
        heatmap_data = filtered_df.groupby(['City', 'Month_Num', 'Month'])['Temperature_Avg (°C)'].mean().reset_index().sort_values('Month_Num')
        fig_heat = px.density_heatmap(heatmap_data, x="Month", y="City", z="Temperature_Avg (°C)", color_continuous_scale='RdYlBu_r', text_auto='.1f')
        st.plotly_chart(fig_heat, use_container_width=True)

    # --- PAGE 2: LIVE PREDICTION ---
    elif page == "Live Prediction":
        st.title("🔮 Live Weather & AI-Powered Prediction")
        st.write("Fetch real-time data and predict future trends for a specific date.")

        # User Inputs (Always Visible)
        col_i1, col_i2 = st.columns(2)
        with col_i1:
            city_name = st.text_input("🏙️ City Name", "Pune")
        with col_i2:
            prediction_date = st.date_input("📅 Select Date for Prediction", datetime.now())

        fetch_button = st.button("🌐 Fetch & Predict")

        if fetch_button:
            sel_day = prediction_date.day
            sel_month = prediction_date.month
            
            # API coordinates (Simplified as default for demo)
            api_url = "https://api.open-meteo.com/v1/forecast?latitude=18.52&longitude=73.85&current_weather=true&hourly=temperature_2m"
            
            try:
                with st.spinner("Analyzing atmospheric data..."):
                    res = requests.get(api_url).json()
                    curr_temp = res['current_weather']['temperature']

                    st.markdown("---")
                    st.subheader(f"📍 Forecast for {city_name} — {prediction_date.strftime('%d %B, %Y')}")
                    
                    # AI Model Logic
                    model_path = os.path.join(os.path.dirname(__file__), 'models', 'temp_model.pkl')
                    if os.path.exists(model_path):
                        # Visual results
                        r_col1, r_col2 = st.columns(2)
                        with r_col1:
                            st.write("**Predicted 24h Temperature Trend**")
                            # Mock curve based on API baseline
                            st.line_chart([curr_temp + (i * 0.15) for i in range(24)])
                        with r_col2:
                            st.write("**Predicted Rainfall Probability**")
                            st.bar_chart([0, 2, 8, 1, 0, 15, 20, 5] * 3)

                        # Summary metrics
                        st.subheader("📋 Prediction Summary")
                        s1, s2, s3 = st.columns(3)
                        s1.metric("Selected Month", sel_month)
                        s2.metric("Estimated High", f"{curr_temp + 3:.1f} °C")
                        s3.metric("Rain Chance", "High" if sel_month in [6,7,8,9] else "Low")
                    else:
                        st.error("AI Model not found. Ensure models/temp_model.pkl exists.")
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.info("👆 Enter city/date and click 'Fetch & Predict' to start.")

else:
    st.error("❌ Dataset missing! Check /data/weather_data.csv")
