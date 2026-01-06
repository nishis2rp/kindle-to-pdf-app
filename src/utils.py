import os
import shutil
import uuid

def create_temp_dir(base_dir, prefix="temp_"):
    """
    Creates a unique temporary directory within base_dir.
    Returns the path to the created directory.
    """
    temp_dir_name = f"{prefix}{uuid.uuid4()}"
    temp_dir_path = os.path.join(base_dir, temp_dir_name)
    os.makedirs(temp_dir_path, exist_ok=True)
    return temp_dir_path

def cleanup_dir(dir_path):
    """
    Removes a directory and its contents.
    """
    if dir_path and os.path.exists(dir_path):
        try:
            shutil.rmtree(dir_path)
            # print(f"Cleaned up temporary directory: {dir_path}") # For debugging
        except OSError as e:
            # print(f"Error cleaning up directory {dir_path}: {e}") # For debugging
            pass
