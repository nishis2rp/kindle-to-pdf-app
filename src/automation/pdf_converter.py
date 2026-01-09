import img2pdf
from PIL import Image
import os
import time

class PdfConverter:
    def __init__(self, status_callback=None):
        self.status_callback = status_callback if status_callback else self._default_status_callback

    def _default_status_callback(self, message):
        print(f"Status: {message}")

    def optimize_image(self, image_path, output_path, image_format="PNG", jpeg_quality=90):
        """Optimize a single image (convert to grayscale, resize, change format)"""
        try:
            with Image.open(image_path) as img:
                # Convert to grayscale for smaller file size
                img_gray = img.convert("L")

                # Resize if too large (preserve aspect ratio)
                if img_gray.width > 1200:
                    width_percent = (1200 / float(img_gray.width))
                    new_height = int((float(img_gray.height) * float(width_percent)))
                    img_gray = img_gray.resize((1200, new_height), Image.LANCZOS)

                # Save with specified format
                if image_format.upper() == "JPEG":
                    img_gray.save(output_path, "JPEG", quality=jpeg_quality, optimize=True)
                else:  # PNG
                    img_gray.save(output_path, "PNG", optimize=True)

                return output_path
        except Exception as e:
            self.status_callback(f"Warning: Could not optimize {os.path.basename(image_path)}: {e}")
            # Return original if optimization fails
            return image_path

    def create_pdf_from_images(self, image_files, output_folder, output_filename,
                               optimize_images=True, image_format="PNG", jpeg_quality=90):
        """
        Create PDF from image files

        Args:
            image_files: List of image file paths
            output_folder: Output directory
            output_filename: PDF filename
            optimize_images: Whether to optimize images (grayscale, resize)
            image_format: "PNG" or "JPEG"
            jpeg_quality: JPEG quality (0-100) if using JPEG format
        """
        self.status_callback("Creating PDF from captured images...")
        os.makedirs(output_folder, exist_ok=True)
        pdf_path = os.path.join(output_folder, output_filename)

        images_to_convert = []
        temp_optimized_dir = None

        if optimize_images:
            self.status_callback(f"Optimizing images (format: {image_format}, quality: {jpeg_quality})...")
            temp_optimized_dir = os.path.join(output_folder, f"temp_optimized_{int(time.time())}")
            os.makedirs(temp_optimized_dir, exist_ok=True)

            for i, image_file in enumerate(image_files, 1):
                self.status_callback(f"Optimizing image {i}/{len(image_files)}: {os.path.basename(image_file)}")

                # Determine output extension
                ext = ".jpg" if image_format.upper() == "JPEG" else ".png"
                output_name = os.path.splitext(os.path.basename(image_file))[0] + ext
                output_path = os.path.join(temp_optimized_dir, output_name)

                optimized_path = self.optimize_image(image_file, output_path, image_format, jpeg_quality)
                images_to_convert.append(optimized_path)
        else:
            images_to_convert = image_files

        try:
            self.status_callback(f"Converting {len(images_to_convert)} images to PDF...")
            with open(pdf_path, "wb") as f:
                f.write(img2pdf.convert(images_to_convert))

            self.status_callback(f"PDF created successfully: {pdf_path}")
            return pdf_path

        except Exception as e:
            self.status_callback(f"Error creating PDF: {e}")
            raise

        finally:
            # Cleanup temporary optimized images
            if temp_optimized_dir and os.path.exists(temp_optimized_dir):
                self.status_callback("Cleaning up temporary optimized images...")
                try:
                    for f in os.listdir(temp_optimized_dir):
                        os.remove(os.path.join(temp_optimized_dir, f))
                    os.rmdir(temp_optimized_dir)
                except Exception as e:
                    self.status_callback(f"Warning: Could not cleanup temp directory: {e}")
