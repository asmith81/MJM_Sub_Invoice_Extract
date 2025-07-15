# src/data_processor.py
"""
Data processing and PDF generation for invoice application
"""

import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.units import inch
from datetime import datetime
import io
from PIL import Image
import os


class DataProcessor:
    def __init__(self):
        self.current_data = None
        self.current_subcontractor = None
        self.full_data = None
    
    def set_data(self, df, subcontractor_name):
        """Set current working data"""
        self.current_data = df
        self.current_subcontractor = subcontractor_name
    
    def set_full_data(self, df):
        """Set full filtered data for reference"""
        self.full_data = df
    
    def get_table_data_for_pdf(self, display_df):
        """Prepare table data for PDF generation"""
        if display_df.empty:
            return []
        
        # Create table data with headers
        table_data = []
        headers = ['Location', 'Invoice #', 'WO #', 'Total', 'Invoice Link']
        table_data.append(headers)
        
        # Add data rows
        for _, row in display_df.iterrows():
            # Create clickable link for Invoice Link
            from reportlab.platypus import Paragraph
            from reportlab.lib.styles import getSampleStyleSheet
            
            styles = getSampleStyleSheet()
            invoice_link = row['Invoice Link']
            
            # Create a clickable link paragraph
            if pd.notna(invoice_link) and invoice_link != '':
                link_text = f'<a href="{invoice_link}">View Invoice</a>'
                link_paragraph = Paragraph(link_text, styles['Normal'])
            else:
                link_paragraph = "No Link"
            
            table_data.append([
                str(row['Location']),
                str(row['Invoice #']),
                str(row['WO #']),
                f"${row['Total']:.2f}",
                link_paragraph
            ])
        
        # Add total row
        total_sum = display_df['Total'].sum()
        table_data.append(['', '', '', 'TOTAL:', f"${total_sum:.2f}"])
        
        return table_data
    
    def generate_pdf(self, display_df, images, subcontractor_name, output_dir=None):
        """Generate PDF with table and images"""
        try:
            # Set default output directory relative to project root
            if output_dir is None:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.dirname(script_dir)
                output_dir = os.path.join(project_root, "pdfs")
            
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate filename
            date_str = datetime.now().strftime("%Y-%m-%d")
            filename = f"{subcontractor_name}_Invoice_{date_str}.pdf"
            filepath = os.path.join(output_dir, filename)
            
            # Create PDF document
            doc = SimpleDocTemplate(filepath, pagesize=letter)
            story = []
            styles = getSampleStyleSheet()
            
            # Title
            title = Paragraph(f"Invoice Summary - {subcontractor_name.title()}", styles['Title'])
            story.append(title)
            story.append(Spacer(1, 12))
            
            # Date
            date_para = Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal'])
            story.append(date_para)
            story.append(Spacer(1, 12))
            
            # Table
            if not display_df.empty:
                table_data = self.get_table_data_for_pdf(display_df)
                table = Table(table_data)
                
                # Table styling
                table_style = TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 14),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
                    ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
                    ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ])
                table.setStyle(table_style)
                story.append(table)
            
            # Add images on separate pages
            for i, image in enumerate(images):
                if image is not None:
                    story.append(Spacer(1, 12))
                    
                    # Convert PIL Image to ReportLab Image
                    img_buffer = io.BytesIO()
                    image.save(img_buffer, format='PNG')
                    img_buffer.seek(0)
                    
                    # Calculate image size to fit page
                    img_width, img_height = image.size
                    max_width = 7 * inch
                    max_height = 9 * inch
                    
                    # Scale image to fit
                    scale_width = max_width / img_width
                    scale_height = max_height / img_height
                    scale = min(scale_width, scale_height)
                    
                    final_width = img_width * scale
                    final_height = img_height * scale
                    
                    # Add image to story
                    rl_image = RLImage(img_buffer, width=final_width, height=final_height)
                    story.append(rl_image)
            
            # Build PDF
            doc.build(story)
            
            return filepath
            
        except Exception as e:
            raise Exception(f"Failed to generate PDF: {str(e)}")
    
    def validate_data(self, df):
        """Validate that the DataFrame has required columns"""
        print(f"DEBUG: Validating data with columns: {df.columns.tolist()}")
        
        required_columns = ['Location', 'Invoice #', 'WO #', 'Total']
        
        # Check each required column individually
        for col in required_columns:
            if col in df.columns:
                print(f"DEBUG: ✓ Found required column: '{col}'")
            else:
                print(f"DEBUG: ✗ Missing required column: '{col}'")
                # Look for similar column names
                similar_cols = [c for c in df.columns if col.lower() in c.lower()]
                if similar_cols:
                    print(f"DEBUG: Similar columns found: {similar_cols}")
        
        # Check for image column (try different possible names)
        image_column_exists = ('Invoice Link' in df.columns or 
                             'invoice link' in df.columns or 
                             'Picture of Completed Job' in df.columns)
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise Exception(f"Missing required columns: {missing_columns}")
        
        # Check specifically for Invoice Link column
        if 'Invoice Link' not in df.columns:
            print("Warning: 'Invoice Link' column not found - PDF links will not work")
        
        return True
    
    def get_image_urls(self, df):
        """Extract image URLs from DataFrame"""
        if df.empty:
            return []
        
        # Check if the column exists (try different possible column names)
        if 'Invoice Link' in df.columns:
            column_name = 'Invoice Link'
        elif 'invoice link' in df.columns:
            column_name = 'invoice link'
        elif 'Picture of Completed Job' in df.columns:
            column_name = 'Picture of Completed Job'
        else:
            print("Warning: No image link column found ('Invoice Link', 'invoice link', or 'Picture of Completed Job')")
            return []
        
        urls = df[column_name].tolist()
        filtered_urls = [url for url in urls if pd.notna(url) and url != '']
        
        return filtered_urls
    
    def format_currency(self, amount):
        """Format currency for display"""
        try:
            return f"${float(amount):.2f}"
        except (ValueError, TypeError):
            return "$0.00"