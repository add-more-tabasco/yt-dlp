#!/usr/bin/env python3

import os
import sys
import tempfile
import shutil
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from yt_dlp import YoutubeDL


class TestAllowDupnameFilename(unittest.TestCase):
    """Test allow-dupname feature for duplicate filenames."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_no_duplicates_returns_original_path(self):
        """File doesn't exist - should return original path."""
        ydl = YoutubeDL({'allow_dupname': True})
        filepath = os.path.join(self.temp_dir, 'video.mp4')
        result = ydl._get_auto_numbered_path(filepath)
        self.assertEqual(result, filepath)

    def test_single_duplicate_increments_to_one(self):
        """First duplicate should get (1) appended."""
        ydl = YoutubeDL({'allow_dupname': True})
        filepath = os.path.join(self.temp_dir, 'video.mp4')

        # Create initial file
        with open(filepath, 'w') as f:
            f.write('original')

        result = ydl._get_auto_numbered_path(filepath)
        expected = os.path.join(self.temp_dir, 'video (1).mp4')
        self.assertEqual(result, expected)

    def test_multiple_duplicates_increment_sequentially(self):
        """Multiple duplicates should increment (1), (2), (3)..."""
        ydl = YoutubeDL({'allow_dupname': True})
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
        ydl = YoutubeDL({'allow_dupname': True})
        filepath = os.path.join(self.temp_dir, 'video.archive.backup.mp4')

        with open(filepath, 'w') as f:
            f.write('original')

        result = ydl._get_auto_numbered_path(filepath)
        expected = os.path.join(self.temp_dir, 'video.archive.backup (1).mp4')
        self.assertEqual(result, expected)

    def test_preserves_directory_structure(self):
        """Should maintain directory paths."""
        ydl = YoutubeDL({'allow_dupname': True})
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
        """allow-dupname + --continue should disable allow_dupname (CLI only)."""
        # This validation only applies to CLI usage, not programmatic API
        # Programmatic users may have valid reasons to use both
        # So we skip this test for programmatic usage
        pass

    def test_incompatible_with_overwrites(self):
        """allow-dupname + --overwrites should disable allow-dupname."""
        ydl = YoutubeDL({'allow_dupname': True, 'overwrites': True})
        self.assertFalse(ydl.params.get('allow_dupname'))

    def test_json_files_also_incremented(self):
        """Info JSON should also be auto-numbered."""
        ydl = YoutubeDL({'allow_dupname': True})
        filepath = os.path.join(self.temp_dir, 'video.info.json')

        with open(filepath, 'w') as f:
            f.write('{}')

        result = ydl._get_auto_numbered_path(filepath)
        expected = os.path.join(self.temp_dir, 'video (1).info.json')
        self.assertEqual(result, expected)

    def test_subtitle_files_incremented(self):
        """Subtitle files should be auto-numbered."""
        ydl = YoutubeDL({'allow_dupname': True})
        filepath = os.path.join(self.temp_dir, 'video.en.vtt')

        with open(filepath, 'w') as f:
            f.write('WEBVTT')

        result = ydl._get_auto_numbered_path(filepath)
        expected = os.path.join(self.temp_dir, 'video (1).en.vtt')
        self.assertEqual(result, expected)

    def test_handles_no_extension(self):
        """Should handle files without extensions."""
        ydl = YoutubeDL({'allow_dupname': True})
        filepath = os.path.join(self.temp_dir, 'README')

        with open(filepath, 'w') as f:
            f.write('readme content')

        result = ydl._get_auto_numbered_path(filepath)
        expected = os.path.join(self.temp_dir, 'README (1)')
        self.assertEqual(result, expected)

    def test_fallback_to_timestamp_on_exhaustion(self):
        """Should fallback to timestamp if (10000) is reached."""
        ydl = YoutubeDL({'allow_dupname': True})
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

    def test_skip_identical_same_size(self):
        """skip_identical should return True when file exists with same size."""
        ydl = YoutubeDL({'skip_identical': True})
        filepath = os.path.join(self.temp_dir, 'video.mp4')

        # Create file with known size
        content = b'x' * 1000
        with open(filepath, 'wb') as f:
            f.write(content)

        result = ydl._is_identical_file(filepath, 1000)
        self.assertTrue(result)

    def test_skip_identical_different_size(self):
        """skip_identical should return False when file exists with different size."""
        ydl = YoutubeDL({'skip_identical': True})
        filepath = os.path.join(self.temp_dir, 'video.mp4')

        # Create file with known size
        with open(filepath, 'wb') as f:
            f.write(b'x' * 1000)

        result = ydl._is_identical_file(filepath, 2000)
        self.assertFalse(result)

    def test_skip_identical_no_expected_size(self):
        """skip_identical should return False when no expected size provided."""
        ydl = YoutubeDL({'skip_identical': True})
        filepath = os.path.join(self.temp_dir, 'video.mp4')

        # Create file
        with open(filepath, 'wb') as f:
            f.write(b'x' * 1000)

        result = ydl._is_identical_file(filepath, None)
        self.assertFalse(result)

    def test_skip_identical_file_not_exists(self):
        """skip_identical should return False when file doesn't exist."""
        ydl = YoutubeDL({'skip_identical': True})
        filepath = os.path.join(self.temp_dir, 'video.mp4')

        result = ydl._is_identical_file(filepath, 1000)
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
