# Data calculation functions - derivative analysis calculations
import pandas as pd
import yfinance as yf
from datetime import timedelta


def fetch_nifty_closing_price(target_date):
    """
    Fetches the Nifty 50 (^NSEI) closing price for a specific date using yfinance.
    
    Returns:
        (closing_price, status_message) tuple
    """
    try:
        if hasattr(target_date, 'date'):
            target_date = target_date.date()
        
        target_datetime = pd.to_datetime(target_date)
        
        start_date = target_datetime
        end_date = target_datetime + timedelta(days=1)
        
        nifty = yf.Ticker("^NSEI")
        hist = nifty.history(start=start_date.strftime('%Y-%m-%d'), 
                             end=end_date.strftime('%Y-%m-%d'))
        
        if hist.empty:
            start_range = target_datetime - timedelta(days=5)
            hist = nifty.history(start=start_range.strftime('%Y-%m-%d'), 
                                 end=end_date.strftime('%Y-%m-%d'))
            
            if hist.empty:
                return None, f"No market data available for {target_date.strftime('%d %b %Y')}"
            
            last_available = hist.iloc[-1]
            last_date = hist.index[-1].date()
            
            if last_date != target_date:
                return round(last_available['Close'], 2), f"Using {last_date.strftime('%d %b %Y')} close"
        
        closing_price = round(hist.iloc[-1]['Close'], 2)
        return closing_price, f"✅ Fetched for {target_date.strftime('%d %b %Y')}"
        
    except Exception as e:
        return None, f"Failed to fetch: {str(e)}"


def process_data(df, current_nifty_spot):
    """Performs all the derivative calculations."""
    
    # Cleaning
    df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['Date'])
    
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
    
    # Create mask for non-TOTAL rows (diff calculations only apply to actual participants)
    non_total_mask = df['Client Type'].str.upper() != 'TOTAL'
    
    # Change of Character (CoC) and ROC - only for non-TOTAL rows
    df['NET CALL (CoC)'] = float('nan')
    df['NET PUT (CoC)'] = float('nan')
    df['NET DIFF'] = float('nan')
    df['Option ROC'] = float('nan')
    
    if non_total_mask.any():
        df_non_total = df[non_total_mask].copy()
        df_non_total['NET CALL (CoC)'] = df_non_total.groupby('Client Type')['Abs Change Call'].diff(periods=-1)
        df_non_total['NET PUT (CoC)'] = df_non_total.groupby('Client Type')['Abs Change Put'].diff(periods=-1)
        df_non_total['NET DIFF'] = df_non_total['NET CALL (CoC)'] - df_non_total['NET PUT (CoC)']
        df_non_total['Option ROC'] = df_non_total.groupby('Client Type')['NET DIFF'].diff(periods=-1)
        df.loc[non_total_mask, ['NET CALL (CoC)', 'NET PUT (CoC)', 'NET DIFF', 'Option ROC']] = df_non_total[['NET CALL (CoC)', 'NET PUT (CoC)', 'NET DIFF', 'Option ROC']]

    # --- SECTION: FUTURE INDEX ---
    df['Future Net'] = df['Future Index Long'] - df['Future Index Short']
    
    # Initialize diff columns
    df['Future ROC'] = float('nan')
    df['Fut Abs Chg Long'] = float('nan')
    df['Fut Abs Chg Short'] = float('nan')
    df['Fut Long %'] = float('nan')
    df['Fut Short %'] = float('nan')
    
    if non_total_mask.any():
        df_non_total = df[non_total_mask].copy()
        df_non_total['Future ROC'] = df_non_total.groupby('Client Type')['Future Net'].diff(periods=-1)
        df_non_total['Fut Abs Chg Long'] = df_non_total.groupby('Client Type')['Future Index Long'].diff(periods=-1)
        df_non_total['Fut Abs Chg Short'] = df_non_total.groupby('Client Type')['Future Index Short'].diff(periods=-1)
        
        # % Changes
        prev_fut_long = df_non_total.groupby('Client Type')['Future Index Long'].shift(-1)
        df_non_total['Fut Long %'] = (df_non_total['Fut Abs Chg Long'] / prev_fut_long) * 100
        prev_fut_short = df_non_total.groupby('Client Type')['Future Index Short'].shift(-1)
        df_non_total['Fut Short %'] = (df_non_total['Fut Abs Chg Short'] / prev_fut_short) * 100
        
        df.loc[non_total_mask, ['Future ROC', 'Fut Abs Chg Long', 'Fut Abs Chg Short', 'Fut Long %', 'Fut Short %']] = df_non_total[['Future ROC', 'Fut Abs Chg Long', 'Fut Abs Chg Short', 'Fut Long %', 'Fut Short %']]
    
    # L/S Ratio - applies to all rows including TOTAL
    df['Fut L/S Ratio'] = df.apply(
        lambda x: x['Future Index Long'] / x['Future Index Short'] if x['Future Index Short'] != 0 else 0, 
        axis=1
    )

    # --- SECTION: FUTURE STOCK ---
    df['Stk Fut Net'] = df['Future Stock Long'] - df['Future Stock Short']
    
    # Initialize diff columns
    df['Stk Fut ROC'] = float('nan')
    df['Stk Abs Chg Long'] = float('nan')
    df['Stk Abs Chg Short'] = float('nan')
    df['Stk Long %'] = float('nan')
    df['Stk Short %'] = float('nan')
    
    if non_total_mask.any():
        df_non_total = df[non_total_mask].copy()
        df_non_total['Stk Fut ROC'] = df_non_total.groupby('Client Type')['Stk Fut Net'].diff(periods=-1)
        df_non_total['Stk Abs Chg Long'] = df_non_total.groupby('Client Type')['Future Stock Long'].diff(periods=-1)
        df_non_total['Stk Abs Chg Short'] = df_non_total.groupby('Client Type')['Future Stock Short'].diff(periods=-1)
        
        prev_stk_long = df_non_total.groupby('Client Type')['Future Stock Long'].shift(-1)
        df_non_total['Stk Long %'] = (df_non_total['Stk Abs Chg Long'] / prev_stk_long) * 100
        prev_stk_short = df_non_total.groupby('Client Type')['Future Stock Short'].shift(-1)
        df_non_total['Stk Short %'] = (df_non_total['Stk Abs Chg Short'] / prev_stk_short) * 100
        
        df.loc[non_total_mask, ['Stk Fut ROC', 'Stk Abs Chg Long', 'Stk Abs Chg Short', 'Stk Long %', 'Stk Short %']] = df_non_total[['Stk Fut ROC', 'Stk Abs Chg Long', 'Stk Abs Chg Short', 'Stk Long %', 'Stk Short %']]
    
    # L/S Ratio - applies to all rows including TOTAL
    df['Stk L/S Ratio'] = df.apply(
        lambda x: x['Future Stock Long'] / x['Future Stock Short'] if x['Future Stock Short'] != 0 else 0, 
        axis=1
    )

    # --- SECTION: NIFTY ---
    df['Nifty Diff'] = df.groupby('Client Type')['Nifty Spot'].diff(periods=-1)

    # --- SECTION: FUTURE RATIOS ---
    # Get total for each date (sum of non-TOTAL rows, or the TOTAL row value)
    total_long_per_date = df[df['Client Type'].str.upper() == 'TOTAL'].groupby('Date')['Future Index Long'].first()
    total_short_per_date = df[df['Client Type'].str.upper() == 'TOTAL'].groupby('Date')['Future Index Short'].first()
    
    # If no TOTAL row, calculate from sum
    if total_long_per_date.empty:
        total_long_per_date = df[non_total_mask].groupby('Date')['Future Index Long'].sum()
        total_short_per_date = df[non_total_mask].groupby('Date')['Future Index Short'].sum()
    
    # Map totals back to dataframe
    df['_total_long'] = df['Date'].map(total_long_per_date)
    df['_total_short'] = df['Date'].map(total_short_per_date)
    
    # Calculate percentages
    df['Future Total Long %'] = (df['Future Index Long'] / df['_total_long']) * 100
    df['Future Total Short %'] = (df['Future Index Short'] / df['_total_short']) * 100
    
    # Drop temp columns
    df = df.drop(columns=['_total_long', '_total_short'], errors='ignore')
    
    return df

