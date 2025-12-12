# Display functions - HTML table generation and formatting
import pandas as pd


# Header structure for the data table
HEADER_STRUCTURE = {
    'groups': [
        {
            'name': '',
            'color': '#FFFF99',
            'subgroups': [
                {'name': 'Date', 'columns': [('Date', 'Date')]},
                {'name': 'Client Type', 'columns': [('Client Type', 'Client Type')]}
            ]
        },
        {
            'name': 'OPTION',
            'color': '#00FF00',
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
            'color': '#00FFFF',
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
            'color': '#FFFF00',
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
            'name': '',
            'color': '#90EE90',
            'subgroups': [
                {'name': 'NIFTY', 'columns': [('Nifty Diff', 'difff')]},
                {'name': 'NIFTY', 'columns': [('Nifty Spot', 'spot')]}
            ]
        },
        {
            'name': 'FUTURE',
            'color': '#FF00FF',
            'subgroups': [
                {'name': 'TOTAL LONG', 'columns': [('Future Total Long %', '%')]},
                {'name': 'TOTAL SHORT', 'columns': [('Future Total Short %', '%')]}
            ]
        }
    ]
}


def get_table_css():
    """Returns the CSS styles for the data table."""
    return """
    body {
        margin: 0;
        padding: 0;
        font-family: 'Segoe UI', Arial, sans-serif;
        background-color: transparent;
    }
    .table-wrapper {
        position: relative;
        padding-top: 50px;
    }
    .maximize-btn {
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
    }
    .maximize-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.6);
    }
    .styled-table-container {
        overflow-x: auto;
        max-height: 600px;
        overflow-y: auto;
        border: 2px solid #333;
        border-radius: 8px;
        background-color: #ffffff !important;
    }
    .styled-table-container::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    .styled-table-container::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 4px;
    }
    .styled-table-container::-webkit-scrollbar-thumb {
        background: #888;
        border-radius: 4px;
    }
    .styled-table-container::-webkit-scrollbar-thumb:hover {
        background: #555;
    }
    .styled-table-container.fullscreen {
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
    }
    .styled-table {
        border-collapse: collapse;
        width: 100%;
        font-size: 12px;
        font-family: 'Segoe UI', Arial, sans-serif;
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    .styled-table th, .styled-table td {
        padding: 6px 10px;
        text-align: center;
        border: 1px solid #333;
        white-space: nowrap;
        color: #000000 !important;
    }
    .styled-table .layer1-header {
        font-weight: bold;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
        border: 2px solid #333;
        color: #000000 !important;
    }
    .styled-table .layer2-header {
        font-weight: 600;
        font-size: 11px;
        border: 1px solid #333;
        color: #000000 !important;
    }
    .styled-table .layer3-header {
        font-weight: 500;
        font-size: 10px;
        border: 1px solid #333;
        color: #000000 !important;
    }
    .styled-table tbody tr:nth-child(even) {
        background-color: #f8f9fa !important;
    }
    .styled-table tbody tr:hover {
        background-color: #e8f4f8 !important;
    }
    .styled-table td {
        font-size: 11px;
        background-color: inherit;
        color: #000000 !important;
    }
    .styled-table td.negative-value {
        color: #dc3545 !important;
        font-weight: 600;
    }
    .styled-table .date-group-1 { background-color: #ffffff !important; }
    .styled-table .date-group-2 { background-color: #f0f8ff !important; }
    .styled-table .total-row td {
        background-color: #FFFACD !important;
        font-weight: 600;
    }
    .close-fullscreen-btn {
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
    }
    .close-fullscreen-btn:hover {
        transform: scale(1.05);
        box-shadow: 0 6px 20px rgba(220, 53, 69, 0.6);
    }
    """


def get_table_javascript():
    """Returns the JavaScript for fullscreen functionality."""
    return """
    function enterFullscreen() {
        var container = document.getElementById('table-container');
        var btn = document.getElementById('maximize-btn');
        var closeBtn = document.getElementById('close-fullscreen-btn');
        
        if (container.requestFullscreen) {
            container.requestFullscreen();
        } else if (container.webkitRequestFullscreen) {
            container.webkitRequestFullscreen();
        } else if (container.msRequestFullscreen) {
            container.msRequestFullscreen();
        }
        
        container.classList.add('fullscreen');
        closeBtn.style.display = 'block';
        btn.style.display = 'none';
    }
    
    function exitFullscreen() {
        var container = document.getElementById('table-container');
        var btn = document.getElementById('maximize-btn');
        var closeBtn = document.getElementById('close-fullscreen-btn');
        
        if (document.exitFullscreen) {
            document.exitFullscreen();
        } else if (document.webkitExitFullscreen) {
            document.webkitExitFullscreen();
        } else if (document.msExitFullscreen) {
            document.msExitFullscreen();
        }
        
        container.classList.remove('fullscreen');
        closeBtn.style.display = 'none';
        btn.style.display = 'flex';
    }
    
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
    document.addEventListener('msfullscreenchange', handleFullscreenChange);
    
    function handleFullscreenChange() {
        var container = document.getElementById('table-container');
        var btn = document.getElementById('maximize-btn');
        var closeBtn = document.getElementById('close-fullscreen-btn');
        
        if (!document.fullscreenElement && !document.webkitFullscreenElement && !document.msFullscreenElement) {
            container.classList.remove('fullscreen');
            closeBtn.style.display = 'none';
            btn.style.display = 'flex';
        }
    }
    """


def format_value_with_class(value, col):
    """Returns (formatted_string, css_class) tuple for a cell value."""
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


def generate_table_html(display_df):
    """Generates the complete HTML for the data table."""
    
    # Filter to only include columns that exist in the dataframe
    filtered_groups = []
    for group in HEADER_STRUCTURE['groups']:
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
    
    # Build HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>{get_table_css()}</style>
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
            html += f'<th colspan="{total_cols}" class="layer1-header" style="background-color: {group["color"]};">{group["name"]}</th>'
        else:
            html += f'<th colspan="{total_cols}" class="layer1-header" style="background-color: {group["color"]};"></th>'
    html += '</tr><tr>'
    
    # Add Layer 2 headers
    for group in filtered_groups:
        for subgroup in group['subgroups']:
            colspan = len(subgroup['columns'])
            html += f'<th colspan="{colspan}" class="layer2-header" style="background-color: {group["color"]}DD;">{subgroup["name"]}</th>'
    html += '</tr><tr>'
    
    # Add Layer 3 headers
    for group in filtered_groups:
        for subgroup in group['subgroups']:
            for col, label in subgroup['columns']:
                display_label = label if label else ''
                html += f'<th class="layer3-header" style="background-color: {group["color"]}99;">{display_label}</th>'
    html += '</tr></thead><tbody>'
    
    # Add data rows
    prev_date = None
    date_group = 0
    for idx, row in display_df.iterrows():
        current_date = row.get('Date', '')
        if current_date != prev_date:
            date_group = 1 - date_group
            prev_date = current_date
        
        # Check if this is a TOTAL row
        client_type = str(row.get('Client Type', '')).upper()
        is_total = 'TOTAL' in client_type
        
        row_classes = [f'date-group-{date_group + 1}']
        if is_total:
            row_classes.append('total-row')
        
        html += f'<tr class="{" ".join(row_classes)}">'
        for col in all_display_cols:
            value = row.get(col, '-')
            formatted, cell_class = format_value_with_class(value, col)
            if cell_class:
                html += f'<td class="{cell_class}">{formatted}</td>'
            else:
                html += f'<td>{formatted}</td>'
        html += '</tr>'
    
    html += f"""</tbody></table>
            <button id="close-fullscreen-btn" class="close-fullscreen-btn" onclick="exitFullscreen()">✕ Exit Fullscreen</button>
            </div>
        </div>
        <script>{get_table_javascript()}</script>
    </body>
    </html>
    """
    

    return html


def generate_calendar_html(available_dates):
    """
    Generates an HTML calendar component where 'available_dates' are highlighted green.
    """
    if not available_dates:
        return "<div>No data available</div>"
    
    # Convert dates to pandas datetime index safely
    try:
        # Explicitly create DatetimeIndex. 
        # pd.to_datetime with errors='coerce' returns NaT for failures.
        # We ensure we have a collection of Timestamps.
        converted = pd.to_datetime(available_dates, errors='coerce')
        
        # Filter NaTs using pd.notna which works on array/index/series
        valid_dates = converted[pd.notna(converted)]
        
        # Force into DatetimeIndex (even if empty) to access .dt methods and .to_period
        dates = pd.DatetimeIndex(valid_dates).sort_values()
        
    except Exception as e:
        return f"<div>Error processing dates: {str(e)}</div>"

    if dates.empty:
        return "<div>No valid dates</div>"

    # Identify month/years to display
    # We'll show distinct months present in the data
    months = dates.to_period('M').unique()
    
    calendar_html = """
    <div class="calendar-container">
    """
    
    import calendar
    
    # Sort months descending (newest first)
    for period in sorted(months, reverse=True):
        year = period.year
        month = period.month
        month_name = calendar.month_name[month]
        
        # Get matrix of days [[0,0,1,2...], [3,4...]]
        cal = calendar.monthcalendar(year, month)
        
        calendar_html += f"""
        <div class="month-card">
            <div class="month-title">{month_name} {year}</div>
            <div class="days-grid">
                <div class="day-header">M</div>
                <div class="day-header">T</div>
                <div class="day-header">W</div>
                <div class="day-header">T</div>
                <div class="day-header">F</div>
                <div class="day-header">S</div>
                <div class="day-header">S</div>
        """
        
        for week in cal:
            for day in week:
                if day == 0:
                    calendar_html += '<div class="day-cell empty"></div>'
                else:
                    # Check if this specific date is in our available_dates
                    # Construct date object
                    current_date = pd.Timestamp(year=year, month=month, day=day)
                    
                    # Check existence
                    is_active = current_date in dates
                    
                    active_class = "active" if is_active else ""
                    title_attr = f"Data available: {current_date.strftime('%d %b %Y')}" if is_active else f"{current_date.strftime('%d %b %Y')}"
                    
                    calendar_html += f'<div class="day-cell {active_class}" title="{title_attr}">{day}</div>'
        
        calendar_html += """
            </div>
        </div>
        """
        
    calendar_html += "</div>"
    
    return calendar_html


def get_display_columns():
    """Returns the ordered list of columns as they appear in the display."""
    columns = []
    for group in HEADER_STRUCTURE['groups']:
        for subgroup in group['subgroups']:
            for col, _ in subgroup['columns']:
                columns.append(col)
    return columns


def get_header_rows():
    """
    Generate the 3-layer header rows for export.
    Returns: (layer1_row, layer2_row, layer3_row)
    Layer3 contains actual column NAMES (for data matching)
    """
    layer1 = []  # Main category (OPTION, FUTURE, etc.)
    layer2 = []  # Sub-category (NET DIFF, ROC, etc.)
    layer3 = []  # Column name (actual column name for data matching)
    
    for group in HEADER_STRUCTURE['groups']:
        for subgroup in group['subgroups']:
            for col, label in subgroup['columns']:
                layer1.append(group['name'])
                layer2.append(subgroup['name'])
                layer3.append(col)  # Use column NAME, not label
    
    return layer1, layer2, layer3


def get_column_colors():
    """
    Returns a list of colors for each column (matching the display).
    """
    colors = []
    for group in HEADER_STRUCTURE['groups']:
        for subgroup in group['subgroups']:
            for col, _ in subgroup['columns']:
                colors.append(group['color'])
    return colors


def prepare_export_data(df):
    """
    Prepare DataFrame for export with formatted values and proper column order.
    Returns a DataFrame ready for CSV or Google Sheets export.
    """
    # Get display column order
    display_cols = get_display_columns()
    
    # Sort data
    df_export = df.copy()
    df_export = df_export.sort_values(by=['Date', 'Client Type'], ascending=[False, True])
    
    # Format Date column
    if 'Date' in df_export.columns:
        df_export['Date'] = pd.to_datetime(df_export['Date']).dt.strftime('%d.%m.%y')
    
    # Format numeric columns
    for col in df_export.columns:
        if col in ['Date', 'Client Type']:
            continue
        
        if df_export[col].dtype in ['float64', 'float32', 'int64', 'int32']:
            if 'Ratio' in col:
                df_export[col] = df_export[col].apply(lambda x: f'{x:.2f}' if pd.notna(x) else '')
            elif '%' in col:
                df_export[col] = df_export[col].apply(lambda x: f'{x:.2f}%' if pd.notna(x) else '')
            elif col in ['Nifty Spot', 'Nifty Diff']:
                df_export[col] = df_export[col].apply(lambda x: f'{x:.2f}' if pd.notna(x) else '')
            else:
                df_export[col] = df_export[col].apply(lambda x: f'{x:,.0f}' if pd.notna(x) else '')
    
    # Replace NaN with empty string
    df_export = df_export.fillna('')
    
    # Reorder columns to match display order
    available_cols = [col for col in display_cols if col in df_export.columns]
    # Add any remaining columns not in display order
    other_cols = [col for col in df_export.columns if col not in available_cols]
    final_cols = available_cols + other_cols
    
    df_export = df_export[final_cols]
    
    return df_export


def prepare_export_with_headers(df):
    """
    Prepare DataFrame for export with multi-row headers.
    Returns list of rows including 3 header rows + data rows.
    """
    # Get formatted data
    df_export = prepare_export_data(df)
    
    # Get header rows
    layer1, layer2, layer3 = get_header_rows()
    
    # Filter headers to only include columns in our data
    display_cols = get_display_columns()
    available_cols = [col for col in display_cols if col in df_export.columns]
    
    # Build filtered header rows
    filtered_layer1 = []
    filtered_layer2 = []
    filtered_layer3 = []
    
    for i, col in enumerate(display_cols):
        if col in available_cols:
            filtered_layer1.append(layer1[i])
            filtered_layer2.append(layer2[i])
            filtered_layer3.append(layer3[i])
    
    # Build rows
    all_rows = [
        filtered_layer1,  # Row 1: Main category
        filtered_layer2,  # Row 2: Sub-category  
        filtered_layer3,  # Row 3: Column names
    ]
    
    # Add data rows
    for _, row in df_export.iterrows():
        all_rows.append(row.tolist())
    
    return all_rows, get_column_colors()


