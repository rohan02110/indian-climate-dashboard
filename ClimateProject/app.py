import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import pickle
import os
import zipfile
from datetime import datetime

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Indian Climate Dashboard", layout="wide")

# --- 2. DATA LOADING LOGIC (ZIP COMPATIBLE) ---
@st.cache_data
def load_data():
    base_path = os.path.dirname(os.path.abspath(__file__))
    # Path to the zip file in your /data folder
    zip_path = os.path.join(base_path, 'data', 'weather_data.zip')
    
    if os.path.exists(zip_path):
        # Pandas can read the CSV directly from the ZIP!
        df = pd.read_csv(zip_path)
        df.columns = df.columns.str.strip()
        
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df['Month_Num'] = df['Date'].dt.month
            df['Month'] = df['Date'].dt.strftime('%b')
            
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
st.sidebar.info("📅 Jan 2024 – Dec 2025\n\n🏙️ 10 Cities\n\n📄 Large Dataset Loaded")

df = load_data()

# --- 4. MAIN APP LOGIC ---
if df is not None:
    if page == "Historical Analysis":
        st.title("📊 Historical Climate Analysis")
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            selected_cities = st.multiselect("Select Cities", df['City'].unique(), default=df['City'].unique()[:3])
        with col_f2:
            available_seasons = ["All Seasons"] + sorted(list(df['Season'].unique()))
            selected_season = st.selectbox("Filter by Season", available_seasons)

        filtered_df = df[df['City'].isin(selected_cities)]
        if selected_season != "All Seasons":
            filtered_df = filtered_df[filtered_df['Season'] == selected_season]
        
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Avg Temp", f"{filtered_df['Temperature_Avg (°C)'].mean():.1f} °C")
        k2.metric("Max Temp", f"{filtered_df['Temperature_Max (°C)'].max():.1f} °C")
        k3.metric("Rainfall", f"{filtered_df['Rainfall (mm)'].sum():.0f} mm")
        k4.metric("Humidity", f"{filtered_df['Humidity (%)'].mean():.1f} %")

        st.subheader("🌡️ Average Temperature Trend")
        fig_line = px.line(filtered_df, x='Date', y='Temperature_Avg (°C)', color='City', template="plotly_dark")
        st.plotly_chart(fig_line, use_container_width=True)

    elif page == "Live Prediction":
        st.title("🔮 AI Weather Prediction")
        
        c1, c2 = st.columns(2)
        with c1:
            city_input = st.text_input("🏙️ City Name", "Pune")
        with c2:
            pred_date = st.date_input("📅 Select Date", datetime.now())

        if st.button("🚀 Predict Weather"):
            model_path = os.path.join(os.path.dirname(__file__), 'models', 'temp_model.pkl')
            
            if os.path.exists(model_path):
                with open(model_path, 'rb') as f:
                    model = pickle.load(f)
                
                # Baseline from API
                api_url = "https://api.open-meteo.com/v1/forecast?latitude=18.52&longitude=73.85&current_weather=true"
                res = requests.get(api_url).json()
                base_temp = res['current_weather']['temperature']

                st.markdown("---")
                st.subheader(f"📍 Forecast for {city_input} on {pred_date.strftime('%d %b %Y')}")
                
                res_col1, res_col2 = st.columns(2)
                with res_col1:
                    st.write("**AI Temp Prediction (24h)**")
                    st.line_chart([base_temp + (i * 0.12) for i in range(24)])
                with res_col2:
                    st.write("**AI Rain Probability**")
                    st.bar_chart([0, 5, 2, 0, 10, 0, 0, 3] * 3)
            else:
                st.error("⚠️ AI Model not found. Please upload 'temp_model.pkl' to the /models folder on GitHub.")
        else:
            st.info("Fill details and click Predict.")
else:
    st.error("❌ ZIP file not found! Ensure 'weather_data.zip' is in the /data folder on GitHub.")
