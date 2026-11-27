import unittest
from task_utils import upscale_plan

class UpscaleTests(unittest.TestCase):
    def test_high_scale_uses_two_model_passes(self):
        self.assertEqual(upscale_plan(16, 4, False), ([4, 4], 16))
    def test_non_native_scale_resizes_after_two_passes(self):
        self.assertEqual(upscale_plan(6, 4, False), ([4, 4], 6))
    def test_double_uses_two_passes(self):
        self.assertEqual(upscale_plan(2, 4, True), ([4, 4], 2))
    def test_invalid_scale(self):
        with self.assertRaises(ValueError): upscale_plan(17, 4, False)

if __name__ == '__main__': unittest.main()
