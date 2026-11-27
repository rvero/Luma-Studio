import unittest
from visual_design import contrast_ratio, swatch_text_color

class VisualDesignTests(unittest.TestCase):
    def test_contrast_values(self):
        self.assertAlmostEqual(contrast_ratio('#000000', '#FFFFFF'), 21.0, places=2)
    def test_swatch_text_has_readable_contrast(self):
        for background in ('#FFFF00', '#777777', '#0000FF', '#FF0000', '#FFFFFF', '#000000'):
            self.assertGreaterEqual(contrast_ratio(background, swatch_text_color(background)), 4.5)

if __name__ == '__main__': unittest.main()
