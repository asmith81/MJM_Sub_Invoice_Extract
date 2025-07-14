# src/google_client.py
"""
Google Sheets and Drive API client for invoice data retrieval
"""

import pandas as pd
import gspread
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import requests
from PIL import Image
import io
import re
import os
import json
from credentials import (
    OAUTH_CREDENTIALS_FILE, OAUTH_CLIENT_CREDENTIALS, SHEET_ID, 
    SHEET_NAME, SCOPES, TOKEN_FILE
)


class GoogleClient:
    def __init__(self):
        self.credentials = None
        self.sheets_client = None
        self.drive_client = None
        self.authenticate()
    
    def authenticate(self):
        """Authenticate with Google APIs using OAuth flow"""
        try:
            creds = None
            
            # Check if token file exists (stored credentials)
            if os.path.exists(TOKEN_FILE):
                creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            
            # If there are no (valid) credentials available, let the user log in
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    # Try to load from oauth.json file first
                    if os.path.exists(OAUTH_CREDENTIALS_FILE):
                        flow = InstalledAppFlow.from_client_secrets_file(
                            OAUTH_CREDENTIALS_FILE, SCOPES
                        )
                    else:
                        # Use manually entered credentials
                        client_config = {
                            "installed": OAUTH_CLIENT_CREDENTIALS
                        }
                        flow = InstalledAppFlow.from_client_config(
                            client_config, SCOPES
                        )
                    
                    # Run local server for OAuth flow
                    creds = flow.run_local_server(port=0)
                
                # Save the credentials for the next run
                with open(TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
            
            self.credentials = creds
            
            # Initialize clients
            self.sheets_client = gspread.authorize(self.credentials)
            self.drive_client = build('drive', 'v3', credentials=self.credentials)
            
            return True
            
        except Exception as e:
            raise Exception(f"Authentication failed: {str(e)}")
    
    def load_sheet_data(self):
        """Load data from Google Sheet into pandas DataFrame"""
        try:
            sheet = self.sheets_client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
            data = sheet.get_all_records()
            df = pd.DataFrame(data)
            
            # Clean column names (remove extra spaces)
            df.columns = df.columns.str.strip()
            
            return df
        except Exception as e:
            raise Exception(f"Failed to load sheet data: {str(e)}")
    
    def filter_invoice_data(self, df):
        """Filter DataFrame based on approval status and payment status"""
        try:
            # Clean and normalize the data
            df['Approval Status'] = df['Approval Status'].astype(str).str.strip().str.lower()
            df['Invoice Status'] = df['Invoice Status'].astype(str).str.strip()
            df['Name'] = df['Name'].astype(str).str.strip().str.lower()
            
            # Filter conditions
            approved_mask = df['Approval Status'].isin(['aprobado', 'approved'])
            unpaid_mask = df['Invoice Status'].isin(['', 'nan', 'None']) | df['Invoice Status'].isna()
            
            # Additional check for whitespace-only values
            whitespace_mask = df['Invoice Status'].str.strip() == ''
            unpaid_mask = unpaid_mask | whitespace_mask
            
            filtered_df = df[approved_mask & unpaid_mask].copy()
            
            # Sort by Invoice Timestamp (ascending)
            if 'Invoice Timestamp' in filtered_df.columns:
                filtered_df['Invoice Timestamp'] = pd.to_datetime(
                    filtered_df['Invoice Timestamp'], errors='coerce'
                )
                filtered_df = filtered_df.sort_values('Invoice Timestamp')
            
            return filtered_df
        except Exception as e:
            raise Exception(f"Failed to filter data: {str(e)}")
    
    def filter_by_subcontractor(self, df, subcontractor_name):
        """Filter DataFrame by subcontractor name"""
        try:
            contractor_mask = df['Name'].str.contains(
                subcontractor_name.lower(), case=False, na=False
            )
            return df[contractor_mask].copy()
        except Exception as e:
            raise Exception(f"Failed to filter by subcontractor: {str(e)}")
    
    def process_location(self, location):
        """Process location string to remove Washington, DC portion"""
        if pd.isna(location) or location == '':
            return ''
        
        # Remove ", Washington, District of Columbia" and zipcode
        pattern = r',\s*Washington,\s*District of Columbia\s*\d{5}.*'
        cleaned = re.sub(pattern, '', str(location), flags=re.IGNORECASE)
        return cleaned.strip()
    
    def prepare_display_data(self, df):
        """Prepare data for GUI display"""
        try:
            if df.empty:
                return pd.DataFrame(columns=['Location', 'Invoice #', 'WO #', 'Total'])
            
            display_df = df.copy()
            
            # Process location column
            display_df['Location'] = display_df['Location'].apply(self.process_location)
            
            # Select and reorder columns for display
            display_columns = ['Location', 'Invoice #', 'WO #', 'Total']
            display_df = display_df[display_columns]
            
            # Convert Total to numeric for calculation
            display_df['Total'] = pd.to_numeric(display_df['Total'], errors='coerce').fillna(0)
            
            return display_df
        except Exception as e:
            raise Exception(f"Failed to prepare display data: {str(e)}")
    
    def get_image_from_url(self, url):
        """Download and return image from Google Drive URL"""
        try:
            if pd.isna(url) or url == '':
                return None
            
            # Extract file ID from Google Drive URL
            file_id_match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
            if not file_id_match:
                return None
            
            file_id = file_id_match.group(1)
            
            # Get downloadable link
            download_url = f"https://drive.google.com/uc?id={file_id}"
            
            # Download image
            response = requests.get(download_url, timeout=10)
            response.raise_for_status()
            
            # Open and return PIL Image
            image = Image.open(io.BytesIO(response.content))
            return image
            
        except Exception as e:
            print(f"Error loading image: {str(e)}")
            return None
    
    def calculate_total_sum(self, df):
        """Calculate sum of Total column"""
        try:
            if df.empty:
                return 0
            return df['Total'].sum()
        except Exception as e:
            print(f"Error calculating total: {str(e)}")
            return 0