import unittest
from browser_detection import detect_browsers

class BrowserDetectionTests(unittest.TestCase):
    def test_only_detected_supported_browsers_are_listed(self):
        present = {'firefox', 'microsoft-edge'}
        found = detect_browsers(platform='linux', which=lambda name: name if name in present else None, exists=lambda path: False, environ={})
        self.assertEqual(found, ['Edge', 'Firefox'])
    def test_browser_can_be_found_at_windows_install_path(self):
        found = detect_browsers(platform='win32', which=lambda name: None, exists=lambda path: str(path).lower().endswith('chrome.exe'), environ={'PROGRAMFILES':'C:/Program Files'})
        self.assertIn('Chrome', found)
        self.assertNotIn('Firefox', found)

if __name__ == '__main__': unittest.main()
