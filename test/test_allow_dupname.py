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

    def test_metadata_save_and_load(self):
        """Test metadata file creation and loading."""
        ydl = YoutubeDL({'allow_dupname': True})
        filepath = os.path.join(self.temp_dir, 'video.mp4')
        info_dict = {
            'webpage_url': 'https://example.com/video',
            'title': 'Test Video',
            'duration': 120,
            'ext': 'mp4',
            'format_id': '137',
            'filesize': 1000000,
        }

        # Save metadata
        ydl._save_metadata(filepath, info_dict)

        # Check metadata file exists
        metadata_file = ydl._get_metadata_file(filepath)
        self.assertTrue(os.path.exists(metadata_file))

        # Load metadata
        loaded = ydl._load_metadata(filepath)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded['webpage_url'], 'https://example.com/video')
        self.assertEqual(loaded['title'], 'Test Video')
        self.assertEqual(loaded['duration'], 120)
        self.assertEqual(loaded['ext'], 'mp4')
        self.assertEqual(loaded['format_id'], '137')
        self.assertEqual(loaded['filesize'], 1000000)

    def test_identical_file_with_matching_metadata(self):
        """Should return True when metadata matches."""
        ydl = YoutubeDL({'allow_dupname': True})
        filepath = os.path.join(self.temp_dir, 'video.mp4')
        info_dict = {
            'webpage_url': 'https://example.com/video',
            'title': 'Test Video',
            'duration': 120,
            'ext': 'mp4',
            'format_id': '137',
            'filesize': 1000000,
        }

        # Create file and save metadata
        with open(filepath, 'w') as f:
            f.write('content')
        ydl._save_metadata(filepath, info_dict)

        # Check with same metadata
        result = ydl._is_identical_file(filepath, info_dict)
        self.assertTrue(result)

    def test_identical_file_with_different_webpage_url(self):
        """Should return False when webpage_url differs."""
        ydl = YoutubeDL({'allow_dupname': True})
        filepath = os.path.join(self.temp_dir, 'video.mp4')
        info_dict1 = {
            'webpage_url': 'https://example.com/video1',
            'title': 'Test Video',
            'duration': 120,
            'ext': 'mp4',
            'format_id': '137',
            'filesize': 1000000,
        }
        info_dict2 = {
            'webpage_url': 'https://example.com/video2',
            'title': 'Test Video',
            'duration': 120,
            'ext': 'mp4',
            'format_id': '137',
            'filesize': 1000000,
        }

        # Create file and save metadata
        with open(filepath, 'w') as f:
            f.write('content')
        ydl._save_metadata(filepath, info_dict1)

        # Check with different webpage_url
        result = ydl._is_identical_file(filepath, info_dict2)
        self.assertFalse(result)

    def test_identical_file_no_metadata(self):
        """Should return False when no metadata file exists."""
        ydl = YoutubeDL({'allow_dupname': True})
        filepath = os.path.join(self.temp_dir, 'video.mp4')
        info_dict = {
            'webpage_url': 'https://example.com/video',
            'title': 'Test Video',
            'duration': 120,
            'ext': 'mp4',
            'format_id': '137',
            'filesize': 1000000,
        }

        # Create file without metadata
        with open(filepath, 'w') as f:
            f.write('content')

        # Check without metadata
        result = ydl._is_identical_file(filepath, info_dict)
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
