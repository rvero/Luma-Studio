import tempfile
from pathlib import Path
import unittest
from types import SimpleNamespace
from PIL import Image
from app import App

class ColorPickerTests(unittest.TestCase):
    def test_image_is_visible_and_pixel_can_be_selected(self):
        app = App()
        try:
            app.image = Image.new('RGBA', (100, 100), (12, 128, 255, 255))
            app.show('Seletor de cores')
            app.update()
            app.draw_image()
            self.assertGreater(app.canvas.winfo_height(), 20)
            event = SimpleNamespace(x=app.offset[0] + 1, y=app.offset[1] + 1)
            app.color_hover(event)
            self.assertTrue(app.canvas.find_withtag('pixel-marker'))
            app.pick_color(event)
            self.assertIn('#0C80FF', app.color_result.cget('text'))
            self.assertEqual(app.color_history, ['#0C80FF'])
        finally:
            app.destroy()

    def test_loading_image_builds_palette_separate_from_history(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'red.png'
            Image.new('RGB', (20, 20), (255, 0, 0)).save(path)
            app = App()
            try:
                app.show('Seletor de cores'); app.update()
                app.run_background = lambda task, done: done(task())
                app.source.insert(0, str(path)); app.load_image()
                self.assertEqual(app.palette_colors, ['#FF0000'])
                self.assertEqual(app.color_history, [])
                self.assertEqual(len(app.palette_frame.winfo_children()), 1)
            finally:
                app.destroy()

if __name__ == '__main__': unittest.main()
