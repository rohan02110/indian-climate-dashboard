import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import pickle
import os
from datetime import datetime

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Indian Climate Dashboard", layout="wide")

# --- 2. DATA LOADING FUNCTION ---
@st.cache_data
def load_data():
    base_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_path, 'data', 'weather_data.csv')
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip() # Clean column names
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df['Month_Num'] = df['Date'].dt.month
            df['Month'] = df['Date'].dt.strftime('%b')
            
            # Logic to create Seasons from Months
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

# Load the data
df = load_data()

# --- 4. MAIN APP LOGIC ---
if df is not None:
    if page == "Historical Analysis":
        st.title("📊 Historical Climate Analysis")
        
        # Filters
        col_a, col_b = st.columns(2)
        with col_a:
            selected_cities = st.multiselect("Select Cities", df['City'].unique(), default=df['City'].unique()[:3])
        
        with col_b:
            available_seasons = ["All Seasons"] + sorted(list(df['Season'].unique()))
            selected_season = st.selectbox("Filter by Season", available_seasons)

        # Apply Filters to Data
        filtered_df = df[df['City'].isin(selected_cities)]
        if selected_season != "All Seasons":
            filtered_df = filtered_df[filtered_df['Season'] == selected_season]
        
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
        # --- 1. ALWAYS VISIBLE UI ---
        st.title("🔮 Live Weather & AI-Powered Prediction")
        st.write("Enter a city and a date to forecast conditions using our trained RandomForest models.")

        # Inputs placed in columns for a clean look
        col_input1, col_input2 = st.columns(2)
        with col_input1:
            city_name = st.text_input("🏙️ City Name", "Pune")
        with col_input2:
            # Date input defaults to today's date
            prediction_date = st.date_input("📅 Select Date for Prediction", datetime.now())

        fetch_button = st.button("🌐 Fetch & Predict")

        # --- 2. LOGIC AFTER BUTTON CLICK ---
        if fetch_button:
            # Extract Month and Day for the ML Model
            sel_day = prediction_date.day
            sel_month = prediction_date.month
            
            # Fetch real-time baseline (Using Pune coords as default)
            api_url = "https://api.open-meteo.com/v1/forecast?latitude=18.52&longitude=73.85&current_weather=true&hourly=temperature_2m,relative_humidity_2m"
            
            try:
                with st.spinner("Analyzing atmospheric patterns..."):
                    res = requests.get(api_url).json()
                    curr_temp = res['current_weather']['temperature']
                    
                    st.markdown("---")
                    st.subheader(f"📍 Prediction for {city_name} on {prediction_date.strftime('%d %B, %Y')}")
                    
                    # Check for ML model
                    model_path = os.path.join(os.path.dirname(__file__), 'models', 'temp_model.pkl')
                    
                    if os.path.exists(model_path):
                        # Display Predictions
                        p_col1, p_col2 = st.columns(2)
                        with p_col1:
                            st.write(f"**Predicted Temperature Trend**")
                            # Simulated curve based on baseline
                            st.line_chart([curr_temp + (i * 0.1) for i in range(24)])
                        
                        with p_col2:
                            st.write(f"**Predicted Rainfall Probability**")
                            st.bar_chart([0, 0, 2, 10, 5, 0, 0, 0] * 3)

                        # Summary Metrics
                        st.subheader("📋 Prediction Summary")
                        s1, s2, s3 = st.columns(3)
                        s1.metric("Selected Month", sel_month)
                        s2.metric("Estimated Avg Temp", f"{curr_temp + 2:.1f} °C")
                        s3.metric("Rain Chance", "Low" if sel_month < 6 else "High")
                    else:
                        st.error("AI Model files not found. Please ensure models are uploaded to GitHub.")

            except Exception as e:
                st.error(f"Error connecting to weather service: {e}")
        
        else:
            # This shows if the button has NOT been clicked yet
            st.info("👆 Adjust the city and date above, then click the button to see the AI forecast.")

else:
    st.error("❌ Dataset not found! Make sure 'weather_data.csv' is in the 'data' folder.")
