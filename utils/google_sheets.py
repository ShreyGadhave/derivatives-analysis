# Google Sheets integration functions
import streamlit as st
import pandas as pd

# Try to import Google Sheets libraries (for cloud deployment)
try:
    from google.oauth2.service_account import Credentials
    import gspread
    from gspread.exceptions import SpreadsheetNotFound, APIError
    GSHEETS_AVAILABLE = True
except ImportError:
    GSHEETS_AVAILABLE = False
    SpreadsheetNotFound = Exception  # Fallback to generic exception
    APIError = Exception


def is_cloud_deployment():
    """Check if we're running on Streamlit Cloud with secrets configured."""
    try:
        if hasattr(st, 'secrets') and len(st.secrets) > 0:
            if 'gcp_service_account' in st.secrets:
                return True
        return False
    except Exception:
        return False


def _has_secrets():
    """Safely check if secrets are configured."""
    try:
        if hasattr(st, 'secrets') and len(st.secrets) > 0:
            return 'gcp_service_account' in st.secrets
    except Exception:
        pass
    return False


@st.cache_resource
def get_google_sheets_client():
    """Initialize Google Sheets client using Streamlit secrets."""
    try:
        if not GSHEETS_AVAILABLE:
            return None
        
        if not _has_secrets():
            return None
        
        credentials = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
        )
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        st.error(f"Google Sheets connection failed: {e}")
        return None


def get_or_create_spreadsheet(client):
    """Get or create the spreadsheet. Tries URL first (recommended), then name."""
    try:
        # Option 1: Try to open by URL (recommended - avoids Drive quota issues)
        if 'spreadsheet_url' in st.secrets and st.secrets['spreadsheet_url']:
            try:
                spreadsheet_url = st.secrets['spreadsheet_url']
                spreadsheet = client.open_by_url(spreadsheet_url)
                return spreadsheet
            except Exception as e:
                st.warning(f"Could not open spreadsheet by URL: {e}")
        
        # Option 2: Try to open by name
        spreadsheet_name = st.secrets.get("spreadsheet_name", "DerivativesDB")
        
        try:
            spreadsheet = client.open(spreadsheet_name)
            return spreadsheet
        except SpreadsheetNotFound:
            # Option 3: Create new spreadsheet (requires Drive quota)
            try:
                spreadsheet = client.create(spreadsheet_name)
                
                # Share with user if email provided
                if 'share_email' in st.secrets:
                    spreadsheet.share(st.secrets['share_email'], perm_type='user', role='writer')
                
                return spreadsheet
            except APIError as create_error:
                error_msg = str(create_error)
                if 'quota' in error_msg.lower() or 'storage' in error_msg.lower():
                    st.error("❌ **Google Drive Storage Quota Exceeded!**\n\n"
                            "The service account cannot create new spreadsheets.\n\n"
                            "**Fix:** Create a spreadsheet manually in your Google Drive, "
                            "share it with the service account email, and add `spreadsheet_url` to your secrets.")
                else:
                    st.error(f"❌ Could not create spreadsheet: {create_error}")
                return None
                
    except APIError as e:
        error_msg = str(e)
        if 'quota' in error_msg.lower() or 'storage' in error_msg.lower():
            st.error("❌ **Google Drive Storage Quota Exceeded!**\n\n"
                    "Please create a spreadsheet manually and use `spreadsheet_url` in your secrets.")
        else:
            st.error(f"Google API Error: {e}")
        return None
    except Exception as e:
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
        
        # Get all records (row 1 is headers, data starts row 2)
        data = worksheet.get_all_records()
        
        if not data:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        
        # Convert Date column
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        
        # Convert numeric columns from strings where needed
        for col in df.columns:
            if col in ['Date', 'Client Type']:
                continue
            # Try to convert to numeric
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
        
    except Exception as e:
        st.error(f"Error loading from Google Sheets: {e}")
        return None



def save_to_google_sheets(df):
    """Save only calculated/display columns to Google Sheets (not raw input columns)."""
    try:
        # Import to get display columns
        from utils.display import get_display_columns
        
        client = get_google_sheets_client()
        if client is None:
            return False
        
        spreadsheet = get_or_create_spreadsheet(client)
        if spreadsheet is None:
            return False
        
        worksheet = spreadsheet.sheet1
        
        # Get ALL display columns (calculated results)
        display_cols = get_display_columns()
        
        # Create a copy with only display columns, adding missing ones as empty
        df_copy = pd.DataFrame()
        for col in display_cols:
            if col in df.columns:
                df_copy[col] = df[col]
            else:
                df_copy[col] = ''  # Add missing columns as empty
        
        # Sort by date descending
        if 'Date' in df_copy.columns:
            df_copy = df_copy.sort_values(by=['Date', 'Client Type'], ascending=[False, True])
            df_copy['Date'] = pd.to_datetime(df_copy['Date'], errors='coerce').dt.strftime('%Y-%m-%d')
        
        # Replace NaN with empty string for JSON compatibility
        df_copy = df_copy.fillna('')
        
        # Build rows with headers
        headers = df_copy.columns.tolist()
        data_rows = df_copy.values.tolist()
        
        all_rows = [headers] + data_rows
        
        # Clear and write
        worksheet.clear()
        worksheet.update('A1', all_rows)
        
        return True
        
    except Exception as e:
        st.error(f"Error saving to Google Sheets: {e}")
        return False


