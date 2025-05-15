import pandas as pd
import streamlit as st
import plotly.express as px
import sqlite3
import os

# Streamlit config
st.set_page_config(page_title="Bird Observation Dashboard", layout="wide")

# Paths to uploaded files
uploaded_files = [
    "C:\\Users\\ASUS\\Desktop\\GUVI Data Science\\Capstone Projects\\GUVI Projects\\Project - 2\\excel_data\\Forest_Data.XLSX",
    "C:\\Users\\ASUS\\Desktop\\GUVI Data Science\\Capstone Projects\\GUVI Projects\\Project - 2\\excel_data\\Grassland_Data.XLSX"
]

def load_all_sheets_from_uploaded_excels(file_paths):
    all_data = pd.DataFrame()
    for file_path in file_paths:
        file = os.path.basename(file_path)
        xls = pd.ExcelFile(file_path)
        for sheet in xls.sheet_names:
            df = xls.parse(sheet)
            if df.empty:
                continue
            df['Admin_Unit_Code'] = sheet
            df['Source_File'] = file
            all_data = pd.concat([all_data, df], ignore_index=True)
    return all_data

def clean_data(df):
    required_columns = ["Scientific_Name", "Location_Type", "Year", "Plot_Name"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        st.error(f"❌ Missing required columns in data: {missing_columns}")
        raise KeyError(f"Missing required columns in data: {missing_columns}")

    df.drop_duplicates(inplace=True)
    df.dropna(subset=required_columns, inplace=True)

    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Year'] = df['Date'].dt.year.fillna(df['Year'])
        df['Month'] = df['Date'].dt.month
    else:
        df['Date'] = pd.NaT
        df['Month'] = pd.NA

    df['Season'] = df['Month'].map({
        12: 'Winter', 1: 'Winter', 2: 'Winter',
        3: 'Spring', 4: 'Spring', 5: 'Spring',
        6: 'Summer', 7: 'Summer', 8: 'Summer',
        9: 'Fall', 10: 'Fall', 11: 'Fall'
    })
    return df

def save_to_csv(df, filename='cleaned_bird_observations.csv'):
    df.to_csv(filename, index=False)
    return filename

def save_to_sqlite(df, db_name='bird_data.db'):
    conn = sqlite3.connect(db_name)
    df.to_sql('bird_observations', conn, if_exists='replace', index=False)
    conn.close()

def run_sql_filters(location, species, year):
    query = "SELECT * FROM bird_observations WHERE 1=1"
    params = []
    if location != "All":
        query += " AND Location_Type = ?"
        params.append(location)
    if species != "All":
        query += " AND Scientific_Name = ?"
        params.append(species)
    if year != "All":
        query += " AND Year = ?"
        params.append(int(year))

    conn = sqlite3.connect('bird_data.db')
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def get_top_areas_and_species():
    conn = sqlite3.connect('bird_data.db')
    area_query = "SELECT Location_Type, COUNT(*) as Count FROM bird_observations GROUP BY Location_Type ORDER BY Count DESC LIMIT 10"
    species_query = "SELECT Scientific_Name, COUNT(*) as Count FROM bird_observations GROUP BY Scientific_Name ORDER BY Count DESC LIMIT 10"
    top_areas = pd.read_sql_query(area_query, conn)
    top_species = pd.read_sql_query(species_query, conn)
    conn.close()
    return top_areas, top_species

def streamlit_dashboard(df):
    st.header("📊 Interactive Bird Observation Dashboard")
    st.sidebar.header("🔍 Filter Options")

    location_options = sorted(df['Location_Type'].dropna().unique())
    year_options = sorted(df['Year'].dropna().unique())
    species_options = sorted(df['Scientific_Name'].dropna().unique())

    selected_location = st.sidebar.selectbox("Location Type", ["All"] + location_options)
    selected_species = st.sidebar.selectbox("Scientific Name", ["All"] + species_options)
    selected_year = st.sidebar.selectbox("Year", ["All"] + [str(y) for y in year_options])

    filtered_df = run_sql_filters(selected_location, selected_species, selected_year)

    st.subheader("🦜 Filtered Bird Observations")
    st.write(f"Showing {len(filtered_df)} records")
    st.dataframe(filtered_df)

    st.subheader("📍 Top 10 Observation Areas")
    top_areas, top_species = get_top_areas_and_species()
    fig1 = px.bar(top_areas, x='Location_Type', y='Count', title='Top 10 Areas by Observation Count')
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("🔝 Top 10 Bird Species")
    fig2 = px.bar(top_species, x='Scientific_Name', y='Count', title='Top 10 Observed Bird Species')
    st.plotly_chart(fig2, use_container_width=True)

def show_raw_data(df):
    st.header("📄 Cleaned Data Table")
    st.dataframe(df)

def show_overview(df, csv_path):
    st.header("📘 Dataset Overview")
    st.markdown("This dashboard analyzes bird observations collected from forest and grassland habitats.")
    st.markdown(f"**Total Observations:** {len(df)}")
    st.markdown(f"**Unique Species:** {df['Scientific_Name'].nunique()}")
    st.markdown(f"**Years Covered:** {df['Year'].min()} - {df['Year'].max()}")
    st.markdown(f"**Files Loaded:** {', '.join(df['Source_File'].unique())}")

    with open(csv_path, "rb") as file:
        st.download_button(
            label="📥 Download Cleaned CSV",
            data=file,
            file_name=os.path.basename(csv_path),
            mime="text/csv"
        )

def main():
    raw_data = load_all_sheets_from_uploaded_excels(uploaded_files)

    if raw_data.empty:
        st.warning("⚠ No data loaded. Check if your Excel sheets have valid data.")
        return

    try:
        cleaned_data = clean_data(raw_data)
        csv_file_path = save_to_csv(cleaned_data)
        save_to_sqlite(cleaned_data)

        st.sidebar.title("📂 Navigation")
        page = st.sidebar.radio("Go to", ["Overview", "Dashboard", "Raw Data"])

        if page == "Overview":
            show_overview(cleaned_data, csv_file_path)
        elif page == "Dashboard":
            streamlit_dashboard(cleaned_data)
        elif page == "Raw Data":
            show_raw_data(cleaned_data)

    except KeyError:
        st.stop()

if __name__ == "__main__":
    main()
