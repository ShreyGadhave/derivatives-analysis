# Configuration and constants for the Derivatives Analysis Tool

# Database file for local fallback
DB_FILE = 'derivative_data_db.csv'

# Raw data columns (used for filtering calculated columns)
RAW_DATA_COLUMNS = [
    'Date', 'Client Type', 
    'Future Index Long', 'Future Index Short',
    'Future Stock Long', 'Future Stock Short', 
    'Option Index Call Long', 'Option Index Put Long',
    'Option Index Call Short', 'Option Index Put Short',
    'Option Stock Call Long', 'Option Stock Put Long',
    'Option Stock Call Short', 'Option Stock Put Short',
    'Total Long Contracts', 'Total Short Contracts', 
    'Nifty Spot'
]
