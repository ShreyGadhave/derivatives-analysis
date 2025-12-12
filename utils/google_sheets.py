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
    """Load data from Google Sheets (handles 3-row headers)."""
    try:
        # Import to get column order
        from utils.display import get_display_columns
        
        client = get_google_sheets_client()
        if client is None:
            return None
        
        spreadsheet = get_or_create_spreadsheet(client)
        if spreadsheet is None:
            return None
        
        worksheet = spreadsheet.sheet1
        
        # Get all values (including headers)
        all_values = worksheet.get_all_values()
        
        if not all_values or len(all_values) <= 3:
            # Empty or only headers
            return pd.DataFrame()
        
        # Row 3 (index 2) contains the actual column names we need
        # But we use our known display columns for consistency
        display_cols = get_display_columns()
        
        # Get the header row (row 3, index 2) to determine actual columns
        header_row = all_values[2] if len(all_values) > 2 else []
        
        # Data starts from row 4 (index 3)
        data_rows = all_values[3:]
        
        if not data_rows:
            return pd.DataFrame()
        
        # Create DataFrame - use display columns as headers
        # Match the number of columns in data
        num_cols = len(data_rows[0]) if data_rows else 0
        headers = display_cols[:num_cols] if len(display_cols) >= num_cols else display_cols + [f'Col_{i}' for i in range(len(display_cols), num_cols)]
        
        df = pd.DataFrame(data_rows, columns=headers[:len(data_rows[0])])
        
        # Convert Date column
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], format='%d.%m.%y', errors='coerce')
        
        return df
        
    except Exception as e:
        st.error(f"Error loading from Google Sheets: {e}")
        return None



def save_to_google_sheets(df):
    """Save DataFrame to Google Sheets with proper formatting and colors."""
    try:
        # Import here to avoid circular import
        from utils.display import prepare_export_with_headers, get_column_colors
        
        client = get_google_sheets_client()
        if client is None:
            return False
        
        spreadsheet = get_or_create_spreadsheet(client)
        if spreadsheet is None:
            return False
        
        worksheet = spreadsheet.sheet1
        
        # Get formatted data with headers
        all_rows, colors = prepare_export_with_headers(df)
        
        # Clear and write all rows at once
        worksheet.clear()
        worksheet.update('A1', all_rows)
        
        # Apply header colors (rows 1-3)
        try:
            # Get number of columns
            num_cols = len(all_rows[0]) if all_rows else 0
            
            if num_cols > 0:
                # Apply colors to header rows using batch update for better performance
                from gspread.utils import rowcol_to_a1
                
                # Build color requests for each column in header rows
                requests = []
                for col_idx, color_hex in enumerate(colors[:num_cols]):
                    # Convert hex color to RGB (0-1 scale)
                    r = int(color_hex[1:3], 16) / 255
                    g = int(color_hex[3:5], 16) / 255
                    b = int(color_hex[5:7], 16) / 255
                    
                    # Apply color to rows 1-3 for this column
                    for row_idx in range(3):
                        requests.append({
                            'repeatCell': {
                                'range': {
                                    'sheetId': worksheet.id,
                                    'startRowIndex': row_idx,
                                    'endRowIndex': row_idx + 1,
                                    'startColumnIndex': col_idx,
                                    'endColumnIndex': col_idx + 1
                                },
                                'cell': {
                                    'userEnteredFormat': {
                                        'backgroundColor': {'red': r, 'green': g, 'blue': b},
                                        'textFormat': {'bold': True}
                                    }
                                },
                                'fields': 'userEnteredFormat(backgroundColor,textFormat)'
                            }
                        })
                
                # Apply TOTAL row highlighting (light yellow)
                # Find rows where column B (Client Type) contains "TOTAL"
                for row_idx, row in enumerate(all_rows[3:], start=3):  # Skip header rows
                    if len(row) > 1 and 'TOTAL' in str(row[1]).upper():
                        requests.append({
                            'repeatCell': {
                                'range': {
                                    'sheetId': worksheet.id,
                                    'startRowIndex': row_idx,
                                    'endRowIndex': row_idx + 1,
                                    'startColumnIndex': 0,
                                    'endColumnIndex': num_cols
                                },
                                'cell': {
                                    'userEnteredFormat': {
                                        'backgroundColor': {'red': 1.0, 'green': 0.98, 'blue': 0.8},  # Light yellow
                                        'textFormat': {'bold': True}
                                    }
                                },
                                'fields': 'userEnteredFormat(backgroundColor,textFormat)'
                            }
                        })
                
                # Execute batch update
                if requests:
                    spreadsheet.batch_update({'requests': requests})
                    
        except Exception as format_error:
            # If formatting fails, data is still saved - just log the error
            print(f"Warning: Could not apply formatting: {format_error}")
        
        return True
        
    except Exception as e:
        st.error(f"Error saving to Google Sheets: {e}")
        return False
