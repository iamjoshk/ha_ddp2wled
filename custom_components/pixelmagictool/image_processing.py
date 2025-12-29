"""
Image processing utilities for PixelMagicTool.

This module implements the same image processing techniques used by WLEDVideoSync
to achieve proper saturation, brightness, contrast, sharpening, and auto-image
functionality.

Based on WLEDVideoSync src/utl/cv2utils.py ImageUtils class.
"""

import cv2
import numpy as np
import contextlib
import logging

_LOGGER = logging.getLogger(__name__)


class ImageProcessor:
    """Image processing utilities for enhancing images sent to WLED devices."""

    @staticmethod
    def apply_filters(img: np.ndarray, filters: dict) -> np.ndarray:
        """
        Apply filters to an image using OpenCV.

        Applies various image filters like saturation, brightness, contrast, sharpen, 
        and color balance to the input image. The filters and their parameters are 
        specified in the `filters` dictionary.

        Args:
            img: Input image as numpy array (RGB)
            filters: Dictionary with filter parameters:
                - saturation: float (0.0 to 2.0, 1.0 = no change)
                - brightness: float (0.0 to 2.0, 1.0 = no change)
                - contrast: float (0.0 to 2.0, 1.0 = no change)
                - sharpen: float (0.0 to 1.0, 0.0 = no sharpening)
                - balance_r: float (0.0 to 2.0, 1.0 = no change)
                - balance_g: float (0.0 to 2.0, 1.0 = no change)
                - balance_b: float (0.0 to 2.0, 1.0 = no change)

        Returns:
            Processed image as numpy array
        """
        # Apply saturation adjustment
        if filters.get("saturation", 1.0) != 1.0:
            img = ImageProcessor.adjust_saturation(img, filters["saturation"])

        # Apply brightness adjustment
        if filters.get("brightness", 1.0) != 1.0:
            img = ImageProcessor.adjust_brightness(img, filters["brightness"])

        # Apply contrast adjustment
        if filters.get("contrast", 1.0) != 1.0:
            img = ImageProcessor.adjust_contrast(img, filters["contrast"])

        # Apply sharpening
        if filters.get("sharpen", 0.0) > 0.0:
            img = ImageProcessor.apply_sharpening(img, filters["sharpen"])

        # Apply color balance
        if (filters.get("balance_r", 1.0) != 1.0 or 
            filters.get("balance_g", 1.0) != 1.0 or 
            filters.get("balance_b", 1.0) != 1.0):
            img = ImageProcessor.adjust_color_balance(img, {
                "r": filters.get("balance_r", 1.0),
                "g": filters.get("balance_g", 1.0),
                "b": filters.get("balance_b", 1.0),
            })

        return img

    @staticmethod
    def adjust_saturation(img: np.ndarray, saturation_factor: float) -> np.ndarray:
        """
        Adjust the saturation of an image.

        Enhances or reduces the saturation of an image by blending the original 
        image with a grayscale version.

        Args:
            img: Input image (RGB)
            saturation_factor: Saturation multiplier (0.0 = grayscale, 1.0 = original, 2.0 = highly saturated)

        Returns:
            Image with adjusted saturation
        """
        # Convert to HSV and split the channels
        hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
        h, s, v = cv2.split(hsv)

        # Create a grayscale (desaturated) version
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

        # Enhance color saturation
        s_enhanced = cv2.addWeighted(s, saturation_factor, gray, 1 - saturation_factor, 0)

        return cv2.cvtColor(cv2.merge([h, s_enhanced, v]), cv2.COLOR_HSV2RGB)

    @staticmethod
    def adjust_brightness(img: np.ndarray, brightness_factor: float) -> np.ndarray:
        """
        Adjust the brightness of an image.

        Changes the brightness of an image by blending it with a black image.

        Args:
            img: Input image (RGB)
            brightness_factor: Brightness multiplier (0.0 = black, 1.0 = original, 2.0 = brighter)

        Returns:
            Image with adjusted brightness
        """
        # Create a black image
        black_img = np.zeros_like(img)

        return cv2.addWeighted(img, brightness_factor, black_img, 1 - brightness_factor, 0)

    @staticmethod
    def adjust_contrast(img: np.ndarray, contrast_factor: float) -> np.ndarray:
        """
        Adjust the contrast of an image.

        Modifies the contrast of an image by blending it with a gray image 
        of mean luminance.

        Args:
            img: Input image (RGB)
            contrast_factor: Contrast multiplier (0.0 = gray, 1.0 = original, 2.0 = high contrast)

        Returns:
            Image with adjusted contrast
        """
        # Compute the mean luminance (gray level)
        mean_luminance = np.mean(img)

        # Create a gray image of mean luminance
        gray_img = np.full_like(img, mean_luminance)

        return cv2.addWeighted(img, contrast_factor, gray_img, 1 - contrast_factor, 0)

    @staticmethod
    def apply_sharpening(img: np.ndarray, sharpen_factor: float) -> np.ndarray:
        """
        Sharpen an image using a Laplacian kernel.

        Applies a sharpening filter to the image using a Laplacian kernel 
        scaled by the sharpen_factor parameter.

        Args:
            img: Input image (RGB)
            sharpen_factor: Sharpening intensity (0.0 = no sharpening, 1.0 = full sharpening)

        Returns:
            Sharpened image
        """
        kernel = np.array([[0, -1, 0], [-1, 4, -1], [0, -1, 0]]) * sharpen_factor
        kernel[1, 1] += 1
        img = cv2.filter2D(img, -1, kernel)
        return img

    @staticmethod
    def adjust_color_balance(img: np.ndarray, balance: dict) -> np.ndarray:
        """
        Adjust color balance of an image.

        Scales the red, green, and blue channels of the image by the factors 
        specified in the `balance` dictionary.

        Args:
            img: Input image (RGB)
            balance: Dictionary with 'r', 'g', 'b' keys containing multipliers

        Returns:
            Color balanced image
        """
        # Scale the red, green, and blue channels
        scale = np.array([balance["r"], balance["g"], balance["b"]])[np.newaxis, np.newaxis, :]
        img = (img * scale).astype(np.uint8)
        return img

    @staticmethod
    def apply_gamma_correction(img: np.ndarray, gamma: float = 0.5) -> np.ndarray:
        """
        Apply gamma correction to an image.

        Generates a gamma correction lookup table and applies it to the image.

        Args:
            img: Input image (RGB)
            gamma: Gamma value (0.1 = bright, 1.0 = no change, 2.0 = dark)

        Returns:
            Gamma corrected image
        """
        inverse_gamma = 1 / gamma
        gamma_table = [((i / 255) ** inverse_gamma) * 255 for i in range(256)]
        gamma_table = np.array(gamma_table, np.uint8)
        
        return cv2.LUT(img, gamma_table)

    @staticmethod
    def automatic_brightness_and_contrast(img: np.ndarray, clip_hist_percent: float = 25.0) -> np.ndarray:
        """
        Automatically adjust brightness and contrast of an image.

        Calculates the optimal brightness and contrast values based on the 
        image's histogram and applies them to enhance the image's dynamic range.
        
        This is the "auto" feature from WLEDVideoSync that creates balanced images.

        Args:
            img: Input image (RGB)
            clip_hist_percent: Percentage of histogram to clip (0-50, typically 25)

        Returns:
            Auto-adjusted image with improved brightness and contrast
        """
        # Convert to BGR for OpenCV histogram calculation
        bgr_img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2GRAY)

        # Calculate grayscale histogram
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist_size = len(hist)

        # Calculate cumulative distribution from the histogram
        accumulator = [float(hist[0])]
        accumulator.extend(
            accumulator[index - 1] + float(hist[index])
            for index in range(1, hist_size)
        )

        # Locate points to clip
        maximum = accumulator[-1]
        clip_hist_percent *= (maximum / 100.0)
        clip_hist_percent /= 2.0

        # Locate left cut
        minimum_gray = 0
        while accumulator[minimum_gray] < clip_hist_percent:
            minimum_gray += 1

        # Locate right cut
        maximum_gray = hist_size - 1
        with contextlib.suppress(IndexError):
            while accumulator[maximum_gray] >= (maximum - clip_hist_percent):
                maximum_gray -= 1

        # Calculate alpha and beta values
        if maximum_gray - minimum_gray > 0:
            alpha = 255 / (maximum_gray - minimum_gray)
        else:
            alpha = 255 / 0.1  # Avoid division by zero
        beta = -minimum_gray * alpha

        # Apply the calculated adjustments
        result = cv2.convertScaleAbs(bgr_img, alpha=alpha, beta=beta)
        
        # Convert back to RGB
        return cv2.cvtColor(result, cv2.COLOR_BGR2RGB)

    @staticmethod
    def process_image_for_led(img: np.ndarray, 
                             saturation: float = 1.0,
                             brightness: float = 1.0, 
                             contrast: float = 1.0,
                             sharpen: float = 0.0,
                             balance_r: float = 1.0,
                             balance_g: float = 1.0,
                             balance_b: float = 1.0,
                             gamma: float = 0.5,
                             auto_bright: bool = True,
                             clip_hist_percent: float = 25.0) -> np.ndarray:
        """
        Complete image processing pipeline optimized for LED displays.

        This method applies the full WLEDVideoSync image processing pipeline:
        1. Gamma correction
        2. Auto brightness/contrast (if enabled)
        3. Manual adjustments (saturation, brightness, contrast, sharpening, color balance)

        Args:
            img: Input image (RGB)
            saturation: Saturation adjustment (0.0-2.0, 1.0=no change)
            brightness: Brightness adjustment (0.0-2.0, 1.0=no change)  
            contrast: Contrast adjustment (0.0-2.0, 1.0=no change)
            sharpen: Sharpening intensity (0.0-1.0, 0.0=no sharpening)
            balance_r: Red channel balance (0.0-2.0, 1.0=no change)
            balance_g: Green channel balance (0.0-2.0, 1.0=no change)
            balance_b: Blue channel balance (0.0-2.0, 1.0=no change)
            gamma: Gamma correction (0.1-2.0, 0.5=default, 1.0=no change)
            auto_bright: Enable automatic brightness/contrast
            clip_hist_percent: Clipping percentage for auto adjustment (0-50)

        Returns:
            Processed image optimized for LED display
        """
        _LOGGER.debug("Processing image for LED display: auto_bright=%s, gamma=%.2f", auto_bright, gamma)
        
        # Step 1: Apply gamma correction
        if gamma != 1.0:
            img = ImageProcessor.apply_gamma_correction(img, gamma)

        # Step 2: Apply automatic brightness and contrast if enabled
        if auto_bright:
            img = ImageProcessor.automatic_brightness_and_contrast(img, clip_hist_percent)
            _LOGGER.debug("Applied automatic brightness/contrast with clip_hist_percent=%.1f", clip_hist_percent)

        # Step 3: Apply manual filter adjustments
        filter_params = [saturation, brightness, contrast, sharpen, balance_r, balance_g, balance_b]
        
        # Only apply filters if any parameter is not at default value
        if any(param != 1.0 for param in filter_params[:-1]) or sharpen != 0.0:
            filters = {
                "saturation": saturation,
                "brightness": brightness,
                "contrast": contrast,
                "sharpen": sharpen,
                "balance_r": balance_r,
                "balance_g": balance_g,
                "balance_b": balance_b,
            }
            img = ImageProcessor.apply_filters(img, filters)
            _LOGGER.debug("Applied manual filters: sat=%.2f, bri=%.2f, con=%.2f, sharp=%.2f", 
                         saturation, brightness, contrast, sharpen)

        return img