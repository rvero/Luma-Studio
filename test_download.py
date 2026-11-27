import unittest
from core import download_command

class DownloadTests(unittest.TestCase):
    def test_browser_cookies_are_optional_and_passed_to_ytdlp(self):
        command = download_command('yt-dlp', 'https://instagram.com/p/example', 'dest', False, 'firefox')
        self.assertEqual(command[command.index('--cookies-from-browser') + 1], 'firefox')
        self.assertEqual(command[-1], 'https://instagram.com/p/example')

if __name__ == '__main__': unittest.main()
