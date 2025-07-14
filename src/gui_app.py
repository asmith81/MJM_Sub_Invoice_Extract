# src/gui_app.py
"""
Main GUI application for invoice processing
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
from PIL import Image, ImageTk
import threading
from .google_client import GoogleClient
from .data_processor import DataProcessor
from .credentials import SUBCONTRACTORS


class InvoiceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Invoice Processing Tool")
        self.root.geometry("1200x800")
        
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
        
        self.tree = ttk.Treeview(table_frame, columns=('Location', 'Invoice #', 'WO #', 'Total'), show='headings')
        self.tree.heading('Location', text='Location')
        self.tree.heading('Invoice #', text='Invoice #')
        self.tree.heading('WO #', text='WO #')
        self.tree.heading('Total', text='Total')
        
        # Configure column widths
        self.tree.column('Location', width=200)
        self.tree.column('Invoice #', width=100)
        self.tree.column('WO #', width=100)
        self.tree.column('Total', width=100)
        
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Total label
        self.total_label = ttk.Label(left_frame, text="Total: $0.00", font=('TkDefaultFont', 10, 'bold'))
        self.total_label.grid(row=1, column=0, pady=(5, 0), sticky=tk.W)
        
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
                self.data_processor.format_currency(row['Total'])
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
                for url in image_urls:
                    image = self.google_client.get_image_from_url(url)
                    self.current_images.append(image)
                
                self.current_image_index = 0
                
                # Update image display
                self.root.after(0, self.update_image_display)
                
                self.stop_loading()
                
            except Exception as e:
                self.stop_loading()
                messagebox.showerror("Error", f"Failed to load images: {str(e)}")
        
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
        
        try:
            self.start_loading()
            
            # Generate PDF
            filepath = self.data_processor.generate_pdf(
                self.display_data,
                self.current_images,
                self.selected_subcontractor
            )
            
            self.stop_loading()
            messagebox.showinfo("Success", f"PDF generated successfully:\n{filepath}")
            
        except Exception as e:
            self.stop_loading()
            messagebox.showerror("Error", f"Failed to generate PDF: {str(e)}")
    
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


def main():
    """Main function to run the application"""
    root = tk.Tk()
    app = InvoiceApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()