from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PIL import Image
import os
import time

class PdfConverter:
    def __init__(self, output_dir="Kindle_PDFs", status_callback=None):
        self.output_dir = output_dir
        self.status_callback = status_callback if status_callback else self._default_status_callback
        os.makedirs(self.output_dir, exist_ok=True)

    def _default_status_callback(self, message):
        print(f"Status: {message}")

    def create_pdf_from_images(self, image_files):
        self.status_callback("Creating PDF...")
        pdf_name = f"Kindle_Book_{time.strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = os.path.join(self.output_dir, pdf_name)

        c = canvas.Canvas(pdf_path, pagesize=letter)
        width, height = letter

        for image_path in image_files:
            img = Image.open(image_path)
            img_width, img_height = img.size
            aspect = img_height / float(img_width)
            new_width = width
            new_height = new_width * aspect
            c.setPageSize((new_width, new_height))
            c.drawImage(image_path, 0, 0, width=new_width, height=new_height)
            c.showPage()

        c.save()
        return pdf_path
