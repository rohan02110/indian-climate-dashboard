import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import pickle
import os

# 1. Load Dataset
# Assuming your CSV has columns: 'City', 'Month', 'Day', 'Humidity', 'Temp', 'Rainfall'
def train_and_save_model():
    if not os.path.exists('data/weather_data.csv'):
        print("Error: Please place weather_data.csv in the /data folder!")
        return

    df = pd.read_csv('data/weather_data.csv')

    # Simple Preprocessing: Convert categorical city names to numbers
    df['City_Code'] = df['City'].astype('category').cat.codes
    
    # Features (X) and Targets (y)
    X = df[['City_Code', 'Month', 'Day', 'Humidity']]
    y_temp = df['Temp']
    y_rain = df['Rainfall']

    # Train Model for Temperature
    model_temp = RandomForestRegressor(n_estimators=100)
    model_temp.fit(X, y_temp)

    # Train Model for Rainfall
    model_rain = RandomForestRegressor(n_estimators=100)
    model_rain.fit(X, y_rain)

    # Save the models to the /models folder
    if not os.path.exists('models'): os.makedirs('models')
    
    with open('models/temp_model.pkl', 'wb') as f:
        pickle.dump(model_temp, f)
    with open('models/rain_model.pkl', 'wb') as f:
        pickle.dump(model_rain, f)
        
    print("Models trained and saved successfully!")

if __name__ == "__main__":
    train_and_save_model()