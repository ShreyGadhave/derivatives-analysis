# Database functions - load and save data
import os
import pandas as pd
import streamlit as st

from config import DB_FILE
from utils.google_sheets import load_from_google_sheets, save_to_google_sheets


def load_database():
    """Loads the historical data - tries Google Sheets first, then local CSV."""
    
    # Try Google Sheets first (for cloud deployment)
    if st.session_state.get('use_cloud_db', False):
        df = load_from_google_sheets()
        if df is not None:
            return df
    
    # Fallback to local CSV
    st.session_state['use_cloud_db'] = False
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            df['Date'] = pd.to_datetime(df['Date'])
            return df
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


def save_database(df, use_cloud=False):
    """Save DataFrame to appropriate storage (Google Sheets or local CSV)."""
    df = df.sort_values(by=['Date', 'Client Type'], ascending=[False, True])
    
    if use_cloud:
        success = save_to_google_sheets(df)
        if success:
            st.success("✅ Data Processed and Saved to Google Sheets!")
            return True
        else:
            st.error("❌ Failed to save to Google Sheets. Trying local CSV...")
            df.to_csv(DB_FILE, index=False)
            st.warning("⚠️ Data saved to local CSV as fallback.")
            return False
    else:
        df.to_csv(DB_FILE, index=False)
        st.success("✅ Data Processed and Saved to local CSV!")
        return True
