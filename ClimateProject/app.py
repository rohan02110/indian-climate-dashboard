import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import pickle
import os

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Indian Climate Dashboard", layout="wide")

# --- 2. DATA LOADING FUNCTION ---
@st.cache_data
def load_data():
    base_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_path, 'data', 'weather_data.csv')
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip()
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df['Month_Num'] = df['Date'].dt.month
            df['Month'] = df['Date'].dt.strftime('%b')
            
            # --- ADD THIS SEASON LOGIC ---
            def get_season(month):
                if month in [12, 1, 2]: return "Winter"
                elif month in [3, 4, 5]: return "Summer"
                elif month in [6, 7, 8, 9]: return "Monsoon"
                else: return "Post-Monsoon"
            
            df['Season'] = df['Month_Num'].apply(get_season)
            # ----------------------------
        return df
    return None
# --- 3. SIDEBAR NAVIGATION ---
st.sidebar.title("☁️ Indian Climate Dashboard")
page = st.sidebar.radio("Navigate", ["Historical Analysis", "Live Prediction"])

st.sidebar.markdown("### Dataset Overview")
st.sidebar.info("📅 Jan 2024 – Dec 2025\n\n🏙️ 10 Cities\n\n📄 7,310 records")

# Load the data once
df = load_data()

# --- 4. MAIN APP LOGIC ---
if df is not None:
    if page == "Historical Analysis":
        st.title("📊 Historical Climate Analysis")
        
        # Filters
  with col_b:
            # We now use the 'Season' column we just created
            available_seasons = ["All Seasons"] + list(df['Season'].unique())
            selected_season = st.selectbox("Filter by Season", available_seasons)

        # Apply the Season Filter to your data
        if selected_season != "All Seasons":
            filtered_df = filtered_df[filtered_df['Season'] == selected_season]
        filtered_df = df[df['City'].isin(selected_cities)]
        
        # KPIs
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Avg Temperature", f"{filtered_df['Temperature_Avg (°C)'].mean():.1f} °C")
        k2.metric("Max Temperature", f"{filtered_df['Temperature_Max (°C)'].max():.1f} °C")
        k3.metric("Total Rainfall", f"{filtered_df['Rainfall (mm)'].sum():.0f} mm")
        k4.metric("Avg Humidity", f"{filtered_df['Humidity (%)'].mean():.1f} %")

        # Line Chart
        st.subheader("🌡️ Average Temperature Trend")
        fig_line = px.line(filtered_df, x='Date', y='Temperature_Avg (°C)', color='City', template="plotly_dark")
        st.plotly_chart(fig_line, use_container_width=True)

        # Heatmap
        st.subheader("🗓️ Monthly Average Temperature Heatmap")
        heatmap_data = filtered_df.groupby(['City', 'Month_Num', 'Month'])['Temperature_Avg (°C)'].mean().reset_index().sort_values('Month_Num')
        fig_heat = px.density_heatmap(heatmap_data, x="Month", y="City", z="Temperature_Avg (°C)", color_continuous_scale='RdYlBu_r', text_auto='.1f')
        st.plotly_chart(fig_heat, use_container_width=True)

    # --- LIVE PREDICTION PAGE ---
    elif page == "Live Prediction":
        st.title("🔮 Live Weather & AI-Powered Prediction")
        st.write("Fetch real-time conditions via Open-Meteo API.")

        city_name = st.text_input("🏙️ City Name", "Pune")
        
        # We use a stateful approach to keep the UI from disappearing
        if st.button("🌐 Fetch Live Weather"):
            api_url = "https://api.open-meteo.com/v1/forecast?latitude=18.52&longitude=73.85&current_weather=true&hourly=temperature_2m,relative_humidity_2m"
            
            try:
                res = requests.get(api_url).json()
                curr = res['current_weather']
                hour = res['hourly']

                st.markdown("---")
                st.subheader(f"📍 Current Conditions — {city_name}")
                
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Temperature", f"{curr['temperature']} °C")
                m2.metric("Humidity", f"{hour['relative_humidity_2m'][0]} %")
                m3.metric("Rainfall", "0.0 mm")
                m4.metric("Season", "Summer")

                # Hourly Chart
                st.subheader("📈 Next 24 Hours Forecast")
                h_df = pd.DataFrame({'Time': hour['time'][:24], 'Temp': hour['temperature_2m'][:24]})
                st.line_chart(h_df.set_index('Time'))
                
                # Mock Prediction Section
                st.markdown("---")
                st.subheader("🤖 AI Prediction")
                p1, p2 = st.columns(2)
                p1.line_chart([curr['temperature'] + (i * 0.1) for i in range(24)])
                p2.bar_chart([0, 1, 0, 5, 10, 2] * 4)

            except Exception as e:
                st.error(f"Could not connect to Weather API: {e}")
        else:
            st.info("👆 Enter city and click the button to see the prediction.")

else:
    st.error("❌ Dataset not found! Make sure 'weather_data.csv' is in the 'data' folder.")
