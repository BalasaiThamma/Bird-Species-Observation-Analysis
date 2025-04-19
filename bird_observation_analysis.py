import pandas as pd
import streamlit as st
import plotly.express as px
import os

# Streamlit config
st.set_page_config(page_title="Bird Observation Dashboard", layout="wide")

# Paths to uploaded files
uploaded_files = [
    "C:\\Users\\ASUS\\Desktop\\GUVI Data Science\\Capstone Projects\\GUVI Projects\\Project - 2\\excel_data\\Forest_Data.XLSX",
    "C:\\Users\\ASUS\\Desktop\\GUVI Data Science\\Capstone Projects\\GUVI Projects\\Project - 2\\excel_data\\Grassland_Data.XLSX"
]

# Load all sheets from uploaded Excel files
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

# Clean the data
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

# Save cleaned data to CSV
def save_to_csv(df, filename='cleaned_bird_observations.csv'):
    df.to_csv(filename, index=False)
    return filename

# Dashboard page
def streamlit_dashboard(df):
    st.header("📊 Interactive Bird Observation Dashboard")
    st.sidebar.header("🔍 Filter Options")

    location_options = sorted(df['Location_Type'].dropna().unique())
    year_options = sorted(df['Year'].dropna().unique())
    plot_options = sorted(df['Plot_Name'].dropna().unique())
    common_name_options = sorted(df['Common_Name'].dropna().unique()) if 'Common_Name' in df.columns else []
    observer_options = sorted(df['Observer'].dropna().unique()) if 'Observer' in df.columns else []
    season_options = sorted(df['Season'].dropna().unique())
    source_file_options = sorted(df['Source_File'].dropna().unique())
    admin_unit_options = sorted(df['Admin_Unit_Code'].dropna().unique())

    selected_location = st.sidebar.selectbox("Location Type", ["All"] + location_options)
    selected_year = st.sidebar.selectbox("Year", ["All"] + [str(y) for y in year_options])
    selected_plot = st.sidebar.selectbox("Plot Name", ["All"] + plot_options)
    selected_common_name = st.sidebar.selectbox("Common Name", ["All"] + common_name_options) if common_name_options else "All"
    selected_observer = st.sidebar.selectbox("Observer", ["All"] + observer_options) if observer_options else "All"
    selected_season = st.sidebar.selectbox("Season", ["All"] + season_options)
    selected_source_file = st.sidebar.selectbox("Source File", ["All"] + source_file_options)
    selected_admin_unit = st.sidebar.selectbox("Admin Unit Code", ["All"] + admin_unit_options)

    if st.sidebar.button("Reset Filters"):
        st.experimental_rerun()

    # Filter logic
    if selected_location != "All":
        df = df[df['Location_Type'] == selected_location]
    if selected_year != "All":
        df = df[df['Year'] == int(selected_year)]
    if selected_plot != "All":
        df = df[df['Plot_Name'] == selected_plot]
    if selected_common_name != "All" and 'Common_Name' in df.columns:
        df = df[df['Common_Name'] == selected_common_name]
    if selected_observer != "All" and 'Observer' in df.columns:
        df = df[df['Observer'] == selected_observer]
    if selected_season != "All":
        df = df[df['Season'] == selected_season]
    if selected_source_file != "All":
        df = df[df['Source_File'] == selected_source_file]
    if selected_admin_unit != "All":
        df = df[df['Admin_Unit_Code'] == selected_admin_unit]

    st.subheader("🦜 Unique Bird Species by Habitat")
    species_by_habitat = df.groupby('Location_Type')['Scientific_Name'].nunique().reset_index()
    fig1 = px.bar(species_by_habitat, x='Location_Type', y='Scientific_Name',
                  color='Location_Type', text_auto=True,
                  labels={'Scientific_Name': 'Unique Species'},
                  title="Unique Bird Species per Habitat")
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("📅 Monthly Bird Observations")
    obs_by_month = df['Month'].value_counts().sort_index().reset_index()
    obs_by_month.columns = ['Month', 'Observations']
    fig2 = px.line(obs_by_month, x='Month', y='Observations', markers=True,
                   title="Bird Observations by Month")
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("🏆 Top 10 Observed Species")
    if 'Common_Name' in df.columns:
        top_species = df['Common_Name'].value_counts().head(10).reset_index()
        top_species.columns = ['Common_Name', 'Count']
        fig3 = px.bar(top_species, x='Common_Name', y='Count', text_auto=True,
                      title="Top 10 Observed Species", color='Count')
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.warning("No 'Common_Name' column found in data.")

    st.subheader("🌡 Temperature Distribution")
    if 'Temperature' in df.columns:
        temp_df = df.dropna(subset=['Temperature'])
        fig4 = px.histogram(temp_df, x='Temperature', nbins=30,
                            title="Temperature Distribution During Observations")
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.warning("Temperature data not available.")

    st.subheader("🧍 Observer Trends")
    if 'Observer' in df.columns:
        observer_df = df['Observer'].value_counts().head(10).reset_index()
        observer_df.columns = ['Observer', 'Count']
        fig5 = px.bar(observer_df, x='Observer', y='Count', text_auto=True,
                      title="Top Observers", color='Count')
        st.plotly_chart(fig5, use_container_width=True)
    else:
        st.warning("Observer column not found in data.")

# Raw data viewer page
def show_raw_data(df):
    st.header("📄 Cleaned Data Table")
    st.dataframe(df)

# Overview / Info page
def show_overview(df, csv_path):
    st.header("📘 Dataset Overview")
    st.markdown("This dashboard analyzes bird observations collected from forest and grassland habitats.")
    st.markdown(f"**Total Observations:** {len(df)}")
    st.markdown(f"**Unique Species:** {df['Scientific_Name'].nunique()}")
    st.markdown(f"**Years Covered:** {df['Year'].min()} - {df['Year'].max()}")
    st.markdown(f"**Files Loaded:** {', '.join(df['Source_File'].unique())}")

    # Download button
    with open(csv_path, "rb") as file:
        st.download_button(
            label="📥 Download Cleaned CSV",
            data=file,
            file_name=os.path.basename(csv_path),
            mime="text/csv"
        )

# Main app function with navigation
def main():
    raw_data = load_all_sheets_from_uploaded_excels(uploaded_files)

    if raw_data.empty:
        st.warning("⚠ No data loaded. Check if your Excel sheets have valid data.")
        return

    try:
        cleaned_data = clean_data(raw_data)
        csv_file_path = save_to_csv(cleaned_data)  # Save as CSV

        # Sidebar nav
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
