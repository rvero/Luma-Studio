import unittest
from core import image_command, download_command, pixel_hex, media_command

class CoreTests(unittest.TestCase):
    def test_image_command_preserves_paths_and_options(self):
        self.assertEqual(image_command('magick', 'a b.png', 'out.jpg', 800, None, 90), ['magick', 'a b.png', '-resize', '800x', '-quality', '90', 'out.jpg'])
    def test_download_audio(self):
        cmd = download_command('yt-dlp', 'https://example.com/a', 'dest', True)
        self.assertIn('--extract-audio', cmd)
        self.assertEqual(cmd[-1], 'https://example.com/a')
    def test_pixel_hex(self):
        self.assertEqual(pixel_hex((12, 128, 255, 0)), '#0C80FF')
    def test_audio_conversion_removes_video_and_uses_mp3_codec(self):
        cmd = media_command('ffmpeg', 'video.mp4', 'music.mp3', 'mp3', 'Alta')
        self.assertIn('-vn', cmd)
        self.assertIn('libmp3lame', cmd)
        self.assertEqual(cmd[-1], 'music.mp3')
    def test_video_conversion_selects_webm_codecs(self):
        cmd = media_command('ffmpeg', 'source.mov', 'result.webm', 'webm', 'Equilibrada')
        self.assertIn('libvpx-vp9', cmd)
        self.assertIn('libopus', cmd)
    def test_unknown_format_rejected(self):
        with self.assertRaises(ValueError): media_command('ffmpeg', 'a', 'b', 'exe', 'Alta')

if __name__ == '__main__': unittest.main()
