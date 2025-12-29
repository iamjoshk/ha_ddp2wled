"""
Image processing utilities for HA DDP2WLED.

This module implements the same image processing techniques used by WLEDVideoSync
to achieve proper saturation, brightness, contrast, sharpening, and auto-image
functionality.

Based on WLEDVideoSync src/utl/cv2utils.py ImageUtils class.
Uses only PIL/Pillow and basic Python - no OpenCV required.
"""

import math
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import logging

_LOGGER = logging.getLogger(__name__)


class ImageProcessor:
    """Image processing utilities for enhancing images sent to WLED devices."""

    @staticmethod
    def apply_filters(img: Image.Image, filters: dict) -> Image.Image:
        """
        Apply filters to an image using PIL.

        Applies various image filters like saturation, brightness, contrast, sharpen, 
        and color balance to the input image. The filters and their parameters are 
        specified in the `filters` dictionary.

        Args:
            img: Input PIL Image (RGB)
            filters: Dictionary with filter parameters:
                - saturation: float (0.0 to 2.0, 1.0 = no change)
                - brightness: float (0.0 to 2.0, 1.0 = no change)
                - contrast: float (0.0 to 2.0, 1.0 = no change)
                - sharpen: float (0.0 to 1.0, 0.0 = no sharpening)
                - balance_r: float (0.0 to 2.0, 1.0 = no change)
                - balance_g: float (0.0 to 2.0, 1.0 = no change)
                - balance_b: float (0.0 to 2.0, 1.0 = no change)

        Returns:
            Processed PIL Image
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
    def adjust_saturation(img: Image.Image, saturation_factor: float) -> Image.Image:
        """
        Adjust the saturation of an image using PIL.

        Args:
            img: Input PIL Image (RGB)
            saturation_factor: Saturation multiplier (0.0 = grayscale, 1.0 = original, 2.0 = highly saturated)

        Returns:
            Image with adjusted saturation
        """
        enhancer = ImageEnhance.Color(img)
        return enhancer.enhance(saturation_factor)

    @staticmethod
    def adjust_brightness(img: Image.Image, brightness_factor: float) -> Image.Image:
        """
        Adjust the brightness of an image using PIL.

        Args:
            img: Input PIL Image (RGB)
            brightness_factor: Brightness multiplier (0.0 = black, 1.0 = original, 2.0 = brighter)

        Returns:
            Image with adjusted brightness
        """
        enhancer = ImageEnhance.Brightness(img)
        return enhancer.enhance(brightness_factor)

    @staticmethod
    def adjust_contrast(img: Image.Image, contrast_factor: float) -> Image.Image:
        """
        Adjust the contrast of an image using PIL.

        Args:
            img: Input PIL Image (RGB)
            contrast_factor: Contrast multiplier (0.0 = gray, 1.0 = original, 2.0 = high contrast)

        Returns:
            Image with adjusted contrast
        """
        enhancer = ImageEnhance.Contrast(img)
        return enhancer.enhance(contrast_factor)

    @staticmethod
    def apply_sharpening(img: Image.Image, sharpen_factor: float) -> Image.Image:
        """
        Sharpen an image using PIL.

        Args:
            img: Input PIL Image (RGB)
            sharpen_factor: Sharpening intensity (0.0 = no sharpening, 1.0 = full sharpening)

        Returns:
            Sharpened image
        """
        # Use PIL's built-in sharpening filter
        sharpened = img.filter(ImageFilter.SHARPEN)
        
        # Blend original and sharpened based on sharpen_factor
        return Image.blend(img, sharpened, sharpen_factor)

    @staticmethod
    def adjust_color_balance(img: Image.Image, balance: dict) -> Image.Image:
        """
        Adjust color balance of an image using PIL.

        Args:
            img: Input PIL Image (RGB)
            balance: Dictionary with 'r', 'g', 'b' keys containing multipliers

        Returns:
            Color balanced image
        """
        # Get image data
        pixels = list(img.getdata())
        width, height = img.size
        
        # Apply color balance
        balanced_pixels = []
        for r, g, b in pixels:
            new_r = min(255, int(r * balance["r"]))
            new_g = min(255, int(g * balance["g"]))
            new_b = min(255, int(b * balance["b"]))
            balanced_pixels.append((new_r, new_g, new_b))
        
        # Create new image with balanced pixels
        result = Image.new('RGB', (width, height))
        result.putdata(balanced_pixels)
        return result

    @staticmethod
    def apply_gamma_correction(img: Image.Image, gamma: float = 0.5) -> Image.Image:
        """
        Apply gamma correction to an image using PIL.

        Args:
            img: Input PIL Image (RGB)
            gamma: Gamma value (0.1 = bright, 1.0 = no change, 2.0 = dark)

        Returns:
            Gamma corrected image
        """
        if gamma == 1.0:
            return img
            
        # Create gamma lookup table
        inverse_gamma = 1.0 / gamma
        gamma_table = [int(((i / 255.0) ** inverse_gamma) * 255) for i in range(256)]
        
        # Apply gamma correction using PIL's point() method
        return img.point(gamma_table * 3)  # *3 for RGB channels

    @staticmethod
    def automatic_brightness_and_contrast(img: Image.Image, clip_hist_percent: float = 25.0) -> Image.Image:
        """
        Automatically adjust brightness and contrast of an image using PIL.

        Calculates the optimal brightness and contrast values based on the 
        image's histogram and applies them to enhance the image's dynamic range.
        
        This is the "auto" feature from WLEDVideoSync that creates balanced images.

        Args:
            img: Input PIL Image (RGB)
            clip_hist_percent: Percentage of histogram to clip (0-50, typically 25)

        Returns:
            Auto-adjusted image with improved brightness and contrast
        """
        # Convert to grayscale for histogram analysis
        gray = img.convert('L')
        
        # Get histogram
        histogram = gray.histogram()
        
        # Calculate cumulative distribution
        total_pixels = sum(histogram)
        accumulator = []
        running_sum = 0
        for count in histogram:
            running_sum += count
            accumulator.append(running_sum)
        
        # Calculate clipping thresholds
        clip_threshold = total_pixels * (clip_hist_percent / 100.0) / 2.0
        
        # Find minimum and maximum values after clipping
        minimum_gray = 0
        for i, acc_count in enumerate(accumulator):
            if acc_count >= clip_threshold:
                minimum_gray = i
                break
        
        maximum_gray = 255
        for i in range(255, -1, -1):
            if accumulator[i] <= (total_pixels - clip_threshold):
                maximum_gray = i
                break
        
        # Calculate alpha (contrast) and beta (brightness) values
        if maximum_gray > minimum_gray:
            alpha = 255.0 / (maximum_gray - minimum_gray)
            beta = -minimum_gray * alpha
        else:
            alpha = 1.0
            beta = 0.0
        
        # Apply the calculated adjustments using PIL
        # This is equivalent to: result = alpha * img + beta
        enhanced = ImageEnhance.Contrast(img).enhance(alpha)
        if beta != 0:
            # Apply brightness adjustment
            brightness_factor = 1.0 + (beta / 255.0)
            enhanced = ImageEnhance.Brightness(enhanced).enhance(brightness_factor)
        
        return enhanced

    @staticmethod
    def process_image_for_led(img: Image.Image, 
                             saturation: float = 1.0,
                             brightness: float = 1.0, 
                             contrast: float = 1.0,
                             sharpen: float = 0.0,
                             balance_r: float = 1.0,
                             balance_g: float = 1.0,
                             balance_b: float = 1.0,
                             gamma: float = 0.5,
                             auto_bright: bool = True,
                             clip_hist_percent: float = 25.0) -> Image.Image:
        """
        Complete image processing pipeline optimized for LED displays using PIL.

        This method applies the full WLEDVideoSync image processing pipeline:
        1. Gamma correction
        2. Auto brightness/contrast (if enabled)
        3. Manual adjustments (saturation, brightness, contrast, sharpening, color balance)

        Args:
            img: Input PIL Image (RGB)
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
            Processed PIL Image optimized for LED display
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