# File processing functions - read files and extract dates
import re
import pandas as pd
import streamlit as st


def extract_date_from_title(title_text):
    """
    Extracts date from NSE title row like:
    'Participant wise Open Interest (no. of contracts) in Equity Derivatives as on Dec 05, 2025'
    """
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
        
        df.columns = df.columns.str.strip()

        if 'Date' in df.columns:
            return df

        # Attempt 2: Header in Row 1 (Skipping Title Row) - NSE's format
        uploaded_file.seek(0)
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, header=1)
        else:
            df = pd.read_excel(uploaded_file, header=1)
        
        df.columns = df.columns.str.strip()
        df = df.dropna(how='all')

        if 'Client Type' in df.columns:
            if extracted_date is not None:
                df['Date'] = extracted_date
                return df
            else:
                cols = list(df.columns)
                client_idx = cols.index('Client Type')
                if client_idx > 0:
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
            df = pd.read_csv(uploaded_file, nrows=5)
            df.columns = df.columns.str.strip()
            
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
                valid_dates = df['Date'].dropna()
                if not valid_dates.empty:
                    return valid_dates.iloc[0], "date_column"
            
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, header=1, nrows=5)
            df.columns = df.columns.str.strip()
            
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
                valid_dates = df['Date'].dropna()
                if not valid_dates.empty:
                    return valid_dates.iloc[0], "date_column"
        else:
            df = pd.read_excel(uploaded_file, nrows=5)
            df.columns = df.columns.str.strip()
            
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
                valid_dates = df['Date'].dropna()
                if not valid_dates.empty:
                    return valid_dates.iloc[0], "date_column"
        
        return None, None
        
    except Exception:
        return None, None
    finally:
        uploaded_file.seek(0)
