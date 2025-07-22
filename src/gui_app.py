# src/gui_app.py
"""
Main GUI application for invoice processing
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
from PIL import Image, ImageTk
import threading
import sys
from google_client import GoogleClient
from data_processor import DataProcessor
from credentials import SUBCONTRACTORS


class InvoiceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Invoice Processing Tool")
        self.root.geometry("1200x800")
        
        # Platform detection for cross-platform compatibility
        self.is_mac = sys.platform == "darwin"
        
        # Initialize components
        self.google_client = GoogleClient()
        self.data_processor = DataProcessor()
        
        # Data storage
        self.raw_data = None
        self.filtered_data = None
        self.display_data = None
        self.current_images = []
        self.current_image_index = 0
        self.selected_subcontractor = None
        
        # GUI components
        self.setup_gui()
        
        # Load initial data
        self.load_data()
    
    def get_copy_shortcut_text(self):
        """Get platform-appropriate copy shortcut text for display"""
        return "⌘C" if self.is_mac else "Ctrl+C"
    
    def get_copy_accelerator(self):
        """Get platform-appropriate accelerator string for menus"""
        return "Cmd+C" if self.is_mac else "Ctrl+C"
    
    def setup_copy_bindings(self):
        """Set up cross-platform keyboard and mouse bindings for copy functionality"""
        # Keyboard shortcuts for copy - bind multiple combinations for maximum compatibility
        copy_shortcuts = ['<Control-c>', '<Control-C>']  # Windows/Linux
        
        if self.is_mac:
            # Add Mac-specific shortcuts
            copy_shortcuts.extend(['<Command-c>', '<Command-C>', '<Meta-c>', '<Meta-C>'])
        
        # Bind all copy shortcuts
        for shortcut in copy_shortcuts:
            self.tree.bind(shortcut, self.copy_selected_rows)
        
        # Right-click context menu - bind multiple mouse events for compatibility
        right_click_events = ['<Button-3>']  # Standard right-click
        
        if self.is_mac:
            # Add traditional Mac right-click (Ctrl+Click)
            right_click_events.append('<Control-Button-1>')
        
        # Bind all right-click events
        for event in right_click_events:
            self.tree.bind(event, self.show_context_menu)
    
    def setup_gui(self):
        """Set up the GUI layout"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Top section - Subcontractor selection
        top_frame = ttk.Frame(main_frame)
        top_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(top_frame, text="Select Subcontractor:").grid(row=0, column=0, padx=(0, 10))
        
        self.subcontractor_var = tk.StringVar()
        self.subcontractor_combo = ttk.Combobox(
            top_frame, 
            textvariable=self.subcontractor_var,
            values=SUBCONTRACTORS,
            state="readonly",
            width=20
        )
        self.subcontractor_combo.grid(row=0, column=1, padx=(0, 10))
        self.subcontractor_combo.bind('<<ComboboxSelected>>', self.on_subcontractor_change)
        
        # Status label
        self.status_label = ttk.Label(top_frame, text="Ready", foreground="green")
        self.status_label.grid(row=0, column=2, padx=(20, 0))
        
        # Middle section - Two panels
        middle_frame = ttk.Frame(main_frame)
        middle_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        middle_frame.columnconfigure(0, weight=1)
        middle_frame.columnconfigure(1, weight=1)
        middle_frame.rowconfigure(0, weight=1)
        
        # Left panel - Table
        left_frame = ttk.LabelFrame(middle_frame, text="Invoice Data", padding="5")
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)
        
        # Table with scrollbar
        table_frame = ttk.Frame(left_frame)
        table_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        
        self.tree = ttk.Treeview(table_frame, columns=('Location', 'Invoice #', 'WO #', 'Total', 'Invoice Link'), show='headings', selectmode='extended')
        self.tree.heading('Location', text='Location')
        self.tree.heading('Invoice #', text='Invoice #')
        self.tree.heading('WO #', text='WO #')
        self.tree.heading('Total', text='Total')
        self.tree.heading('Invoice Link', text='Invoice Link')
        
        # Configure column widths
        self.tree.column('Location', width=200)
        self.tree.column('Invoice #', width=100)
        self.tree.column('WO #', width=100)
        self.tree.column('Total', width=100)
        self.tree.column('Invoice Link', width=300)
        
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Add cross-platform keyboard shortcuts and context menu for copy functionality
        self.setup_copy_bindings()
        
        # Create context menu with platform-appropriate accelerators
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(
            label="Copy Row", 
            command=self.copy_selected_rows,
            accelerator=self.get_copy_accelerator()
        )
        self.context_menu.add_command(label="Copy All", command=self.copy_all_rows)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Copy URL Only", command=self.copy_selected_url)
        
        # Total label
        self.total_label = ttk.Label(left_frame, text="Total: $0.00", font=('TkDefaultFont', 10, 'bold'))
        self.total_label.grid(row=1, column=0, pady=(5, 0), sticky=tk.W)
        
        # Help label for copy functionality with platform-appropriate shortcut
        help_text = f"💡 Tip: Select rows and press {self.get_copy_shortcut_text()} to copy, or right-click for options"
        self.help_label = ttk.Label(left_frame, text=help_text, font=('TkDefaultFont', 8), foreground='gray')
        self.help_label.grid(row=2, column=0, pady=(2, 0), sticky=tk.W)
        
        # Right panel - Image display
        right_frame = ttk.LabelFrame(middle_frame, text="Invoice Image", padding="5")
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)
        
        # Image display area
        self.image_frame = ttk.Frame(right_frame)
        self.image_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.image_frame.columnconfigure(0, weight=1)
        self.image_frame.rowconfigure(0, weight=1)
        
        self.image_label = ttk.Label(self.image_frame, text="No image available")
        self.image_label.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Image navigation
        nav_frame = ttk.Frame(right_frame)
        nav_frame.grid(row=1, column=0, pady=(5, 0))
        
        self.prev_button = ttk.Button(nav_frame, text="◀ Previous", command=self.prev_image)
        self.prev_button.grid(row=0, column=0, padx=(0, 5))
        
        self.image_counter_label = ttk.Label(nav_frame, text="0 / 0")
        self.image_counter_label.grid(row=0, column=1, padx=5)
        
        self.next_button = ttk.Button(nav_frame, text="Next ▶", command=self.next_image)
        self.next_button.grid(row=0, column=2, padx=(5, 0))
        
        # Bottom section - Action buttons
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        self.pdf_button = ttk.Button(bottom_frame, text="Generate PDF", command=self.generate_pdf)
        self.pdf_button.grid(row=0, column=0, padx=(0, 10))
        
        self.refresh_button = ttk.Button(bottom_frame, text="Refresh Data", command=self.refresh_data)
        self.refresh_button.grid(row=0, column=1)
        
        # Progress bar
        self.progress = ttk.Progressbar(bottom_frame, mode='indeterminate')
        self.progress.grid(row=0, column=2, padx=(20, 0), sticky=(tk.W, tk.E))
        bottom_frame.columnconfigure(2, weight=1)
    
    def update_status(self, message, color="black"):
        """Update status label"""
        self.status_label.config(text=message, foreground=color)
        self.root.update_idletasks()
    
    def start_loading(self):
        """Start loading animation"""
        self.progress.start()
        self.update_status("Loading...", "orange")
    
    def stop_loading(self):
        """Stop loading animation"""
        self.progress.stop()
        self.update_status("Ready", "green")
    
    def load_data(self):
        """Load data from Google Sheets in background thread"""
        def load_worker():
            try:
                self.start_loading()
                
                # Load raw data
                self.raw_data = self.google_client.load_sheet_data()
                
                # Filter data
                self.filtered_data = self.google_client.filter_invoice_data(self.raw_data)
                
                self.stop_loading()
                
            except Exception as e:
                self.stop_loading()
                messagebox.showerror("Error", f"Failed to load data: {str(e)}")
        
        thread = threading.Thread(target=load_worker)
        thread.daemon = True
        thread.start()
    
    def on_subcontractor_change(self, event=None):
        """Handle subcontractor selection change"""
        self.selected_subcontractor = self.subcontractor_var.get()
        
        if not self.selected_subcontractor or self.filtered_data is None:
            return
        
        try:
            # Filter by subcontractor
            contractor_data = self.google_client.filter_by_subcontractor(
                self.filtered_data, self.selected_subcontractor
            )
            
            # Prepare display data
            self.display_data = self.google_client.prepare_display_data(contractor_data)
            
            # Update table
            self.update_table()
            
            # Load images
            self.load_images(contractor_data)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to filter data: {str(e)}")
            print(f"DEBUG: Exception in on_subcontractor_change: {str(e)}")
    
    def update_table(self):
        """Update the table display"""
        # Clear existing data
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if self.display_data is None or self.display_data.empty:
            self.total_label.config(text="Total: $0.00")
            return
        
        # Add data to table
        for _, row in self.display_data.iterrows():
            self.tree.insert('', 'end', values=(
                row['Location'],
                row['Invoice #'],
                row['WO #'],
                self.data_processor.format_currency(row['Total']),
                row['Invoice Link'] # Added Invoice Link
            ))
        
        # Update total
        total = self.google_client.calculate_total_sum(self.display_data)
        self.total_label.config(text=f"Total: {self.data_processor.format_currency(total)}")
    
    def load_images(self, contractor_data):
        """Load images in background thread"""
        def load_worker():
            try:
                self.start_loading()
                
                # Get image URLs
                image_urls = self.data_processor.get_image_urls(contractor_data)
                
                # Load images
                self.current_images = []
                for i, url in enumerate(image_urls):
                    image = self.google_client.get_image_from_url(url)
                    self.current_images.append(image)
                
                self.current_image_index = 0
                
                # Update image display
                self.root.after(0, self.update_image_display)
                
                self.stop_loading()
                
            except Exception as e:
                self.stop_loading()
                messagebox.showerror("Error", f"Failed to load images: {str(e)}")
                print(f"DEBUG: GUI - Exception in load_images: {str(e)}")
        
        thread = threading.Thread(target=load_worker)
        thread.daemon = True
        thread.start()
    
    def update_image_display(self):
        """Update the image display"""
        if not self.current_images:
            self.image_label.config(image='', text="No images available")
            self.image_counter_label.config(text="0 / 0")
            self.prev_button.config(state='disabled')
            self.next_button.config(state='disabled')
            return
        
        # Update counter
        total_images = len(self.current_images)
        current_num = self.current_image_index + 1
        self.image_counter_label.config(text=f"{current_num} / {total_images}")
        
        # Update button states
        self.prev_button.config(state='normal' if self.current_image_index > 0 else 'disabled')
        self.next_button.config(state='normal' if self.current_image_index < total_images - 1 else 'disabled')
        
        # Display current image
        current_image = self.current_images[self.current_image_index]
        
        if current_image is None:
            self.image_label.config(image='', text="Image not available")
            return
        
        # Resize image to fit display
        display_width = 400
        display_height = 500
        
        # Calculate scaling
        img_width, img_height = current_image.size
        scale_width = display_width / img_width
        scale_height = display_height / img_height
        scale = min(scale_width, scale_height)
        
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        # Resize and display
        resized_image = current_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(resized_image)
        
        self.image_label.config(image=photo, text="")
        self.image_label.image = photo  # Keep a reference
    
    def prev_image(self):
        """Show previous image"""
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.update_image_display()
    
    def next_image(self):
        """Show next image"""
        if self.current_image_index < len(self.current_images) - 1:
            self.current_image_index += 1
            self.update_image_display()
    
    def generate_pdf(self):
        """Generate PDF with current data"""
        if self.display_data is None or self.display_data.empty:
            messagebox.showwarning("Warning", "No data to generate PDF")
            return
        
        if not self.selected_subcontractor:
            messagebox.showwarning("Warning", "Please select a subcontractor")
            return
        
        def pdf_worker():
            try:
                self.start_loading()
                
                # Generate PDF
                filepath = self.data_processor.generate_pdf(
                    self.display_data,
                    self.current_images,
                    self.selected_subcontractor
                )
                
                self.stop_loading()
                
                # Show success message on main thread
                self.root.after(0, lambda: messagebox.showinfo("Success", f"PDF generated successfully:\n{filepath}"))
                
            except Exception as e:
                self.stop_loading()
                # Capture the error message before the lambda
                error_msg = str(e)
                # Show error message on main thread
                self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to generate PDF: {error_msg}"))
        
        thread = threading.Thread(target=pdf_worker)
        thread.daemon = True
        thread.start()
    
    def refresh_data(self):
        """Refresh all data from Google Sheets"""
        # Remember current selection
        current_selection = self.selected_subcontractor
        
        def refresh_worker():
            try:
                self.start_loading()
                
                # Reload data
                self.raw_data = self.google_client.load_sheet_data()
                self.filtered_data = self.google_client.filter_invoice_data(self.raw_data)
                
                # Restore selection and update display
                if current_selection:
                    self.root.after(0, lambda: self.restore_selection(current_selection))
                
                self.stop_loading()
                
            except Exception as e:
                self.stop_loading()
                messagebox.showerror("Error", f"Failed to refresh data: {str(e)}")
        
        thread = threading.Thread(target=refresh_worker)
        thread.daemon = True
        thread.start()
    
    def restore_selection(self, subcontractor):
        """Restore subcontractor selection after refresh"""
        self.subcontractor_var.set(subcontractor)
        self.on_subcontractor_change()
    
    def copy_selected_rows(self, event=None):
        """Copy selected rows to clipboard"""
        try:
            selected_items = self.tree.selection()
            if not selected_items:
                return
            
            # Get headers
            headers = ['Location', 'Invoice #', 'WO #', 'Total', 'Invoice Link']
            
            # Build clipboard content
            clipboard_content = []
            clipboard_content.append('\t'.join(headers))  # Tab-separated headers
            
            for item in selected_items:
                values = self.tree.item(item, 'values')
                clipboard_content.append('\t'.join(str(v) for v in values))
            
            # Copy to clipboard
            clipboard_text = '\n'.join(clipboard_content)
            self.root.clipboard_clear()
            self.root.clipboard_append(clipboard_text)
            
            # Show feedback
            self.update_status(f"Copied {len(selected_items)} row(s) to clipboard", "blue")
            self.root.after(2000, lambda: self.update_status("Ready", "green"))
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy: {str(e)}")
    
    def copy_all_rows(self, event=None):
        """Copy all visible rows to clipboard"""
        try:
            if self.display_data is None or self.display_data.empty:
                messagebox.showinfo("Info", "No data to copy")
                return
            
            # Get headers
            headers = ['Location', 'Invoice #', 'WO #', 'Total', 'Invoice Link']
            
            # Build clipboard content
            clipboard_content = []
            clipboard_content.append('\t'.join(headers))  # Tab-separated headers
            
            # Add all rows
            for _, row in self.display_data.iterrows():
                row_data = [
                    str(row['Location']),
                    str(row['Invoice #']),
                    str(row['WO #']),
                    self.data_processor.format_currency(row['Total']),
                    str(row['Invoice Link'])
                ]
                clipboard_content.append('\t'.join(row_data))
            
            # Copy to clipboard
            clipboard_text = '\n'.join(clipboard_content)
            self.root.clipboard_clear()
            self.root.clipboard_append(clipboard_text)
            
            # Show feedback
            self.update_status(f"Copied all {len(self.display_data)} row(s) to clipboard", "blue")
            self.root.after(2000, lambda: self.update_status("Ready", "green"))
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy all rows: {str(e)}")
    
    def copy_selected_url(self, event=None):
        """Copy selected row's URL to clipboard"""
        try:
            selected_items = self.tree.selection()
            if not selected_items:
                return
            
            # Get the first selected item's URL (last column)
            item = selected_items[0]
            values = self.tree.item(item, 'values')
            
            if len(values) >= 5:  # Make sure URL column exists
                url = values[4]  # Invoice Link is the 5th column (index 4)
                
                # Copy URL to clipboard
                self.root.clipboard_clear()
                self.root.clipboard_append(str(url))
                
                # Show feedback
                self.update_status("URL copied to clipboard", "blue")
                self.root.after(2000, lambda: self.update_status("Ready", "green"))
            else:
                messagebox.showinfo("Info", "No URL found in selected row")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy URL: {str(e)}")
    
    def show_context_menu(self, event):
        """Show context menu on right-click"""
        try:
            # Select the item under the cursor
            item = self.tree.identify_row(event.y)
            if item:
                self.tree.selection_set(item)
                self.tree.focus(item)
            
            # Show context menu
            self.context_menu.post(event.x_root, event.y_root)
            
        except Exception as e:
            print(f"Error showing context menu: {str(e)}")


def main():
    """Main function to run the application"""
    root = tk.Tk()
    app = InvoiceApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()