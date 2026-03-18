"""Tests for the monitor module."""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock
from PIL import Image
import numpy as np

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from monitor import images_differ


class TestImagesDiffer(unittest.TestCase):
    """Test change detection logic."""

    def _make_image(self, color=(100, 100, 100), size=(100, 100)):
        return Image.new("RGB", size, color)

    def test_none_inputs(self):
        img = self._make_image()
        self.assertTrue(images_differ(None, img))
        self.assertTrue(images_differ(img, None))
        self.assertTrue(images_differ(None, None))

    def test_identical_images(self):
        img = self._make_image()
        self.assertFalse(images_differ(img, img.copy()))

    def test_different_images(self):
        img1 = self._make_image((0, 0, 0))
        img2 = self._make_image((255, 255, 255))
        self.assertTrue(images_differ(img1, img2))

    def test_different_sizes(self):
        img1 = self._make_image(size=(100, 100))
        img2 = self._make_image(size=(200, 200))
        self.assertTrue(images_differ(img1, img2))

    def test_small_change_below_threshold(self):
        """A tiny change (1 pixel) should NOT trigger on a 100x100 image."""
        img1 = self._make_image((100, 100, 100))
        img2 = img1.copy()
        pixels = img2.load()
        pixels[50, 50] = (255, 255, 255)  # change 1 pixel out of 10000
        # 1/10000 = 0.01% which is below the 2% threshold
        self.assertFalse(images_differ(img1, img2))

    def test_large_change_above_threshold(self):
        """Changing 50% of the image should trigger."""
        arr1 = np.full((100, 100, 3), 100, dtype=np.uint8)
        arr2 = arr1.copy()
        arr2[:50, :, :] = 255  # change top half
        img1 = Image.fromarray(arr1)
        img2 = Image.fromarray(arr2)
        self.assertTrue(images_differ(img1, img2))


class TestMonitorRegions(unittest.TestCase):
    """Test screen region calculation."""

    @patch("monitor.get_screen_size", return_value=(1920, 1080))
    def test_get_monitor_region_left(self, mock_size):
        config.MONITOR_SIDE = "left"
        from monitor import get_monitor_region
        region = get_monitor_region()
        self.assertEqual(region, (0, 0, 960, 1080))

    @patch("monitor.get_screen_size", return_value=(1920, 1080))
    def test_get_monitor_region_right(self, mock_size):
        config.MONITOR_SIDE = "right"
        from monitor import get_monitor_region
        region = get_monitor_region()
        self.assertEqual(region, (960, 0, 1920, 1080))
        config.MONITOR_SIDE = "left"  # reset


if __name__ == "__main__":
    unittest.main()
