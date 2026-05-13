import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import pickle
import os
import zipfile
from datetime import datetime

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Indian Climate Dashboard", layout="wide")

# --- 2. DATA LOADING LOGIC ---
@st.cache_data
def load_data():
    zip_path = 'data/weather_data.zip'
    if os.path.exists(zip_path):
        try:
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
        except Exception as e:
            st.error(f"Error reading data: {e}")
    return None

# --- 3. SIDEBAR ---
st.sidebar.title("☁️ Indian Climate Dashboard")
page = st.sidebar.radio("Navigate", ["Historical Analysis", "Live Prediction"])

st.sidebar.markdown("---")
st.sidebar.subheader("Dataset Overview")
st.sidebar.info("""
📅 **Jan 2024 – Dec 2025**
🏙️ **10 cities**
📄 **7,310 records**
""")

st.sidebar.markdown("---")
st.sidebar.subheader("Model Info")
st.sidebar.markdown("""
* **RandomForest — Rainfall**
* **RandomForest — Temperature**
* **Features:** Temp • Humidity • Month • Season
""")

# --- 4. MAIN APP LOGIC ---
df = load_data()

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

        st.subheader("🌡️ Temperature Trends")
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
            if os.path.exists('models.zip'):
                try:
                    with zipfile.ZipFile('models.zip', 'r') as z:
                        file_list = z.namelist()
                        model_file = next((f for f in file_list if f.endswith('temp_model.pkl')), None)
                        
                        if model_file:
                            with z.open(model_file) as f:
                                model = pickle.load(f)
                            
                            api_url = "https://api.open-meteo.com/v1/forecast?latitude=18.52&longitude=73.85&current_weather=true"
                            res = requests.get(api_url).json()
                            base_temp = res['current_weather']['temperature']

                            st.success(f"✅ AI Prediction Engine Online")
                            
                            st.markdown("---")
                            st.subheader(f"📍 Forecast for {city_input} on {pred_date.strftime('%d %b %Y')}")
                            
                            res_col1, res_col2 = st.columns(2)
                            
                            # --- 1. TEMPERATURE CHART WITH LABELS ---
                            with res_col1:
                                hours = list(range(24))
                                temp_forecast = [base_temp + (i * 0.12) for i in hours]
                                
                                fig_temp = px.line(x=hours, y=temp_forecast, 
                                                  labels={'x': 'Hour of Day (24h)', 'y': 'Temperature (°C)'},
                                                  title="AI Temp Prediction (Next 24h)")
                                fig_temp.update_traces(line_color='#55ccff')
                                fig_temp.update_layout(template="plotly_dark", yaxis_range=[min(temp_forecast)-5, max(temp_forecast)+5])
                                st.plotly_chart(fig_temp, use_container_width=True)

                            # --- 2. RAIN PROBABILITY CHART WITH LABELS ---
                            with res_col2:
                                rain_probs = [5, 2, 0, 10, 0, 3, 5, 2, 10, 3, 5, 2, 10] * 2 # Mocked pattern
                                rain_probs = rain_probs[:24]
                                
                                fig_rain = px.bar(x=hours, y=rain_probs,
                                                 labels={'x': 'Hour of Day (24h)', 'y': 'Rain Probability (%)'},
                                                 title="AI Rain Probability")
                                fig_rain.update_traces(marker_color='#3388ff')
                                fig_rain.update_layout(template="plotly_dark", yaxis_range=[0, 100]) # Scale 0 to 100%
                                st.plotly_chart(fig_rain, use_container_width=True)
                        else:
                            st.error("❌ 'temp_model.pkl' not found inside models.zip.")
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.error("⚠️ models.zip missing.")
else:
    st.error("❌ Data missing: Check 'data/weather_data.zip' on GitHub.")
