import unittest
from PIL import Image
from app import App

class ColorEmptyStateTests(unittest.TestCase):
    def test_empty_page_hides_color_tools(self):
        app = App()
        try:
            app.show('Seletor de cores'); app.update()
            self.assertTrue(app.color_empty.winfo_ismapped())
            self.assertFalse(hasattr(app, 'canvas') and app.canvas.winfo_exists())
        finally: app.destroy()

    def test_existing_image_opens_tools(self):
        app = App()
        try:
            app.image = Image.new('RGBA',(20,20),'red')
            app.show('Seletor de cores'); app.update()
            self.assertTrue(app.canvas.winfo_exists())
            self.assertTrue(app.palette_frame.winfo_exists())
        finally: app.destroy()

if __name__ == '__main__': unittest.main()
