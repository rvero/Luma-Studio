import unittest
from unittest.mock import patch
from PIL import Image
from app import App

class ClipboardFlows(unittest.TestCase):
    def test_pasting_image_opens_picker_and_palette(self):
        app = App()
        try:
            app.show('Seletor de cores'); app.update()
            with patch('image_clipboard.read_image', return_value=Image.new('RGBA',(12,12),'red')):
                app.paste_image()
            app.update()
            self.assertTrue(app.canvas.winfo_exists())
            self.assertEqual(app.palette_colors, ['#FF0000'])
        finally:
            app.close_app()

    def test_paste_button_accepts_path_from_clipboard(self):
        app = App()
        try:
            app.show('Converter mídia'); app.update()
            with patch('PIL.ImageGrab.grabclipboard', return_value=['C:/video.mp4']):
                app.paste_to_entry(app.media_source)
            self.assertEqual(app.media_source.get(), 'C:/video.mp4')
        finally:
            app.close_app()

if __name__ == '__main__': unittest.main()
