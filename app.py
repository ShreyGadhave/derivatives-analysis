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
from utils.display import generate_table_html, prepare_export_with_headers

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
st.title("📊 Derivatives Data Analysis Tool")


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
                
                # Load existing data from sheets
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
                
                # Process the new data
                new_processed = process_data(raw_df, nifty_spot_input)
                
                # Combine with existing data
                if not existing_df.empty:
                    combined_df = pd.concat([new_processed, existing_df], ignore_index=True)
                else:
                    combined_df = new_processed.copy()
                
                # Sort and save
                combined_df = combined_df.sort_values(by=['Date', 'Client Type'], ascending=[False, True])
                
                save_database(combined_df, use_cloud=st.session_state.get('use_cloud_db', False))
                st.session_state['data'] = combined_df
                st.success(f"✅ Data for {len(new_dates)} date(s) processed and saved successfully!")
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