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
    
    def optimize_image_for_pdf(self, image, max_width=800, max_height=1000):
        """Optimize image for PDF generation with orientation handling"""
        try:
            if image is None:
                return None
            
            # Handle EXIF orientation if present
            try:
                from PIL.ExifTags import ORIENTATION
                exif = image._getexif()
                if exif is not None:
                    orientation = exif.get(0x0112)
                    if orientation == 3:
                        image = image.rotate(180, expand=True)
                    elif orientation == 6:
                        image = image.rotate(270, expand=True)
                    elif orientation == 8:
                        image = image.rotate(90, expand=True)
            except (AttributeError, TypeError, ImportError):
                # No EXIF data, old PIL version, or missing ExifTags
                pass
            
            # Convert to RGB if not already (handles RGBA, grayscale, etc.)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Get original dimensions
            original_width, original_height = image.size
            
            # Check if image is landscape (wider than tall)
            is_landscape = original_width > original_height
            
            # For landscape images, we might want to rotate them if they're invoice documents
            # This is a heuristic - you might want to adjust based on your specific images
            if is_landscape and original_width > original_height * 1.5:  # Very wide landscape
                # Optionally rotate landscape images to portrait for better PDF fit
                # Uncomment the next line if you want to auto-rotate wide landscape images
                # image = image.rotate(90, expand=True)
                pass
            
            # Optimize image size to reduce memory usage
            # Calculate scaling factor to fit within max dimensions
            scale_width = max_width / image.width
            scale_height = max_height / image.height
            scale = min(scale_width, scale_height, 1.0)  # Don't upscale
            
            if scale < 1.0:
                new_width = int(image.width * scale)
                new_height = int(image.height * scale)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Optimize quality for PDF (reduce file size)
            if image.width > 600 or image.height > 800:
                # Further resize very large images
                scale_factor = min(600 / image.width, 800 / image.height)
                if scale_factor < 1.0:
                    new_width = int(image.width * scale_factor)
                    new_height = int(image.height * scale_factor)
                    image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            return image
            
        except Exception as e:
            print(f"Error optimizing image: {str(e)}")
            return image  # Return original if optimization fails
    
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
            
            # Process and add images
            print(f"Processing {len(images)} images for PDF...")
            
            for i, image in enumerate(images):
                if image is not None:
                    try:
                        print(f"Processing image {i+1}/{len(images)}")
                        
                        # Optimize image for PDF
                        optimized_image = self.optimize_image_for_pdf(image)
                        
                        if optimized_image is None:
                            print(f"Skipping image {i+1} - optimization failed")
                            continue
                        
                        # Add page break before image
                        story.append(Spacer(1, 12))
                        
                        # Convert PIL Image to ReportLab Image
                        img_buffer = io.BytesIO()
                        optimized_image.save(img_buffer, format='PNG', optimize=True)
                        img_buffer.seek(0)
                        
                        # Calculate image size to fit page
                        img_width, img_height = optimized_image.size
                        max_width = 7 * inch
                        max_height = 9 * inch
                        
                        # Scale image to fit page
                        scale_width = max_width / img_width
                        scale_height = max_height / img_height
                        scale = min(scale_width, scale_height)
                        
                        final_width = img_width * scale
                        final_height = img_height * scale
                        
                        # Add image to story
                        rl_image = RLImage(img_buffer, width=final_width, height=final_height)
                        story.append(rl_image)
                        
                        # Clean up buffer
                        img_buffer.close()
                        
                    except Exception as img_error:
                        print(f"Error processing image {i+1}: {str(img_error)}")
                        # Continue with other images instead of failing completely
                        continue
                else:
                    print(f"Skipping image {i+1} - image is None")
            
            # Build PDF
            print("Building PDF...")
            doc.build(story)
            print(f"PDF generated successfully: {filepath}")
            
            return filepath
            
        except Exception as e:
            print(f"Error generating PDF: {str(e)}")
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