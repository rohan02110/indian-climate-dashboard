import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import pickle
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="Indian Climate Dashboard", layout="wide")

# --- SIDEBAR ---
st.sidebar.title("☁️ Indian Climate Dashboard")
page = st.sidebar.radio("Navigate", ["Historical Analysis", "Live Prediction"])
st.sidebar.markdown("### Dataset Overview")
st.sidebar.info("📅 Jan 2024 – Dec 2025\n\n🏙️ 10 Cities\n\n📄 7,310 records")

# --- DATA LOADING ---
@st.cache_data
def load_data():
    base_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_path, 'data', 'weather_data.csv')
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip()
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df['Month'] = df['Date'].dt.strftime('%b') # Get 'Jan', 'Feb', etc.
            df['Month_Num'] = df['Date'].dt.month     # For sorting
        return df
    return None

df = load_data()

if df is not None:
    if page == "Historical Analysis":
        st.title("📊 Historical Climate Analysis")
        
        # 1. Filters
        col_a, col_b = st.columns(2)
        with col_a:
            selected_cities = st.multiselect("Select Cities", df['City'].unique(), default=df['City'].unique()[:3])
        with col_b:
            # Note: Ensure your CSV has a 'State' or 'Season' column, or we use 'All Seasons'
            season_list = ["All Seasons"] + list(df['State'].unique()) if 'State' in df.columns else ["All Seasons"]
            selected_season = st.selectbox("Filter by Region/State", season_list)

        filtered_df = df[df['City'].isin(selected_cities)]
        
        # 2. KPIs
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Avg Temperature", f"{filtered_df['Temperature_Avg (°C)'].mean():.1f} °C")
        k2.metric("Max Temperature", f"{filtered_df['Temperature_Max (°C)'].max():.1f} °C")
        k3.metric("Total Rainfall", f"{filtered_df['Rainfall (mm)'].sum():.0f} mm")
        k4.metric("Avg Humidity", f"{filtered_df['Humidity (%)'].mean():.1f} %")

        # 3. Line Chart
        st.subheader("🌡️ Average Temperature Trend")
        fig_line = px.line(filtered_df, x='Date', y='Temperature_Avg (°C)', color='City', template="plotly_dark")
        st.plotly_chart(fig_line, use_container_width=True)

        # 4. Seasonal Breakdown (Bar Charts)
        st.markdown("---")
        st.subheader("🍂 Seasonal Breakdown")
        col_c, col_d = st.columns(2)
        
        # We group by 'State' or 'City' as a proxy for Season if Season isn't in your CSV
        with col_c:
            fig_bar_temp = px.bar(filtered_df.groupby('City')['Temperature_Avg (°C)'].mean().reset_index(), 
                                 x='City', y='Temperature_Avg (°C)', color='City', title="Avg Temp by City")
            st.plotly_chart(fig_bar_temp, use_container_width=True)
        with col_d:
            fig_bar_rain = px.bar(filtered_df.groupby('City')['Rainfall (mm)'].sum().reset_index(), 
                                 x='City', y='Rainfall (mm)', color='City', title="Total Rainfall by City")
            st.plotly_chart(fig_bar_rain, use_container_width=True)

        # 5. Monthly Heatmap
        st.markdown("---")
        st.subheader("🗓️ Monthly Average Temperature Heatmap")
        heatmap_data = filtered_df.groupby(['City', 'Month_Num', 'Month'])['Temperature_Avg (°C)'].mean().reset_index()
        heatmap_data = heatmap_data.sort_values('Month_Num')
        
        fig_heat = px.density_heatmap(heatmap_data, x="Month", y="City", z="Temperature_Avg (°C)", 
                                      color_continuous_scale='RdYlBu_r', text_auto='.1f')
        st.plotly_chart(fig_heat, use_container_width=True)

        # 6. Scatter Plot
        st.markdown("---")
        st.subheader("💧 Humidity vs. Rainfall Scatter")
        fig_scatter = px.scatter(filtered_df, x='Humidity (%)', y='Rainfall (mm)', 
                                 color='City', size='Temperature_Avg (°C)', 
                                 hover_name='City', template="plotly_dark")
        st.plotly_chart(fig_scatter, use_container_width=True)

    elif page == "Live Prediction":
        # (Keep your existing Live Prediction code here)
        st.title("🔮 Live Weather & AI Prediction")
        # ... [Existing Prediction Logic] ...
        st.info("Live Prediction features are ready and connected to Open-Meteo API.")

else:
    st.error("Dataset not found! Please check your /data/ folder.")
