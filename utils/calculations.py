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
    
    # Change of Character (CoC) and ROC
    df['NET CALL (CoC)'] = df.groupby('Client Type')['Abs Change Call'].diff(periods=-1)
    df['NET PUT (CoC)'] = df.groupby('Client Type')['Abs Change Put'].diff(periods=-1)
    df['NET DIFF'] = df['NET CALL (CoC)'] - df['NET PUT (CoC)']
    df['Option ROC'] = df.groupby('Client Type')['NET DIFF'].diff(periods=-1)

    # --- SECTION: FUTURE INDEX ---
    df['Future Net'] = df['Future Index Long'] - df['Future Index Short']
    df['Future ROC'] = df.groupby('Client Type')['Future Net'].diff(periods=-1)
    df['Fut Abs Chg Long'] = df.groupby('Client Type')['Future Index Long'].diff(periods=-1)
    df['Fut Abs Chg Short'] = df.groupby('Client Type')['Future Index Short'].diff(periods=-1)
    
    # L/S Ratio
    df['Fut L/S Ratio'] = df.apply(
        lambda x: x['Future Index Long'] / x['Future Index Short'] if x['Future Index Short'] != 0 else 0, 
        axis=1
    )
    
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
    df['Stk L/S Ratio'] = df.apply(
        lambda x: x['Future Stock Long'] / x['Future Stock Short'] if x['Future Stock Short'] != 0 else 0, 
        axis=1
    )
    
    prev_stk_long = df.groupby('Client Type')['Future Stock Long'].shift(-1)
    df['Stk Long %'] = (df['Stk Abs Chg Long'] / prev_stk_long) * 100
    prev_stk_short = df.groupby('Client Type')['Future Stock Short'].shift(-1)
    df['Stk Short %'] = (df['Stk Abs Chg Short'] / prev_stk_short) * 100

    # --- SECTION: NIFTY ---
    df['Nifty Diff'] = df.groupby('Client Type')['Nifty Spot'].diff(periods=-1)

    # --- SECTION: FUTURE RATIOS ---
    df['Future Total Long %'] = (df['Future Index Long'] / df.groupby('Date')['Future Index Long'].transform('sum')) * 100
    df['Future Total Short %'] = (df['Future Index Short'] / df.groupby('Date')['Future Index Short'].transform('sum')) * 100
    
    return df
