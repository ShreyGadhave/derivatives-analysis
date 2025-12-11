# 📊 Derivatives Data Analysis Tool

A powerful Streamlit application for analyzing NSE Derivatives Participant-wise Open Interest data with **persistent cloud storage**.

## ✨ Features

- 📁 **Upload Daily Files** - Upload CSV/Excel files from NSE
- 🔄 **Auto-Detect Dates** - Automatically extracts dates from file names or content
- 📈 **Auto-Fetch Nifty Price** - Uses yfinance to fetch historical Nifty 50 closing prices
- 📊 **3-Layer Headers** - Excel-like multi-level headers (OPTION, FUTURE, FUTURE STOCK)
- 🔴 **Negative Values** - Highlighted in red for quick identification
- ⛶ **Fullscreen Mode** - Maximize table to full browser window
- 💾 **Persistent Cloud Database** - Data stored in Google Sheets (survives app restarts!)
- 📥 **Download CSV** - Export the complete processed database

## 🚀 Quick Start (Local Development)

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

## ☁️ Deployment on Streamlit Cloud

### Step 1: Set Up Google Sheets API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable these APIs:
   - Google Sheets API
   - Google Drive API
4. Create a Service Account:
   - Go to "IAM & Admin" → "Service Accounts"
   - Click "Create Service Account"
   - Download the JSON key file

### Step 2: Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/derivatives-analysis.git
git push -u origin main
```

### Step 3: Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "New app"
3. Select your repository
4. Set Main file path: `app.py`
5. Click "Advanced settings" → "Secrets"
6. Add your secrets (see below)
7. Click "Deploy!"

### Step 4: Configure Secrets

In Streamlit Cloud, go to your app's settings and add these secrets:

```toml
spreadsheet_name = "DerivativesDB"
share_email = "your-email@gmail.com"

[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "service-account@project.iam.gserviceaccount.com"
client_id = "123456789"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
```

## 📊 Calculated Metrics

### OPTION Section
- NET DIFF, ROC (Rate of Change)
- Absolute Change (Call Index, Put Index)
- NET, NET CALL, NET PUT

### FUTURE Section
- NET, ROC
- Absolute Change (LONG, SHORT)
- L/S Ratio, Long %, Short %

### FUTURE STOCK Section
- NET, ROC
- Absolute Change (LONG, SHORT)
- L/S Ratio, Long %, Short %

### NIFTY Section
- Nifty Diff, Nifty Spot

## 📁 Data Format

Upload participant-wise OI data files from NSE with columns:
- Date, Client Type
- Future Index Long/Short
- Future Stock Long/Short
- Option Index Call/Put Long/Short

## 🔒 Data Persistence

| Mode | Storage | Persistence |
|------|---------|-------------|
| **Local** | `derivative_data_db.csv` | Until file deleted |
| **Cloud** | Google Sheets | ✅ Permanent |

The app automatically detects if it's running on Streamlit Cloud and uses Google Sheets for storage. Locally, it falls back to CSV.

## 📝 License

MIT License
