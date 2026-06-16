import pandas as pd
import streamlit as st
import os
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Ultimate F1 Historical Hub", layout="wide")
st.title("🏎️ All-Time Formula 1 Analytics Hub")

import os

if os.path.exists('results.csv'):
    base = ''
elif os.path.exists('Data/results.csv'):
    base = 'Data/'
else:
    base = './Data/'

results = pd.read_csv(f'{base}results.csv')
drivers = pd.read_csv(f'{base}drivers.csv')
constructors = pd.read_csv(f'{base}constructors.csv')
races = pd.read_csv(f'{base}races.csv')

# Data Type Cleaning
results['positionOrder'] = pd.to_numeric(results['positionOrder'], errors='coerce')
races['year'] = pd.to_numeric(races['year'], errors='coerce')

# Merge Datasets for Master Query Frame
master_df = pd.merge(results, races[['raceId', 'year', 'name']], on='raceId')
master_df = pd.merge(master_df, drivers[['driverId', 'forename', 'surname', 'nationality']], on='driverId', suffixes=('', '_driver'))
master_df = pd.merge(master_df, constructors[['constructorId', 'name', 'nationality']], on='constructorId', suffixes=('', '_team'))
master_df['Driver Name'] = master_df['forename'] + ' ' + master_df['surname']

# --- SIDEBAR FILTERS ---
st.sidebar.header("Dashboard Controls")
view_option = st.sidebar.radio("Select Leaderboard View:", ["Drivers (All-Time Wins)", "Constructors (Team Wins)"])

# Dynamic Era Year Range Slider
min_year = int(master_df['year'].min())
max_year = int(master_df['year'].max())
selected_years = st.sidebar.slider("Select Era Timeline:", min_year, max_year, (min_year, max_year))

# Filter dataset by year selection
filtered_df = master_df[(master_df['year'] >= selected_years[0]) & (master_df['year'] <= selected_years[1])]

# --- MAIN LEADERBOARD TABS ---
tab1, tab2 = st.tabs(["📊 Main Leaderboards", "⚔️ Driver Head-to-Head Comparison"])

with tab1:
    if view_option == "Drivers (All-Time Wins)":
        wins_df = filtered_df[filtered_df['positionOrder'] == 1].groupby('Driver Name').size().reset_index(name='Wins')
        top_data = wins_df.sort_values(by='Wins', ascending=False).head(10)
        
        fig = px.bar(top_data, x='Driver Name', y='Wins', 
                     title=f"Top Driver Victories ({selected_years[0]} - {selected_years[1]})",
                     color='Wins', color_continuous_scale='Reds', template="plotly_dark")
    else:
        wins_df = filtered_df[filtered_df['positionOrder'] == 1].groupby('name_team').size().reset_index(name='Wins')
        top_data = wins_df.sort_values(by='Wins', ascending=False).head(10)
        top_data.rename(columns={'name_team': 'Team Name'}, inplace=True)
        
        fig = px.bar(top_data, x='Team Name', y='Wins', 
                     title=f"Top Team Victories ({selected_years[0]} - {selected_years[1]})",
                     color='Wins', color_continuous_scale='Blues', template="plotly_dark")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.subheader("Leaderboard Standings")
        st.dataframe(top_data, hide_index=True, use_container_width=True)

with tab2:
    st.subheader("Driver Career Profile Matchup")
    
    # Calculate complete lifetime metrics per driver
    all_drivers = sorted(master_df['Driver Name'].unique())
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        driver1 = st.selectbox("Select Driver 1:", all_drivers, index=all_drivers.index("Michael Schumacher") if "Michael Schumacher" in all_drivers else 0)
    with col_d2:
        driver2 = st.selectbox("Select Driver 2:", all_drivers, index=all_drivers.index("Lewis Hamilton") if "Lewis Hamilton" in all_drivers else 1)
        
    def get_driver_profile(name):
        d_sub = master_df[master_df['Driver Name'] == name]
        starts = len(d_sub)
        wins = len(d_sub[d_sub['positionOrder'] == 1])
        podiums = len(d_sub[d_sub['positionOrder'] <= 3])
        points = d_sub['points'].sum()
        return [wins, podiums, starts, points]

    stats1 = get_driver_profile(driver1)
    stats2 = get_driver_profile(driver2)
    
    # Render Metric Comparison Cards
    metrics_labels = ["Wins", "Podiums", "Total Race Starts", "Career Points"]
    
    for i, label in enumerate(metrics_labels):
        m_col1, m_col2 = st.columns(2)
        m_col1.metric(f"{driver1} - {label}", f"{stats1[i]:.1f}" if label == "Career Points" else int(stats1[i]))
        m_col2.metric(f"{driver2} - {label}", f"{stats2[i]:.1f}" if label == "Career Points" else int(stats2[i]))
        st.markdown("---")
