# src/credentials.py
"""
OAuth credentials and configuration for Google Sheets/Drive access
"""

# Path to your oauth.json file - update this path
OAUTH_CREDENTIALS_FILE = "oauth.json"  # Update with actual path to your oauth.json

# OR manually enter your OAuth client credentials here:
OAUTH_CLIENT_CREDENTIALS = {
    "client_id": "1042497359356-d1sgm12rerfdlc3v1vvsutnnrs2d0him.apps.googleusercontent.com",
    "client_secret": "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",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "redirect_uris": ["http://localhost"]
}

# Google Sheets configuration
SHEET_ID = "1gdjS8gaGFaQs6J09yv7SeiYKy6ZdOLnXoZfIrQQpGoY"
SHEET_NAME = "Estimates/Inovices Status"  # Update with your actual sheet name

# OAuth scopes required
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]

# Token storage file (will be created automatically)
TOKEN_FILE = "token.json"

# Subcontractor list
SUBCONTRACTORS = [
    "pelico", "htin", "frank", "harold", "marco", "gustavo", 
    "antonio", "nahun", "edgar", "24/7 tech", "josue cruz"
]