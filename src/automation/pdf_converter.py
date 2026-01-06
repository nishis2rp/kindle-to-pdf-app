import img2pdf
from PIL import Image
import os
import time

class PdfConverter:
    def __init__(self, status_callback=None, optimize_images=False):
        self.status_callback = status_callback if status_callback else self._default_status_callback
        self.optimize_images = optimize_images

    def _default_status_callback(self, message):
        print(f"Status: {message}")

    def _optimize_image(self, image_path, temp_optimized_dir):
        img = Image.open(image_path)
        if self.optimize_images:
            self.status_callback(f"Optimizing image: {os.path.basename(image_path)}")
            img = img.convert("L")
        if self.optimize_images and img.width > 800:
            width_percent = (800 / float(img.size[0]))
            hsize = int((float(img.size[1]) * float(width_percent)))
            img = img.resize((800, hsize), Image.LANCZOS)
        
        optimized_image_path = os.path.join(temp_optimized_dir, os.path.basename(image_path))
        img.save(optimized_image_path)
        return optimized_image_path

    def create_pdf_from_images(self, image_files, output_folder, output_filename):
        self.status_callback("Creating PDF...")
        os.makedirs(output_folder, exist_ok=True) # Ensure output folder exists
        pdf_path = os.path.join(output_folder, output_filename)

        optimized_image_paths = []
        temp_optimized_dir = None

        if self.optimize_images:
            temp_optimized_dir = os.path.join(output_folder, "temp_optimized_images_" + str(time.time()))
            os.makedirs(temp_optimized_dir, exist_ok=True)
            for image_file in image_files:
                optimized_path = self._optimize_image(image_file, temp_optimized_dir)
                optimized_image_paths.append(optimized_path)
        else:
            optimized_image_paths = image_files

        try:
            with open(pdf_path, "wb") as f:
                f.write(img2pdf.convert(optimized_image_paths))
        finally:
            if temp_optimized_dir and os.path.exists(temp_optimized_dir):
                for f in os.listdir(temp_optimized_dir):
                    os.remove(os.path.join(temp_optimized_dir, f))
                os.rmdir(temp_optimized_dir)
        
        return pdf_path
