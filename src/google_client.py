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
            
            filtered_df = df[contractor_mask].copy()
            
            return filtered_df
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
                return pd.DataFrame(columns=['Location', 'Invoice #', 'WO #', 'Total', 'Invoice Link'])
            
            display_df = df.copy()
            
            # Process location column
            display_df['Location'] = display_df['Location'].apply(self.process_location)
            
            # Select and reorder columns for display
            display_columns = ['Location', 'Invoice #', 'WO #', 'Total', 'Invoice Link']
            display_df = display_df[display_columns]
            
            # Convert Total to numeric for calculation
            display_df['Total'] = pd.to_numeric(display_df['Total'], errors='coerce').fillna(0)
            
            return display_df
        except Exception as e:
            raise Exception(f"Failed to prepare display data: {str(e)}")
    
    def get_image_from_url(self, url):
        """Download and return image from Google Drive URL using authenticated API"""
        try:
            if pd.isna(url) or url == '':
                return None
            
            # Clean up URL (remove leading @ symbol if present)
            url = str(url).strip()
            if url.startswith('@'):
                url = url[1:]
            
            # Extract file ID from Google Drive URL - handle multiple formats
            file_id = None
            
            # Format 1: https://drive.google.com/open?id=FILE_ID
            id_match = re.search(r'[?&]id=([a-zA-Z0-9-_]+)', url)
            if id_match:
                file_id = id_match.group(1)
            else:
                # Format 2: https://drive.google.com/file/d/FILE_ID/view
                file_id_match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
                if file_id_match:
                    file_id = file_id_match.group(1)
            
            if not file_id:
                print(f"Could not extract file ID from URL: {url}")
                return None
            
            # Use Google Drive API to download the file
            try:
                # Get file metadata first to check if it exists and is accessible
                file_metadata = self.drive_client.files().get(fileId=file_id).execute()
                
                # Download the file content
                request = self.drive_client.files().get_media(fileId=file_id)
                file_content = io.BytesIO()
                
                # Use MediaIoBaseDownload to download the file
                from googleapiclient.http import MediaIoBaseDownload
                downloader = MediaIoBaseDownload(file_content, request)
                
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                
                # Reset file pointer and try to open as image
                file_content.seek(0)
                image = Image.open(file_content)
                return image
                
            except Exception as drive_error:
                print(f"Google Drive API error for file {file_id}: {str(drive_error)}")
                
                # If Drive API fails, check if it's a permissions issue
                if "403" in str(drive_error) or "Forbidden" in str(drive_error):
                    print("Permission denied - file may not be shared with your account")
                elif "404" in str(drive_error) or "Not Found" in str(drive_error):
                    print("File not found - file may have been deleted or moved")
                
                return None
            
        except Exception as e:
            print(f"Error loading image from URL '{url}': {str(e)}")
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