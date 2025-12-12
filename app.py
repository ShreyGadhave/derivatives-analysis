import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import os
import yfinance as yf
from datetime import timedelta

# --- CONFIGURATION ---
DB_FILE = 'derivative_data_db.csv'  # Local fallback file

# Try to import Google Sheets libraries (for cloud deployment)
try:
    from google.oauth2.service_account import Credentials
    import gspread
    from gspread.exceptions import SpreadsheetNotFound, APIError
    GSHEETS_AVAILABLE = True
    print("✅ Google Sheets libraries loaded successfully")
except ImportError:
    GSHEETS_AVAILABLE = False
    SpreadsheetNotFound = Exception  # Fallback to generic exception
    APIError = Exception
    print("⚠️ Google Sheets libraries not available")

st.set_page_config(page_title="Derivatives Analysis Tool", layout="wide")

# --- CHECK FOR CLOUD DEPLOYMENT ---
def is_cloud_deployment():
    """Check if we're running on Streamlit Cloud with secrets configured."""
    try:
        # First check if secrets exist and are not empty
        if hasattr(st, 'secrets') and len(st.secrets) > 0:
            if 'gcp_service_account' in st.secrets:
                print("✅ Streamlit secrets detected")
                return True
        print("⚠️ No Streamlit secrets found")
        return False
    except Exception as e:
        print(f"⚠️ Error checking secrets: {e}")
        return False

# Initialize session state for cloud mode
if 'use_cloud_db' not in st.session_state:
    st.session_state['use_cloud_db'] = is_cloud_deployment() and GSHEETS_AVAILABLE

# --- GOOGLE SHEETS FUNCTIONS ---

@st.cache_resource
def get_google_sheets_client():
    """Initialize Google Sheets client using Streamlit secrets."""
    try:
        if not GSHEETS_AVAILABLE:
            print("❌ gspread not available")
            return None
        
        # Safely check for secrets
        has_secrets = False
        try:
            if hasattr(st, 'secrets') and len(st.secrets) > 0:
                has_secrets = 'gcp_service_account' in st.secrets
        except Exception:
            has_secrets = False
        
        if not has_secrets:
            print("❌ No gcp_service_account in secrets")
            return None
        
        credentials = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
        )
        client = gspread.authorize(credentials)
        print("✅ Google Sheets client authorized successfully")
        return client
    except Exception as e:
        print(f"❌ Error creating Google Sheets client: {e}")
        st.error(f"Google Sheets connection failed: {e}")
        return None

def get_or_create_spreadsheet(client):
    """Get or create the spreadsheet."""
    try:
        spreadsheet_name = st.secrets.get("spreadsheet_name", "DerivativesDB")
        
        try:
            spreadsheet = client.open(spreadsheet_name)
            print(f"✅ Opened existing spreadsheet: {spreadsheet_name}")
        except SpreadsheetNotFound:
            spreadsheet = client.create(spreadsheet_name)
            print(f"✅ Created new spreadsheet: {spreadsheet_name}")
            
            # Share with user if email provided
            if 'share_email' in st.secrets:
                spreadsheet.share(st.secrets['share_email'], perm_type='user', role='writer')
                print(f"✅ Shared spreadsheet with: {st.secrets['share_email']}")
        
        return spreadsheet
    except APIError as e:
        print(f"❌ Google API Error: {e}")
        st.error(f"Google API Error: {e}")
        return None
    except Exception as e:
        print(f"❌ Error with spreadsheet: {e}")
        st.error(f"Spreadsheet error: {e}")
        return None

def load_from_google_sheets():
    """Load data from Google Sheets."""
    try:
        client = get_google_sheets_client()
        if client is None:
            return None
        
        spreadsheet = get_or_create_spreadsheet(client)
        if spreadsheet is None:
            return None
        
        worksheet = spreadsheet.sheet1
        data = worksheet.get_all_records()
        
        if not data:
            print("📊 Google Sheet is empty")
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
        
        print(f"✅ Loaded {len(df)} rows from Google Sheets")
        return df
        
    except Exception as e:
        print(f"❌ Error loading from Google Sheets: {e}")
        st.error(f"Error loading from Google Sheets: {e}")
        return None

def save_to_google_sheets(df):
    """Save DataFrame to Google Sheets."""
    try:
        client = get_google_sheets_client()
        if client is None:
            print("❌ No client for saving")
            return False
        
        spreadsheet = get_or_create_spreadsheet(client)
        if spreadsheet is None:
            return False
        
        worksheet = spreadsheet.sheet1
        
        # Convert DataFrame to list of lists
        df_copy = df.copy()
        if 'Date' in df_copy.columns:
            df_copy['Date'] = df_copy['Date'].astype(str)
        
        # Clear and write
        worksheet.clear()
        
        # Write headers first
        headers = df_copy.columns.tolist()
        worksheet.append_row(headers)
        
        # Write data in batches
        data_rows = df_copy.values.tolist()
        if len(data_rows) > 0:
            # Use batch update for better performance
            worksheet.append_rows(data_rows)
        
        print(f"✅ Saved {len(df)} rows to Google Sheets")
        return True
        
    except Exception as e:
        print(f"❌ Error saving to Google Sheets: {e}")
        st.error(f"Error saving to Google Sheets: {e}")
        return False

# --- DATABASE FUNCTIONS ---

def load_database():
    """Loads the historical data - tries Google Sheets first, then local CSV."""
    
    # Try Google Sheets first (for cloud deployment)
    if st.session_state.get('use_cloud_db', False):
        print("🔄 Attempting to load from Google Sheets...")
        df = load_from_google_sheets()
        if df is not None:
            return df
        print("⚠️ Falling back to local CSV")
    
    # Fallback to local CSV
    st.session_state['use_cloud_db'] = False
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            df['Date'] = pd.to_datetime(df['Date'])
            print(f"✅ Loaded {len(df)} rows from local CSV")
            return df
        except Exception as e:
            print(f"❌ Error loading local CSV: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

def save_to_database(new_df):
    """Merges new data with existing database and saves it."""
    
    # 1. Load existing data
    if st.session_state.get('use_cloud_db', False):
        old_df = load_from_google_sheets()
        if old_df is None:
            old_df = pd.DataFrame()
    elif os.path.exists(DB_FILE):
        old_df = pd.read_csv(DB_FILE)
        old_df['Date'] = pd.to_datetime(old_df['Date'])
    else:
        old_df = pd.DataFrame()

    # 2. Combine Data
    if old_df.empty:
        combined_df = new_df
    else:
        new_dates = new_df['Date'].unique()
        old_df_filtered = old_df[~old_df['Date'].isin(new_dates)]
        combined_df = pd.concat([old_df_filtered, new_df], ignore_index=True)

    # 3. Sort and Save
    combined_df = combined_df.sort_values(by=['Date', 'Client Type'], ascending=[False, True])
    
    # Save to appropriate storage
    if st.session_state.get('use_cloud_db', False):
        success = save_to_google_sheets(combined_df)
        if success:
            st.success("✅ Data saved to Google Sheets!")
        else:
            st.error("❌ Failed to save to Google Sheets")
    else:
        combined_df.to_csv(DB_FILE, index=False)
        st.success("✅ Data saved to local CSV")
    
    return combined_df

import re
from datetime import datetime

def extract_date_from_title(title_text):
    """
    Extracts date from NSE title row like:
    'Participant wise Open Interest (no. of contracts) in Equity Derivatives as on Dec 05, 2025'
    """
    # Pattern to match "as on Mon DD, YYYY" format
    pattern = r'as on\s+([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})'
    match = re.search(pattern, title_text, re.IGNORECASE)
    if match:
        month_str, day, year = match.groups()
        try:
            date_str = f"{month_str} {day}, {year}"
            return pd.to_datetime(date_str, format='%b %d, %Y')
        except:
            pass
    return None

def extract_date_from_filename(filename):
    """
    Extracts date from filename like 'fao_participant_oi_05122025.csv'
    The format is DDMMYYYY
    """
    # Pattern to match DDMMYYYY at end of filename
    pattern = r'(\d{2})(\d{2})(\d{4})'
    match = re.search(pattern, filename)
    if match:
        day, month, year = match.groups()
        try:
            return pd.to_datetime(f"{day}/{month}/{year}", format='%d/%m/%Y')
        except:
            pass
    return None

def read_file_smart(uploaded_file):
    """
    Attempts to read the file by handling potential Title rows.
    Handles NSE's format where date is in title row, not as a column.
    Returns a cleaned DataFrame or None if it fails.
    """
    try:
        extracted_date = None
        
        # First, try to read the title row to extract date
        uploaded_file.seek(0)
        if uploaded_file.name.endswith('.csv'):
            # Read just the first row to get the title
            first_row = pd.read_csv(uploaded_file, nrows=1, header=None)
            if not first_row.empty:
                title_text = str(first_row.iloc[0, 0])
                extracted_date = extract_date_from_title(title_text)
        
        # If date not found in title, try to extract from filename
        if extracted_date is None:
            extracted_date = extract_date_from_filename(uploaded_file.name)
        
        # Attempt 1: Standard read (Header in Row 0)
        uploaded_file.seek(0)
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        df.columns = df.columns.str.strip() # Clean whitespace

        # Check if 'Date' exists
        if 'Date' in df.columns:
            return df

        # Attempt 2: Header in Row 1 (Skipping Title Row) - This is NSE's format
        uploaded_file.seek(0)
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, header=1)
        else:
            df = pd.read_excel(uploaded_file, header=1)
        
        df.columns = df.columns.str.strip()
        
        # Remove any completely empty rows
        df = df.dropna(how='all')

        # If we have 'Client Type' column and extracted date, add Date column
        if 'Client Type' in df.columns:
            if extracted_date is not None:
                df['Date'] = extracted_date
                return df
            else:
                # Attempt 3: If 'Date' is still missing, maybe it's the first unnamed column?
                # Sometimes header is 'Unnamed: 0' if the cell was blank in Excel
                cols = list(df.columns)
                client_idx = cols.index('Client Type')
                if client_idx > 0:
                    # Rename the previous column to Date
                    col_to_rename = cols[client_idx - 1]
                    df = df.rename(columns={col_to_rename: 'Date'})
                    return df
        
        if 'Date' in df.columns:
            return df
                
        return None

    except Exception as e:
        st.error(f"Error parsing file: {e}")
        return None

def peek_file_for_date(uploaded_file):
    """
    Peeks into the uploaded file to detect the date without fully processing it.
    Handles files with title rows (like NSE format) and various date formats.
    Returns: (detected_date, date_source) tuple or (None, None) if not found.
    """
    try:
        uploaded_file.seek(0)
        
        # Method 1: Try to extract date from filename first
        date_from_filename = extract_date_from_filename(uploaded_file.name)
        if date_from_filename:
            return date_from_filename, "filename"
        
        # Method 2: Try to extract from title row (NSE format)
        uploaded_file.seek(0)
        if uploaded_file.name.endswith('.csv'):
            first_row = pd.read_csv(uploaded_file, nrows=1, header=None)
            if not first_row.empty:
                title_text = str(first_row.iloc[0, 0])
                date_from_title = extract_date_from_title(title_text)
                if date_from_title:
                    return date_from_title, "title_row"
        
        # Method 3: Try to find Date column in data
        uploaded_file.seek(0)
        if uploaded_file.name.endswith('.csv'):
            # Try header at row 0
            df = pd.read_csv(uploaded_file, nrows=5)
            df.columns = df.columns.str.strip()
            
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
                valid_dates = df['Date'].dropna()
                if not valid_dates.empty:
                    return valid_dates.iloc[0], "date_column"
            
            # Try header at row 1 (skipping title)
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, header=1, nrows=5)
            df.columns = df.columns.str.strip()
            
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
                valid_dates = df['Date'].dropna()
                if not valid_dates.empty:
                    return valid_dates.iloc[0], "date_column"
        else:
            # Excel file
            df = pd.read_excel(uploaded_file, nrows=5)
            df.columns = df.columns.str.strip()
            
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
                valid_dates = df['Date'].dropna()
                if not valid_dates.empty:
                    return valid_dates.iloc[0], "date_column"
        
        return None, None
        
    except Exception as e:
        return None, None
    finally:
        # Reset file pointer for future reads
        uploaded_file.seek(0)

def fetch_nifty_closing_price(target_date):
    """
    Fetches the Nifty 50 (^NSEI) closing price for a specific date using yfinance.
    
    Args:
        target_date: datetime object or date for which to fetch the price
        
    Returns:
        (closing_price, status_message) tuple
        - closing_price: float or None if failed
        - status_message: string describing the result
    """
    try:
        # Convert to datetime if needed
        if hasattr(target_date, 'date'):
            target_date = target_date.date() if hasattr(target_date, 'date') else target_date
        
        target_datetime = pd.to_datetime(target_date)
        
        # Fetch data for target date and next day (to ensure we get the target date)
        start_date = target_datetime
        end_date = target_datetime + timedelta(days=1)
        
        # Use yfinance to get Nifty 50 data
        nifty = yf.Ticker("^NSEI")
        hist = nifty.history(start=start_date.strftime('%Y-%m-%d'), 
                             end=end_date.strftime('%Y-%m-%d'))
        
        if hist.empty:
            # Try fetching a range around the date (might be a holiday)
            # Fetch 5 days before to get the last available price
            start_range = target_datetime - timedelta(days=5)
            hist = nifty.history(start=start_range.strftime('%Y-%m-%d'), 
                                 end=end_date.strftime('%Y-%m-%d'))
            
            if hist.empty:
                return None, f"No market data available for {target_date.strftime('%d %b %Y')} (possibly a holiday/weekend)"
            
            # Get the closest available closing price
            last_available = hist.iloc[-1]
            last_date = hist.index[-1].date()
            
            if last_date != target_date:
                return round(last_available['Close'], 2), f"Using {last_date.strftime('%d %b %Y')} close (market was closed on {target_date.strftime('%d %b %Y')})"
        
        # Get the closing price for the target date
        closing_price = round(hist.iloc[-1]['Close'], 2)
        return closing_price, f"✅ Fetched for {target_date.strftime('%d %b %Y')}"
        
    except Exception as e:
        return None, f"Failed to fetch: {str(e)}"

def process_data(df, current_nifty_spot):
    """Performs all the derivative calculations."""
    
    # Cleaning
    df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['Date']) # Remove empty rows
    
    # Sort for calculations
    df = df.sort_values(by=['Date', 'Client Type'], ascending=[False, True])
    
    # Assign Nifty Spot to the LATEST date only
    if not df.empty:
        latest_date = df['Date'].max()
        df.loc[df['Date'] == latest_date, 'Nifty Spot'] = current_nifty_spot

    # --- SECTION: OPTION ---
    df['Abs Change Call'] = df['Option Index Call Long'] - df['Option Index Call Short']
    df['Abs Change Put'] = df['Option Index Put Long'] - df['Option Index Put Short']
    df['Option NET'] = (df['Option Index Call Long'] + df['Option Index Put Short']) - \
                       (df['Option Index Put Long'] + df['Option Index Call Short'])
    
    # Change of Character (CoC) and ROC
    # We group by Client Type to ensure we compare Client vs Client (Today vs Yesterday)
    df['NET CALL (CoC)'] = df.groupby('Client Type')['Abs Change Call'].diff(periods=-1)
    df['NET PUT (CoC)'] = df.groupby('Client Type')['Abs Change Put'].diff(periods=-1)
    df['NET DIFF'] = df['NET CALL (CoC)'] - df['NET PUT (CoC)']
    df['Option ROC'] = df.groupby('Client Type')['NET DIFF'].diff(periods=-1)

    # --- SECTION: FUTURE INDEX ---
    df['Future Net'] = df['Future Index Long'] - df['Future Index Short']
    df['Future ROC'] = df.groupby('Client Type')['Future Net'].diff(periods=-1)
    df['Fut Abs Chg Long'] = df.groupby('Client Type')['Future Index Long'].diff(periods=-1)
    df['Fut Abs Chg Short'] = df.groupby('Client Type')['Future Index Short'].diff(periods=-1)
    
    # L/S Ratio (Avoid division by zero)
    df['Fut L/S Ratio'] = df.apply(lambda x: x['Future Index Long'] / x['Future Index Short'] if x['Future Index Short'] != 0 else 0, axis=1)
    
    # % Changes
    prev_fut_long = df.groupby('Client Type')['Future Index Long'].shift(-1)
    df['Fut Long %'] = (df['Fut Abs Chg Long'] / prev_fut_long) * 100
    prev_fut_short = df.groupby('Client Type')['Future Index Short'].shift(-1)
    df['Fut Short %'] = (df['Fut Abs Chg Short'] / prev_fut_short) * 100

    # --- SECTION: FUTURE STOCK ---
    df['Stk Fut Net'] = df['Future Stock Long'] - df['Future Stock Short']
    df['Stk Fut ROC'] = df.groupby('Client Type')['Stk Fut Net'].diff(periods=-1)
    df['Stk Abs Chg Long'] = df.groupby('Client Type')['Future Stock Long'].diff(periods=-1)
    df['Stk Abs Chg Short'] = df.groupby('Client Type')['Future Stock Short'].diff(periods=-1)
    df['Stk L/S Ratio'] = df.apply(lambda x: x['Future Stock Long'] / x['Future Stock Short'] if x['Future Stock Short'] != 0 else 0, axis=1)
    
    prev_stk_long = df.groupby('Client Type')['Future Stock Long'].shift(-1)
    df['Stk Long %'] = (df['Stk Abs Chg Long'] / prev_stk_long) * 100
    prev_stk_short = df.groupby('Client Type')['Future Stock Short'].shift(-1)
    df['Stk Short %'] = (df['Stk Abs Chg Short'] / prev_stk_short) * 100

    # --- SECTION: NIFTY ---
    df['Nifty Diff'] = df.groupby('Client Type')['Nifty Spot'].diff(periods=-1)

    # --- SECTION: FUTURE RATIOS (Total Long % and Total Short %) ---
    # These represent each client's share of total contracts for that date
    df['Future Total Long %'] = (df['Future Index Long'] / df.groupby('Date')['Future Index Long'].transform('sum')) * 100
    df['Future Total Short %'] = (df['Future Index Short'] / df.groupby('Date')['Future Index Short'].transform('sum')) * 100
    
    return df

# --- MAIN APP UI ---

st.title("📊 Derivatives Data Analysis Tool")

# 1. Initialize & Load DB
if 'data' not in st.session_state:
    st.session_state['data'] = load_database()

# Show storage mode indicator in sidebar
st.sidebar.markdown("---")
if st.session_state.get('use_cloud_db', False):
    st.sidebar.success("☁️ **Cloud Mode**: Google Sheets")
else:
    st.sidebar.warning("💾 **Local Mode**: CSV File")

# Debug/Diagnostics section (collapsible)
with st.sidebar.expander("🔧 Connection Diagnostics"):
    st.write("**Debug Info:**")
    st.write(f"• gspread available: `{GSHEETS_AVAILABLE}`")
    
    # Safely check for secrets (avoid error when secrets.toml doesn't exist)
    has_secrets = False
    try:
        if hasattr(st, 'secrets') and len(st.secrets) > 0:
            has_secrets = 'gcp_service_account' in st.secrets
    except Exception:
        has_secrets = False
    
    st.write(f"• Secrets configured: `{has_secrets}`")
    
    if has_secrets:
        try:
            sa_email = st.secrets['gcp_service_account'].get('client_email', 'N/A')
            st.write(f"• Service Account: `{sa_email[:30]}...`")
        except Exception as e:
            st.write(f"• Error reading secrets: `{e}`")
    
    st.write(f"• Cloud mode active: `{st.session_state.get('use_cloud_db', False)}`")
    
    # Test connection button
    if st.button("🔄 Test Google Sheets Connection", key="test_gsheets"):
        if GSHEETS_AVAILABLE and has_secrets:
            try:
                client = get_google_sheets_client()
                if client:
                    st.success("✅ Client authorized!")
                    spreadsheet = get_or_create_spreadsheet(client)
                    if spreadsheet:
                        st.success(f"✅ Spreadsheet accessible: {spreadsheet.title}")
                        ws = spreadsheet.sheet1
                        row_count = ws.row_count
                        st.write(f"📊 Sheet has {row_count} rows")
                    else:
                        st.error("❌ Could not access spreadsheet")
                else:
                    st.error("❌ Client authorization failed")
            except Exception as e:
                st.error(f"❌ Connection error: {e}")
        else:
            st.warning("⚠️ Google Sheets not available or secrets not configured")

st.sidebar.markdown("---")

# Show status of database
if not st.session_state['data'].empty:
    latest_db_date = st.session_state['data']['Date'].max().date()
    st.info(f"📂 Database Loaded. Latest Data Available: **{latest_db_date}**")
else:
    st.warning("📂 Database is empty. Please upload data.")

# --- SIDEBAR ---
st.sidebar.header("Data Entry")
uploaded_file = st.sidebar.file_uploader("Upload Daily Participant File", type=['csv', 'xlsx'])

# Initialize session state for nifty price management
if 'auto_nifty_price' not in st.session_state:
    st.session_state['auto_nifty_price'] = None
if 'detected_date' not in st.session_state:
    st.session_state['detected_date'] = None
if 'nifty_status' not in st.session_state:
    st.session_state['nifty_status'] = None
if 'last_uploaded_file' not in st.session_state:
    st.session_state['last_uploaded_file'] = None

# Auto-detect date and fetch Nifty price when file is uploaded
if uploaded_file is not None:
    # Check if this is a new file upload
    current_file_id = f"{uploaded_file.name}_{uploaded_file.size}"
    
    if st.session_state['last_uploaded_file'] != current_file_id:
        # New file detected - peek for date and fetch price
        st.session_state['last_uploaded_file'] = current_file_id
        
        with st.sidebar.status("🔍 Detecting date & fetching Nifty price...", expanded=True) as status:
            # Step 1: Peek file for date
            detected_date, date_source = peek_file_for_date(uploaded_file)
            
            if detected_date is not None:
                st.session_state['detected_date'] = detected_date
                st.write(f"📅 Date detected: **{detected_date.strftime('%d %b %Y')}** (from {date_source})")
                
                # Step 2: Fetch Nifty closing price
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

# Determine default value for Nifty input
if st.session_state['auto_nifty_price'] is not None:
    default_nifty = st.session_state['auto_nifty_price']
else:
    default_nifty = 0.0

# Nifty price input with auto-suggestion
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

if st.sidebar.button("Submit & Process"):
    if uploaded_file is not None:
        with st.spinner("Reading and Processing..."):
            # A. Read File Smartly
            raw_df = read_file_smart(uploaded_file)
            
            if raw_df is not None:
                # B. IMPROVED APPROACH: Merge raw data with existing DB first, then recalculate everything
                
                # Get existing raw data from database (we'll strip calculated columns and recalculate)
                # Use Google Sheets if cloud mode is enabled, otherwise use local CSV
                existing_df = pd.DataFrame()
                
                if st.session_state.get('use_cloud_db', False):
                    # Load from Google Sheets
                    existing_df = load_from_google_sheets()
                    if existing_df is None:
                        existing_df = pd.DataFrame()
                    elif not existing_df.empty:
                        existing_df['Date'] = pd.to_datetime(existing_df['Date'])
                elif os.path.exists(DB_FILE):
                    # Load from local CSV
                    existing_df = pd.read_csv(DB_FILE)
                    existing_df['Date'] = pd.to_datetime(existing_df['Date'])
                
                if not existing_df.empty:
                    # Keep only the raw input columns (not calculated ones)
                    raw_cols = ['Date', 'Client Type', 'Future Index Long', 'Future Index Short',
                                'Future Stock Long', 'Future Stock Short', 
                                'Option Index Call Long', 'Option Index Put Long',
                                'Option Index Call Short', 'Option Index Put Short',
                                'Option Stock Call Long', 'Option Stock Put Long',
                                'Option Stock Call Short', 'Option Stock Put Short',
                                'Total Long Contracts', 'Total Short Contracts', 'Nifty Spot']
                    
                    # Filter to only existing columns
                    available_raw_cols = [c for c in raw_cols if c in existing_df.columns]
                    existing_raw = existing_df[available_raw_cols].copy()
                    
                    # Remove dates that are being uploaded (to avoid duplicates)
                    new_dates = pd.to_datetime(raw_df['Date']).unique()
                    existing_raw = existing_raw[~existing_raw['Date'].isin(new_dates)]
                    
                    # Combine old and new raw data
                    combined_raw = pd.concat([existing_raw, raw_df], ignore_index=True)
                else:
                    combined_raw = raw_df.copy()
                
                # C. Process the COMBINED data (this calculates ROC, CoC across all dates)
                processed_df = process_data(combined_raw, nifty_spot_input)
                
                # D. Save processed data to appropriate storage
                processed_df = processed_df.sort_values(by=['Date', 'Client Type'], ascending=[False, True])
                
                if st.session_state.get('use_cloud_db', False):
                    # Save to Google Sheets
                    success = save_to_google_sheets(processed_df)
                    if success:
                        st.success("✅ Data Processed and Saved to Google Sheets!")
                    else:
                        st.error("❌ Failed to save to Google Sheets. Trying local CSV...")
                        processed_df.to_csv(DB_FILE, index=False)
                        st.warning("⚠️ Data saved to local CSV as fallback.")
                else:
                    # Save to local CSV
                    processed_df.to_csv(DB_FILE, index=False)
                    st.success("✅ Data Processed and Saved to local CSV!")
                
                # E. Update Session State
                st.session_state['data'] = processed_df
            else:
                st.error("❌ Could not find 'Date' or 'Client Type' columns. Check file format.")
    else:
        st.error("Please upload a file first.")

# --- DISPLAY RESULTS ---
if not st.session_state['data'].empty:
    st.divider()
    st.header("📈 Complete Historical Data")
    st.caption("Newest data appears at the top. When you upload new data, it will be added at the top and older data shifts down.")
    
    # Prepare display dataframe - sort by Date (descending) and Client Type
    display_df = st.session_state['data'].copy()
    display_df = display_df.sort_values(by=['Date', 'Client Type'], ascending=[False, True])
    
    # Format the Date column for display (DD.MM.YY format like in your Excel)
    display_df['Date'] = pd.to_datetime(display_df['Date']).dt.strftime('%d.%m.%y')
    
    # Define the 3-layer header structure matching Excel exactly
    # Each column has: internal_name, layer2_name (sub-category), layer3_name (column name)
    # Colors match the Excel: Green for OPTION, Cyan for FUTURE, Yellow for FUTURE STOCK, etc.
    
    header_structure = {
        # Layer 1: Main category groups with their colors
        'groups': [
            {
                'name': '',  # Empty for Date/Client Type
                'color': '#FFFF99',  # Light yellow
                'subgroups': [
                    {'name': 'Date', 'columns': [('Date', 'Date')]},
                    {'name': 'Client Type', 'columns': [('Client Type', 'Client Type')]}
                ]
            },
            {
                'name': 'OPTION',
                'color': '#00FF00',  # Green
                'subgroups': [
                    {'name': 'NET DIFF', 'columns': [('NET DIFF', '')]},
                    {'name': 'ROC', 'columns': [('Option ROC', '')]},
                    {'name': 'ABSULATE CHANGE', 'columns': [('Abs Change Call', 'call Index'), ('Abs Change Put', 'Put Index')]},
                    {'name': 'OPTION', 'columns': [('Option NET', 'NET')]},
                    {'name': 'NET CALL', 'columns': [('NET CALL (CoC)', '')]},
                    {'name': 'NET PUT', 'columns': [('NET PUT (CoC)', '')]}
                ]
            },
            {
                'name': 'FUTURE',
                'color': '#00FFFF',  # Cyan
                'subgroups': [
                    {'name': 'FUTURE', 'columns': [('Future Net', 'NET')]},
                    {'name': 'ROC', 'columns': [('Future ROC', '')]},
                    {'name': 'ABSULATE CHANGE', 'columns': [('Fut Abs Chg Long', 'LONG'), ('Fut Abs Chg Short', 'SHORT')]},
                    {'name': 'L/S RATIO', 'columns': [('Fut L/S Ratio', '')]},
                    {'name': 'LONG', 'columns': [('Fut Long %', '%')]},
                    {'name': 'SHORT', 'columns': [('Fut Short %', '%')]}
                ]
            },
            {
                'name': 'FUTURE STOCK',
                'color': '#FFFF00',  # Yellow
                'subgroups': [
                    {'name': 'FUTURE', 'columns': [('Stk Fut Net', 'NET')]},
                    {'name': 'ROC', 'columns': [('Stk Fut ROC', '')]},
                    {'name': 'ABSULATE CHANGE', 'columns': [('Stk Abs Chg Long', 'LONG'), ('Stk Abs Chg Short', 'SHORT')]},
                    {'name': 'L/S RATIO', 'columns': [('Stk L/S Ratio', '')]},
                    {'name': 'LONG', 'columns': [('Stk Long %', '%')]},
                    {'name': 'SHORT', 'columns': [('Stk Short %', '%')]}
                ]
            },
            {
                'name': '',  # Empty for NIFTY section (no top header in Excel)
                'color': '#90EE90',  # Light green
                'subgroups': [
                    {'name': 'NIFTY', 'columns': [('Nifty Diff', 'difff')]},
                    {'name': 'NIFTY', 'columns': [('Nifty Spot', 'spot')]}
                ]
            },
            {
                'name': 'FUTURE',
                'color': '#FF00FF',  # Magenta
                'subgroups': [
                    {'name': 'TOTAL LONG', 'columns': [('Future Total Long %', '%')]},
                    {'name': 'TOTAL SHORT', 'columns': [('Future Total Short %', '%')]}
                ]
            }
        ]
    }
    
    # Filter to only include columns that exist in the dataframe
    filtered_groups = []
    for group in header_structure['groups']:
        filtered_subgroups = []
        for subgroup in group['subgroups']:
            filtered_cols = [(col, label) for col, label in subgroup['columns'] if col in display_df.columns]
            if filtered_cols:
                filtered_subgroups.append({'name': subgroup['name'], 'columns': filtered_cols})
        if filtered_subgroups:
            filtered_groups.append({
                'name': group['name'],
                'color': group['color'],
                'subgroups': filtered_subgroups
            })
    
    # Build all valid columns in order
    all_display_cols = []
    for group in filtered_groups:
        for subgroup in group['subgroups']:
            for col, _ in subgroup['columns']:
                all_display_cols.append(col)
    
    # Format values for display and detect if negative
    def format_value_with_class(value, col):
        """Returns (formatted_string, css_class) tuple"""
        if pd.isna(value):
            return '-', ''
        try:
            is_negative = False
            formatted = ''
            
            if isinstance(value, (int, float)):
                is_negative = value < 0
                
                if 'Ratio' in col:
                    formatted = f'{value:.2f}'
                elif '%' in col:
                    formatted = f'{value:.2f}%'
                elif col in ['Nifty Spot', 'Nifty Diff']:
                    formatted = f'{value:.2f}'
                else:
                    formatted = f'{value:,.0f}'
            else:
                formatted = str(value)
            
            css_class = 'negative-value' if is_negative else ''
            return formatted, css_class
        except:
            return str(value), ''
    
    # Wrap in complete HTML document for components.html
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Arial, sans-serif;
            background-color: transparent;
        }}
        .table-wrapper {{
            position: relative;
            padding-top: 50px;
        }}
        .maximize-btn {{
            position: absolute;
            top: 5px;
            right: 10px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white !important;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 6px;
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.4);
            transition: all 0.3s ease;
            z-index: 100;
        }}
        .maximize-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.6);
        }}
        .styled-table-container {{
            overflow-x: auto;
            max-height: 600px;
            overflow-y: auto;
            border: 2px solid #333;
            border-radius: 8px;
            background-color: #ffffff !important;
        }}
        /* Custom scrollbar styling - thin and subtle */
        .styled-table-container::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}
        .styled-table-container::-webkit-scrollbar-track {{
            background: #f1f1f1;
            border-radius: 4px;
        }}
        .styled-table-container::-webkit-scrollbar-thumb {{
            background: #888;
            border-radius: 4px;
        }}
        .styled-table-container::-webkit-scrollbar-thumb:hover {{
            background: #555;
        }}
        .styled-table-container.fullscreen {{
            width: 100% !important;
            height: 100% !important;
            max-width: 100% !important;
            max-height: 100% !important;
            overflow-x: auto !important;
            overflow-y: auto !important;
            border-radius: 0 !important;
            margin: 0 !important;
            padding: 15px !important;
            box-sizing: border-box !important;
            background-color: #ffffff !important;
        }}
        .styled-table {{
            border-collapse: collapse;
            width: 100%;
            font-size: 12px;
            font-family: 'Segoe UI', Arial, sans-serif;
            background-color: #ffffff !important;
            color: #000000 !important;
        }}
        .styled-table thead {{
            /* Header scrolls with table - not fixed */
        }}
        .styled-table th, .styled-table td {{
            padding: 6px 10px;
            text-align: center;
            border: 1px solid #333;
            white-space: nowrap;
            color: #000000 !important;
        }}
        .styled-table .layer1-header {{
            font-weight: bold;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            border: 2px solid #333;
            color: #000000 !important;
        }}
        .styled-table .layer2-header {{
            font-weight: 600;
            font-size: 11px;
            border: 1px solid #333;
            color: #000000 !important;
        }}
        .styled-table .layer3-header {{
            font-weight: 500;
            font-size: 10px;
            border: 1px solid #333;
            color: #000000 !important;
        }}
        .styled-table tbody tr:nth-child(even) {{
            background-color: #f8f9fa !important;
        }}
        .styled-table tbody tr:hover {{
            background-color: #e8f4f8 !important;
        }}
        .styled-table td {{
            font-size: 11px;
            background-color: inherit;
            color: #000000 !important;
        }}
        .styled-table td.negative-value {{
            color: #dc3545 !important;
            font-weight: 600;
        }}
        .styled-table .date-group-1 {{ background-color: #ffffff !important; }}
        .styled-table .date-group-2 {{ background-color: #f0f8ff !important; }}
        .close-fullscreen-btn {{
            position: fixed;
            top: 15px;
            right: 25px;
            background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
            color: white !important;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            z-index: 10001;
            display: none;
            box-shadow: 0 4px 15px rgba(220, 53, 69, 0.4);
            transition: all 0.3s ease;
        }}
        .close-fullscreen-btn:hover {{
            transform: scale(1.05);
            box-shadow: 0 6px 20px rgba(220, 53, 69, 0.6);
        }}
        </style>
    </head>
    <body>
        <div class="table-wrapper">
            <button id="maximize-btn" class="maximize-btn" onclick="enterFullscreen()">⛶ Maximize</button>
            <div id="table-container" class="styled-table-container">
                <table class="styled-table">
                    <thead><tr>"""
    
    # Add Layer 1 headers
    for group in filtered_groups:
        total_cols = sum(len(sg['columns']) for sg in group['subgroups'])
        if group['name']:
            full_html += f'<th colspan="{total_cols}" class="layer1-header" style="background-color: {group["color"]};">{group["name"]}</th>'
        else:
            full_html += f'<th colspan="{total_cols}" class="layer1-header" style="background-color: {group["color"]};"></th>'
    full_html += '</tr><tr>'
    
    # Add Layer 2 headers
    for group in filtered_groups:
        for subgroup in group['subgroups']:
            colspan = len(subgroup['columns'])
            full_html += f'<th colspan="{colspan}" class="layer2-header" style="background-color: {group["color"]}DD;">{subgroup["name"]}</th>'
    full_html += '</tr><tr>'
    
    # Add Layer 3 headers
    for group in filtered_groups:
        for subgroup in group['subgroups']:
            for col, label in subgroup['columns']:
                display_label = label if label else ''
                full_html += f'<th class="layer3-header" style="background-color: {group["color"]}99;">{display_label}</th>'
    full_html += '</tr></thead><tbody>'
    
    # Add data rows
    prev_date = None
    date_group = 0
    for idx, row in display_df.iterrows():
        current_date = row.get('Date', '')
        if current_date != prev_date:
            date_group = 1 - date_group
            prev_date = current_date
        
        row_class = f'date-group-{date_group + 1}'
        full_html += f'<tr class="{row_class}">'
        for col in all_display_cols:
            value = row.get(col, '-')
            formatted, cell_class = format_value_with_class(value, col)
            if cell_class:
                full_html += f'<td class="{cell_class}">{formatted}</td>'
            else:
                full_html += f'<td>{formatted}</td>'
        full_html += '</tr>'
    
    full_html += """</tbody></table>
            <button id="close-fullscreen-btn" class="close-fullscreen-btn" onclick="exitFullscreen()">✕ Exit Fullscreen</button>
            </div>
        </div>
        <script>
        function enterFullscreen() {
            var container = document.getElementById('table-container');
            var btn = document.getElementById('maximize-btn');
            var closeBtn = document.getElementById('close-fullscreen-btn');
            
            // Use the Browser Fullscreen API for true fullscreen
            if (container.requestFullscreen) {
                container.requestFullscreen();
            } else if (container.webkitRequestFullscreen) { /* Safari */
                container.webkitRequestFullscreen();
            } else if (container.msRequestFullscreen) { /* IE11 */
                container.msRequestFullscreen();
            }
            
            // Add fullscreen class for styling
            container.classList.add('fullscreen');
            closeBtn.style.display = 'block';
            btn.style.display = 'none';
        }
        
        function exitFullscreen() {
            var container = document.getElementById('table-container');
            var btn = document.getElementById('maximize-btn');
            var closeBtn = document.getElementById('close-fullscreen-btn');
            
            // Exit fullscreen using the Browser API
            if (document.exitFullscreen) {
                document.exitFullscreen();
            } else if (document.webkitExitFullscreen) { /* Safari */
                document.webkitExitFullscreen();
            } else if (document.msExitFullscreen) { /* IE11 */
                document.msExitFullscreen();
            }
            
            container.classList.remove('fullscreen');
            closeBtn.style.display = 'none';
            btn.style.display = 'flex';
        }
        
        // Listen for fullscreen change events (e.g., user presses Escape)
        document.addEventListener('fullscreenchange', handleFullscreenChange);
        document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
        document.addEventListener('msfullscreenchange', handleFullscreenChange);
        
        function handleFullscreenChange() {
            var container = document.getElementById('table-container');
            var btn = document.getElementById('maximize-btn');
            var closeBtn = document.getElementById('close-fullscreen-btn');
            
            if (!document.fullscreenElement && !document.webkitFullscreenElement && !document.msFullscreenElement) {
                // Exited fullscreen
                container.classList.remove('fullscreen');
                closeBtn.style.display = 'none';
                btn.style.display = 'flex';
            }
        }
        </script>
    </body>
    </html>
    """
    
    # Fixed height for the component (table max-height 600px + button + padding)
    table_height = 720
    
    # Display using components.html which supports JavaScript
    components.html(full_html, height=table_height, scrolling=False)
    
    # Show summary stats
    unique_dates = display_df['Date'].nunique()
    total_rows = len(display_df)
    st.info(f"📊 Showing **{total_rows}** rows across **{unique_dates}** trading dates")
    
    # Download Button for the Master Database
    st.divider()
    csv = st.session_state['data'].to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Full Historical Database (CSV)",
        data=csv,
        file_name='derivative_data_db.csv',
        mime='text/csv',
    )