import unittest
from core import download_command, media_command

class FeatureTests(unittest.TestCase):
    def test_download_chosen_formats(self):
        self.assertIn('flac', download_command('yt-dlp','https://x.com/a','out',format_name='flac'))
        self.assertIn('--recode-video', download_command('yt-dlp','https://x.com/a','out',format_name='mp4'))
    def test_gif_conversion(self):
        self.assertIn('gif', media_command('ffmpeg','x.mp4','x.gif','gif','Alta'))
    def test_audio_to_video_has_visual(self):
        command = media_command('ffmpeg','x.mp3','x.mp4','mp4','Alta', audio_only=True)
        self.assertIn('color=c=black:s=1280x720:r=25', command)
        self.assertIn('-shortest', command)

if __name__ == '__main__': unittest.main()
