# main.py
"""
Invoice Processing Application
Entry point for the invoice automation tool
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox

# Add src directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from gui_app import InvoiceApp
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all required packages are installed:")
    print("pip install pandas gspread google-auth google-auth-oauthlib google-auth-httplib2")
    print("pip install google-api-python-client pillow reportlab")
    sys.exit(1)


def check_credentials():
    """Check if credentials are properly configured"""
    try:
        from credentials import OAUTH_CREDENTIALS_FILE, OAUTH_CLIENT_CREDENTIALS, SHEET_ID
        import os
        
        # Check if oauth.json file exists or manual credentials are set
        oauth_file_exists = os.path.exists(OAUTH_CREDENTIALS_FILE)
        manual_creds_set = not OAUTH_CLIENT_CREDENTIALS.get('client_id', '').startswith('your-')
        
        if not oauth_file_exists and not manual_creds_set:
            messagebox.showerror(
                "Configuration Error",
                "Please set up your OAuth credentials:\n\n"
                "Option 1: Place your oauth.json file in the project directory\n"
                "Option 2: Update OAUTH_CLIENT_CREDENTIALS in src/credentials.py\n\n"
                "Your oauth.json should contain:\n"
                "- client_id\n"
                "- client_secret\n"
                "- auth_uri\n"
                "- token_uri"
            )
            return False
            
        if not SHEET_ID or SHEET_ID.startswith('your-'):
            messagebox.showerror(
                "Configuration Error",
                "Please set your Google Sheet ID in src/credentials.py\n\n"
                "Find the Sheet ID in your Google Sheets URL:\n"
                "https://docs.google.com/spreadsheets/d/[SHEET_ID]/edit"
            )
            return False
            
        return True
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load credentials: {str(e)}")
        return False


def main():
    """Main application entry point"""
    print("Starting Invoice Processing Application...")
    
    # Create main window
    root = tk.Tk()
    root.withdraw()  # Hide main window initially
    
    # Check credentials
    if not check_credentials():
        root.destroy()
        return
    
    try:
        # Show main window and start application
        root.deiconify()
        app = InvoiceApp(root)
        
        print("Application started successfully!")
        root.mainloop()
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to start application: {str(e)}")
        print(f"Error: {e}")
    
    print("Application closed.")


if __name__ == "__main__":
    main()