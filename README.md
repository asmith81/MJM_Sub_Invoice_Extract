# Invoice Processing Application

A Python GUI application for automating invoice workflow processing with Google Sheets and Google Drive integration.

## Features

- **Google Sheets Integration**: Automatically loads invoice data from Google Sheets
- **Smart Filtering**: Filters invoices by approval status and payment status
- **Subcontractor Management**: Filter and view invoices by subcontractor
- **Image Display**: View invoice images stored in Google Drive
- **PDF Generation**: Create comprehensive PDF reports with tables and images
- **Real-time Updates**: Refresh data from Google Sheets without restarting

## Setup Instructions

### 1. Install Python Requirements

```bash
pip install -r requirements.txt
```

### 2. Google API Setup

1. **Create a Google Cloud Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one

2. **Enable Required APIs**:
   - Google Sheets API
   - Google Drive API

3. **Create OAuth Client**:
   - Go to "APIs & Credentials" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop application"
   - Download the JSON file (this is your `oauth.json`)

4. **Share Google Sheet**:
   - Share your Google Sheet with your Google account email
   - Give "Viewer" permissions

### 3. Configure Credentials

**Option 1: Use oauth.json file (Recommended)**
1. Place your downloaded `oauth.json` file in the project root directory
2. Update `src/credentials.py`:
   ```python
   OAUTH_CREDENTIALS_FILE = "oauth.json"  # Path to your oauth.json
   SHEET_ID = "your-actual-google-sheet-id"
   SHEET_NAME = "Your Sheet Name"
   ```

**Option 2: Manual configuration**
Edit `src/credentials.py` and update:
```python
OAUTH_CLIENT_CREDENTIALS = {
    "client_id": "your-client-id.apps.googleusercontent.com",
    "client_secret": "your-client-secret",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "redirect_uris": ["http://localhost"]
}

SHEET_ID = "your-actual-google-sheet-id"
SHEET_NAME = "Your Sheet Name"
```

### 4. First Run Authentication

When you first run the application:
1. A browser window will open automatically
2. Sign in with your Google account
3. Grant permissions to access Google Sheets and Drive
4. The app will save your authentication token for future use

**Note**: The authentication token is saved in `token.json` - keep this file secure and don't share it.

Your Google Sheet must have these columns:
- **Invoice #**: Invoice number
- **Approval Status**: Should contain "aprobado" or "approved" (case-insensitive)
- **Invoice Status**: Should be empty/null for unpaid invoices
- **Invoice Timestamp**: For sorting (date format)
- **Name**: Subcontractor name
- **WO #**: Work order number
- **Invoice Link**: URL to invoice document
- **Total**: Invoice amount
- **Job Completion Status**: Status of job
- **Picture of Completed Job**: Google Drive URL to invoice image
- **Location**: Job location
- **Description**: Job description
- **Picture of WO**: Work order image
- **MJM Invoiced Date**: Invoice date
- **Marcelo Notes**: Notes field
- **Date WO Assigned**: Assignment date
- **Perla Notes**: Notes field
- **Cristian Notes**: Notes field

## Usage

### 1. Start the Application

```bash
python main.py
```

**First time setup**: A browser will open for Google authentication. Sign in and grant permissions.

### 2. Using the Interface

1. **Select Subcontractor**: Choose from the dropdown menu
2. **View Data**: Review the filtered invoice table on the left
3. **Browse Images**: Use arrow buttons to navigate through invoice images
4. **Generate PDF**: Click "Generate PDF" to create a report
5. **Refresh Data**: Click "Refresh Data" to reload from Google Sheets

### 3. PDF Output

Generated PDFs include:
- Summary table with location, invoice #, WO #, and totals
- Individual invoice images on separate pages
- Automatic filename: `{SubcontractorName}_Invoice_{YYYY-MM-DD}.pdf`

## File Structure

```
invoice-app/
├── main.py                 # Application entry point
├── oauth.json             # Your OAuth credentials (download from Google Cloud)
├── token.json             # Saved authentication token (created automatically)
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── src/
│   ├── credentials.py     # OAuth configuration
│   ├── google_client.py   # Google Sheets/Drive integration
│   ├── data_processor.py  # Data processing and PDF generation
│   └── gui_app.py         # Main GUI application
└── pdfs/                  # Generated PDF output (created automatically)
```

## Troubleshooting

### Common Issues

1. **Authentication Error**:
   - Verify credentials.py is properly configured
   - Check that the service account has access to the Google Sheet

2. **Missing Columns**:
   - Ensure your Google Sheet has all required columns
   - Check column names match exactly (case-sensitive)

3. **Image Loading Issues**:
   - Verify Google Drive URLs are accessible
   - Check that images are shared properly

4. **Import Errors**:
   - Install all requirements: `pip install -r requirements.txt`
   - Check Python version (3.7+ recommended)

### Getting Help

If you encounter issues:
1. Check the console output for error messages
2. Verify your Google Sheet format matches the requirements
3. Test your Google API credentials independently

## Subcontractor List

The application supports these subcontractors:
- pelico
- htin
- frank
- harold
- marco
- gustavo
- antonio
- nahun
- edgar
- 24/7 tech
- josue cruz

To modify this list, edit the `SUBCONTRACTORS` array in `src/credentials.py`.

## License

This application is for internal use. Ensure compliance with Google API terms of service.