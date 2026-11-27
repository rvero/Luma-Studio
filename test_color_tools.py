import unittest
from PIL import Image
from color_tools import image_palette, magnified_pixel

class ColorToolTests(unittest.TestCase):
    def test_palette_reflects_image_colors_and_ignores_transparent_pixels(self):
        image = Image.new('RGBA', (10, 10), (255, 0, 0, 255))
        for x in range(5):
            for y in range(10): image.putpixel((x, y), (0, 0, 255, 255))
        image.putpixel((0, 0), (0, 255, 0, 0))
        colors = image_palette(image)
        self.assertIn('#FF0000', colors)
        self.assertIn('#0000FF', colors)
        self.assertNotIn('#00FF00', colors)
    def test_magnifier_marks_center_of_selected_pixel(self):
        image = Image.new('RGBA', (11, 11), (0, 0, 0, 255))
        result = magnified_pixel(image, (5, 5))
        self.assertEqual(result.size, (110, 110))
        self.assertNotEqual(result.getpixel((50, 50))[:3], (0, 0, 0))
        self.assertEqual(result.getpixel((55, 55))[:3], (0, 0, 0))

if __name__ == '__main__': unittest.main()
