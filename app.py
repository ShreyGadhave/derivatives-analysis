# Derivatives Data Analysis Tool - Main Application
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import os

# Import configuration
from config import DB_FILE

# Import utility modules
from utils.google_sheets import (
    GSHEETS_AVAILABLE, 
    is_cloud_deployment, 
    get_google_sheets_client, 
    get_or_create_spreadsheet,
    load_from_google_sheets,
    save_to_google_sheets
)
from utils.database import load_database, save_database
from utils.file_processing import read_file_smart, peek_file_for_date
from utils.calculations import fetch_nifty_closing_price, process_data
from utils.display import generate_table_html, prepare_export_with_headers, generate_calendar_html

# --- PAGE CONFIG ---
st.set_page_config(page_title="Derivatives Analysis Tool", layout="wide")

# --- INITIALIZE SESSION STATE ---
if 'use_cloud_db' not in st.session_state:
    st.session_state['use_cloud_db'] = is_cloud_deployment() and GSHEETS_AVAILABLE

if 'data' not in st.session_state:
    st.session_state['data'] = load_database()

if 'auto_nifty_price' not in st.session_state:
    st.session_state['auto_nifty_price'] = None
if 'detected_date' not in st.session_state:
    st.session_state['detected_date'] = None
if 'nifty_status' not in st.session_state:
    st.session_state['nifty_status'] = None
if 'last_uploaded_file' not in st.session_state:
    st.session_state['last_uploaded_file'] = None



# --- MAIN APP UI ---
# Custom CSS for better spacing, branding, and Calendar component
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 3rem; }
    h1 { font-family: 'Segoe UI', Tahoma, sans-serif; font-weight: 600; font-size: 2.2rem; }
    
    /* Calendar Component Styles */
    .calendar-container {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        justify-content: center;
        padding: 5px;
    }
    .month-card {
        background: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        padding: 8px;
        width: 180px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        transition: transform 0.2s;
    }
    .month-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .month-title {
        text-align: center;
        font-weight: 700;
        color: #444;
        margin-bottom: 6px;
        font-size: 0.85em;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        border-bottom: 1px solid #f0f0f0;
        padding-bottom: 4px;
    }
    .days-grid {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 2px;
        text-align: center;
        font-size: 0.7em;
    }
    .day-header {
        color: #999;
        font-weight: 600;
        padding-bottom: 2px;
        font-size: 0.9em;
    }
    .day-cell {
        aspect-ratio: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 3px;
        color: #d0d0d0;
        background: #f8f9fa;
        cursor: default;
        font-size: 0.95em;
    }
    .day-cell.active {
        background-color: #22c55e;
        color: white;
        font-weight: bold;
        box-shadow: 0 1px 2px rgba(34, 197, 94, 0.4);
    }
    .day-cell.active:hover {
        background-color: #16a34a;
        transform: scale(1.1);
    }
    
    /* Make the calendar expander distinct */
    .streamlit-expanderHeader { background-color: #f0f2f6; border-radius: 5px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

col_header, col_cal = st.columns([0.75, 0.25])

with col_header:
    st.title("📊 Derivatives Data Analysis Tool")

with col_cal:
    # Calendar / Status Component
    if not st.session_state['data'].empty and 'Date' in st.session_state['data'].columns:
        unique_dates = st.session_state['data']['Date'].unique()
        day_count = len(unique_dates)
        cal_label = f"📅 {day_count} Active Dates"
        cal_html = generate_calendar_html(unique_dates)
    else:
        cal_label = "📅 0 Active Dates"
        cal_html = generate_calendar_html([])

    # Use Popover if available (floating), else Expander (push down)
    if hasattr(st, "popover"):
        with st.popover(cal_label):
             components.html(cal_html, height=350, scrolling=True)
    else:
        with st.expander(cal_label, expanded=False):
            components.html(cal_html, height=350, scrolling=True)



# --- SIDEBAR (Top: Compact status indicator) ---
if st.session_state.get('use_cloud_db', False):
    st.sidebar.caption("☁️ **Cloud Mode** • Google Sheets")
else:
    st.sidebar.caption("💾 **Local Mode** • CSV File")

# Compact diagnostics expander
with st.sidebar.expander("🔧 Diagnostics", expanded=False):
    has_secrets = False
    try:
        if hasattr(st, 'secrets') and len(st.secrets) > 0:
            has_secrets = 'gcp_service_account' in st.secrets
    except Exception:
        has_secrets = False
    
    st.caption(f"gspread: `{GSHEETS_AVAILABLE}` | secrets: `{has_secrets}` | cloud: `{st.session_state.get('use_cloud_db', False)}`")
    
    if has_secrets:
        try:
            sa_email = st.secrets['gcp_service_account'].get('client_email', 'N/A')
            st.caption(f"SA: `{sa_email[:25]}...`")
        except Exception:
            pass
    
    if st.button("🔄 Test Connection", key="test_gsheets", use_container_width=True):
        if GSHEETS_AVAILABLE and has_secrets:
            try:
                client = get_google_sheets_client()
                if client:
                    spreadsheet = get_or_create_spreadsheet(client)
                    if spreadsheet:
                        st.success(f"✅ Connected: {spreadsheet.title}")
                    else:
                        st.error("❌ Spreadsheet error")
                else:
                    st.error("❌ Auth failed")
            except Exception as e:
                st.error(f"❌ {e}")
        else:
            st.warning("⚠️ Not configured")

st.sidebar.markdown("---")


# --- SIDEBAR: Data Entry ---
st.sidebar.header("Data Entry")
uploaded_file = st.sidebar.file_uploader("Upload Daily Participant File", type=['csv', 'xlsx'])

# Auto-detect date and fetch Nifty price when file is uploaded
if uploaded_file is not None:
    current_file_id = f"{uploaded_file.name}_{uploaded_file.size}"
    
    if st.session_state['last_uploaded_file'] != current_file_id:
        st.session_state['last_uploaded_file'] = current_file_id
        
        with st.sidebar.status("🔍 Detecting date & fetching Nifty price...", expanded=True) as status:
            detected_date, date_source = peek_file_for_date(uploaded_file)
            
            if detected_date is not None:
                st.session_state['detected_date'] = detected_date
                st.write(f"📅 Date detected: **{detected_date.strftime('%d %b %Y')}** (from {date_source})")
                
                st.write("📈 Fetching Nifty 50 closing price...")
                nifty_price, nifty_message = fetch_nifty_closing_price(detected_date)
                
                if nifty_price is not None:
                    st.session_state['auto_nifty_price'] = nifty_price
                    st.session_state['nifty_status'] = ('success', nifty_message)
                    status.update(label="✅ Auto-filled Nifty price!", state="complete")
                else:
                    st.session_state['auto_nifty_price'] = None
                    st.session_state['nifty_status'] = ('warning', nifty_message)
                    status.update(label="⚠️ Could not fetch price", state="error")
            else:
                st.session_state['detected_date'] = None
                st.session_state['auto_nifty_price'] = None
                st.session_state['nifty_status'] = ('warning', "Could not detect date from file")
                status.update(label="⚠️ Date detection failed", state="error")

# Display detected date info
if st.session_state['detected_date'] is not None:
    st.sidebar.markdown(f"**📅 File Date:** {st.session_state['detected_date'].strftime('%d %b %Y')}")

# Nifty price input
default_nifty = st.session_state['auto_nifty_price'] if st.session_state['auto_nifty_price'] is not None else 0.0
nifty_spot_input = st.sidebar.number_input(
    "Nifty Spot Price", 
    value=default_nifty, 
    step=0.01,
    format="%.2f",
    help="Auto-suggested from yfinance API. You can manually edit if needed."
)

# Show status message for Nifty fetch
if st.session_state['nifty_status'] is not None:
    status_type, status_msg = st.session_state['nifty_status']
    if status_type == 'success':
        st.sidebar.success(status_msg)
    else:
        st.sidebar.warning(f"{status_msg}. Please enter manually.")
elif uploaded_file is None:
    st.sidebar.info("💡 Upload a file to auto-detect Nifty price")


# --- SUBMIT BUTTON ---
if st.sidebar.button("Submit & Process"):
    if uploaded_file is not None:
        with st.spinner("Reading and Processing..."):
            raw_df = read_file_smart(uploaded_file)
            
            if raw_df is not None:
                # Clean new raw data dates
                raw_df['Date'] = pd.to_datetime(raw_df['Date'], dayfirst=True, errors='coerce')
                new_dates = raw_df['Date'].dropna().unique()
                
                # Load existing data from sheets (includes raw columns)
                existing_df = pd.DataFrame()
                
                if st.session_state.get('use_cloud_db', False):
                    existing_df = load_from_google_sheets()
                    if existing_df is None:
                        existing_df = pd.DataFrame()
                    elif not existing_df.empty:
                        existing_df['Date'] = pd.to_datetime(existing_df['Date'], errors='coerce')
                elif os.path.exists(DB_FILE):
                    existing_df = pd.read_csv(DB_FILE)
                    existing_df['Date'] = pd.to_datetime(existing_df['Date'])
                
                # Check if date already exists
                if not existing_df.empty and 'Date' in existing_df.columns:
                    existing_dates = existing_df['Date'].dropna().unique()
                    duplicate_dates = [d for d in new_dates if d in existing_dates]
                    
                    if duplicate_dates:
                        date_strs = [pd.to_datetime(d).strftime('%d.%m.%Y') for d in duplicate_dates]
                        st.error(f"⚠️ Data for these dates already exists: **{', '.join(date_strs)}**. Please remove these dates from your file or delete existing data first.")
                        st.stop()
                
                # Combine new raw data with existing raw data for proper calculations
                from config import RAW_DATA_COLUMNS
                
                if not existing_df.empty:
                    # Get raw columns from existing data
                    existing_raw_cols = [c for c in RAW_DATA_COLUMNS if c in existing_df.columns]
                    
                    if existing_raw_cols:
                        # Extract raw data from existing
                        existing_raw = existing_df[existing_raw_cols].copy()
                        
                        # Align columns
                        for col in raw_df.columns:
                            if col not in existing_raw.columns:
                                existing_raw[col] = float('nan')
                        for col in existing_raw.columns:
                            if col not in raw_df.columns:
                                raw_df[col] = float('nan')
                        
                        # Combine: new raw + existing raw
                        combined_raw = pd.concat([raw_df, existing_raw], ignore_index=True)
                    else:
                        combined_raw = raw_df.copy()
                else:
                    combined_raw = raw_df.copy()
                
                # Process ALL raw data together (enables proper diff calculations)
                combined_df = process_data(combined_raw, nifty_spot_input)
                
                # Sort and save
                combined_df = combined_df.sort_values(by=['Date', 'Client Type'], ascending=[False, True])
                
                save_database(combined_df, use_cloud=st.session_state.get('use_cloud_db', False))
                st.session_state['data'] = combined_df
                st.success(f"✅ Data for {len(new_dates)} date(s) processed and saved successfully!")
                st.rerun()
            else:
                st.error("❌ Could not find 'Date' or 'Client Type' columns. Check file format.")
    else:
        st.error("Please upload a file first.")



# --- DISPLAY RESULTS ---
if not st.session_state['data'].empty:
    st.divider()
    st.header("📈 Complete Historical Data")
    st.caption("Newest data appears at the top. When you upload new data, it will be added at the top and older data shifts down.")
    
    # Prepare display dataframe
    display_df = st.session_state['data'].copy()
    display_df = display_df.sort_values(by=['Date', 'Client Type'], ascending=[False, True])
    display_df['Date'] = pd.to_datetime(display_df['Date']).dt.strftime('%d.%m.%y')
    
    # Generate and display HTML table
    table_html = generate_table_html(display_df)
    components.html(table_html, height=720, scrolling=False)
    
    # Show summary stats
    unique_dates = display_df['Date'].nunique()
    total_rows = len(display_df)
    st.info(f"📊 Showing **{total_rows}** rows across **{unique_dates}** trading dates")
    
    # Download Button - use formatted export data with headers
    st.divider()
    import csv
    import io
    
    all_rows, _ = prepare_export_with_headers(st.session_state['data'])
    
    # Create CSV with multi-row headers
    output = io.StringIO()
    writer = csv.writer(output)
    for row in all_rows:
        writer.writerow(row)
    csv_content = output.getvalue().encode('utf-8')
    
    st.download_button(
        label="📥 Download Full Historical Database (CSV)",
        data=csv_content,
        file_name='derivative_data_db.csv',
        mime='text/csv',
    )
else:
    st.warning("📂 Database is empty. Please upload data.")