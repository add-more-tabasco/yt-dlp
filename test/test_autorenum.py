#!/usr/bin/env python3

import os
import sys
import tempfile
import shutil
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from yt_dlp import YoutubeDL


class TestAutoRenumberFilename(unittest.TestCase):
    """Test auto-increment duplicate filename feature."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_no_duplicates_returns_original_path(self):
        """File doesn't exist - should return original path."""
        ydl = YoutubeDL({'autorenum': True})
        filepath = os.path.join(self.temp_dir, 'video.mp4')
        result = ydl._get_auto_numbered_path(filepath)
        self.assertEqual(result, filepath)

    def test_single_duplicate_increments_to_one(self):
        """First duplicate should get (1) appended."""
        ydl = YoutubeDL({'autorenum': True})
        filepath = os.path.join(self.temp_dir, 'video.mp4')

        # Create initial file
        with open(filepath, 'w') as f:
            f.write('original')

        result = ydl._get_auto_numbered_path(filepath)
        expected = os.path.join(self.temp_dir, 'video (1).mp4')
        self.assertEqual(result, expected)

    def test_multiple_duplicates_increment_sequentially(self):
        """Multiple duplicates should increment (1), (2), (3)..."""
        ydl = YoutubeDL({'autorenum': True})
        filepath = os.path.join(self.temp_dir, 'video.mp4')

        # Create multiple files
        with open(filepath, 'w') as f:
            f.write('original')
        with open(os.path.join(self.temp_dir, 'video (1).mp4'), 'w') as f:
            f.write('dup1')
        with open(os.path.join(self.temp_dir, 'video (2).mp4'), 'w') as f:
            f.write('dup2')

        result = ydl._get_auto_numbered_path(filepath)
        expected = os.path.join(self.temp_dir, 'video (3).mp4')
        self.assertEqual(result, expected)

    def test_with_complex_filenames(self):
        """Should handle filenames with multiple dots."""
        ydl = YoutubeDL({'autorenum': True})
        filepath = os.path.join(self.temp_dir, 'video.archive.backup.mp4')

        with open(filepath, 'w') as f:
            f.write('original')

        result = ydl._get_auto_numbered_path(filepath)
        expected = os.path.join(self.temp_dir, 'video.archive.backup (1).mp4')
        self.assertEqual(result, expected)

    def test_preserves_directory_structure(self):
        """Should maintain directory paths."""
        ydl = YoutubeDL({'autorenum': True})
        subdir = os.path.join(self.temp_dir, 'videos', 'archive')
        os.makedirs(subdir)

        filepath = os.path.join(subdir, 'video.mp4')
        with open(filepath, 'w') as f:
            f.write('original')

        result = ydl._get_auto_numbered_path(filepath)
        expected = os.path.join(subdir, 'video (1).mp4')
        self.assertEqual(result, expected)
        self.assertTrue(result.startswith(subdir))

    def test_incompatible_with_continue(self):
        """autorenum + --continue should disable autorenum."""
        ydl = YoutubeDL({'autorenum': True, 'continue_dl': True})
        # Should have been disabled in __init__
        self.assertFalse(ydl.params.get('autorenum'))

    def test_incompatible_with_overwrites(self):
        """autorenum + --overwrites should disable autorenum."""
        ydl = YoutubeDL({'autorenum': True, 'overwrites': True})
        self.assertFalse(ydl.params.get('autorenum'))

    def test_json_files_also_incremented(self):
        """Info JSON should also be auto-numbered."""
        ydl = YoutubeDL({'autorenum': True})
        filepath = os.path.join(self.temp_dir, 'video.info.json')

        with open(filepath, 'w') as f:
            f.write('{}')

        result = ydl._get_auto_numbered_path(filepath)
        expected = os.path.join(self.temp_dir, 'video (1).info.json')
        self.assertEqual(result, expected)

    def test_subtitle_files_incremented(self):
        """Subtitle files should be auto-numbered."""
        ydl = YoutubeDL({'autorenum': True})
        filepath = os.path.join(self.temp_dir, 'video.en.vtt')

        with open(filepath, 'w') as f:
            f.write('WEBVTT')

        result = ydl._get_auto_numbered_path(filepath)
        expected = os.path.join(self.temp_dir, 'video (1).en.vtt')
        self.assertEqual(result, expected)

    def test_handles_no_extension(self):
        """Should handle files without extensions."""
        ydl = YoutubeDL({'autorenum': True})
        filepath = os.path.join(self.temp_dir, 'README')

        with open(filepath, 'w') as f:
            f.write('readme content')

        result = ydl._get_auto_numbered_path(filepath)
        expected = os.path.join(self.temp_dir, 'README (1)')
        self.assertEqual(result, expected)

    def test_fallback_to_timestamp_on_exhaustion(self):
        """Should fallback to timestamp if (10000) is reached."""
        ydl = YoutubeDL({'autorenum': True})
        filepath = os.path.join(self.temp_dir, 'video.mp4')

        # Create base file
        with open(filepath, 'w') as f:
            f.write('original')

        # Create (1) through (9999)
        for i in range(1, 10001):
            dup_path = os.path.join(self.temp_dir, f'video ({i}).mp4')
            with open(dup_path, 'w') as f:
                f.write(f'dup{i}')

        result = ydl._get_auto_numbered_path(filepath)
        # Should have timestamp in filename
        self.assertIn('(', result)
        self.assertIn(')', result)
        self.assertTrue(result.endswith('.mp4'))


if __name__ == '__main__':
    unittest.main()
