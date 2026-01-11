"""
Image hashing utilities for detecting page changes.
Shared by automation_coordinator and kindle_controller.
"""
import cv2
import numpy as np
from PIL import Image


class ImageHasher:
    """Handles image hashing for page change detection."""

    @staticmethod
    def hash_image(img_data, is_mss_screenshot=True):
        """
        Calculate hash of an image.

        Args:
            img_data: mss screenshot object or PIL Image
            is_mss_screenshot: True if img_data is from mss.grab(), False if PIL Image

        Returns:
            tuple: (mean_value, dhash)
        """
        if is_mss_screenshot:
            img = Image.frombytes("RGB", img_data.size, img_data.rgb)
        else:
            img = img_data

        img_np = np.array(img)
        gray_img = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)

        # Mean value
        mean_value = cv2.mean(gray_img)[0]

        # dHash (difference hash)
        resized = cv2.resize(gray_img, (9, 8), interpolation=cv2.INTER_AREA)
        diff = resized[:, 1:] > resized[:, :-1]
        hash_value = sum([2 ** i for (i, v) in enumerate(diff.flatten()) if v])

        return (mean_value, hash_value)

    @staticmethod
    def compare_hashes(hash1, hash2):
        """
        Compare two hashes and return difference score.

        Args:
            hash1, hash2: tuples of (mean_value, dhash)

        Returns:
            float: difference score (higher = more different)
        """
        mean_diff = abs(hash1[0] - hash2[0])
        xor = hash1[1] ^ hash2[1]
        hamming_dist = bin(xor).count('1')
        combined_diff = mean_diff + (hamming_dist * 2.0)
        return combined_diff
