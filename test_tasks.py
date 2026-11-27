import unittest
from task_utils import progress_from_line, suggested_name, compression_command

class TaskTests(unittest.TestCase):
    def test_progress_from_downloader(self):
        self.assertEqual(progress_from_line('[download]  42.5% of 10MiB'), 42.5)
    def test_non_progress_is_not_percentage(self):
        self.assertIsNone(progress_from_line('processing'))
    def test_suggested_name_avoids_overwriting(self):
        self.assertEqual(suggested_name('C:/a/movie.mp4','mp4'), 'movie_convertido.mp4')
        self.assertEqual(suggested_name('C:/a/movie.mp4','mkv'), 'movie.mkv')
    def test_lossless_video_uses_lossless_codecs(self):
        cmd=compression_command('ffmpeg','a.mp4','b.mkv','Vídeo',False)
        self.assertIn('ffv1',cmd); self.assertIn('copy',cmd)

if __name__ == '__main__': unittest.main()
