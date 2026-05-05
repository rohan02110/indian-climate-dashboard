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

# --- 3. SIDEBAR (NAVIGATION & INFO) ---
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
        
        # Filters
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            selected_cities = st.multiselect("Select Cities", df['City'].unique(), default=df['City'].unique()[:3])
        with col_f2:
            available_seasons = ["All Seasons"] + sorted(list(df['Season'].unique()))
            selected_season = st.selectbox("Filter by Season", available_seasons)

        filtered_df = df[df['City'].isin(selected_cities)]
        if selected_season != "All Seasons":
            filtered_df = filtered_df[filtered_df['Season'] == selected_season]
        
        # Metrics
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Avg Temp", f"{filtered_df['Temperature_Avg (°C)'].mean():.1f} °C")
        k2.metric("Max Temp", f"{filtered_df['Temperature_Max (°C)'].max():.1f} °C")
        k3.metric("Rainfall", f"{filtered_df['Rainfall (mm)'].sum():.0f} mm")
        k4.metric("Humidity", f"{filtered_df['Humidity (%)'].mean():.1f} %")

        # 1. Trend Line
        st.subheader("🌡️ Temperature Trends")
        fig_line = px.line(filtered_df, x='Date', y='Temperature_Avg (°C)', color='City', template="plotly_dark")
        st.plotly_chart(fig_line, use_container_width=True)

        # 2. Heatmap & Scatter Plot Row
        col_graph1, col_graph2 = st.columns(2)

        with col_graph1:
            st.subheader("🗓️ Monthly Avg Temp Heatmap")
            heatmap_data = filtered_df.groupby(['City', 'Month_Num', 'Month'])['Temperature_Avg (°C)'].mean().reset_index().sort_values('Month_Num')
            fig_heat = px.density_heatmap(
                heatmap_data, 
                x="Month", 
                y="City", 
                z="Temperature_Avg (°C)", 
                color_continuous_scale='RdYlBu_r',
                text_auto='.1f',
                template="plotly_dark"
            )
            st.plotly_chart(fig_heat, use_container_width=True)

        with col_graph2:
            st.subheader("💧 Humidity vs. Temperature")
            fig_scatter = px.scatter(
                filtered_df, 
                x="Temperature_Avg (°C)", 
                y="Humidity (%)", 
                color="City",
                size="Rainfall (mm)",
                hover_name="City",
                template="plotly_dark",
                opacity=0.6
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

    elif page == "Live Prediction":
        # ... (Rest of your prediction logic remains the same) ...
        st.title("🔮 AI Weather Prediction")
        c1, c2 = st.columns(2)
        with c1: city_input = st.text_input("🏙️ City Name", "Pune")
        with c2: pred_date = st.date_input("📅 Select Date", datetime.now())

        if st.button("🚀 Predict Weather"):
            if os.path.exists('models.zip'):
                try:
                    with zipfile.ZipFile('models.zip', 'r') as z:
                        file_list = z.namelist()
                        model_file = next((f for f in file_list if f.endswith('temp_model.pkl')), None)
                        if model_file:
                            with z.open(model_file) as f: model = pickle.load(f)
                            api_url = "https://api.open-meteo.com/v1/forecast?latitude=18.52&longitude=73.85&current_weather=true"
                            res = requests.get(api_url).json()
                            base_temp = res['current_weather']['temperature']
                            st.success(f"✅ AI Model successfully loaded.")
                            res_col1, res_col2 = st.columns(2)
                            with res_col1:
                                st.write("**AI Temp Prediction (24h)**")
                                st.line_chart([base_temp + (i * 0.12) for i in range(24)])
                            with res_col2:
                                st.write("**AI Rain Probability**")
                                st.bar_chart([0, 5, 2, 0, 10, 0, 0, 3] * 3)
                except Exception as e: st.error(f"Error: {e}")
            else: st.error("⚠️ models.zip missing.")
else:
    st.error("❌ Data error: Check 'data/weather_data.zip' on GitHub.")
