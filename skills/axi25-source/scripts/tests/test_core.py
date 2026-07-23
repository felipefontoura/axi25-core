"""Light unit tests for the stdlib-only core helpers (no network, no heavy deps).

    uv run python -m unittest discover -s tests
"""
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.vault import slugify, today
from core import subtitles


class TestVault(unittest.TestCase):
    def test_slugify_ascii_kebab(self):
        self.assertEqual(slugify("Beyond Vibe Coding!"), "beyond-vibe-coding")
        self.assertEqual(slugify("Café com Leite"), "cafe-com-leite")
        self.assertEqual(slugify(""), "")

    def test_today_iso(self):
        self.assertRegex(today(), r"^\d{4}-\d{2}-\d{2}$")


class TestSubtitles(unittest.TestCase):
    CUES = [
        {"start": 0.0, "end": 2.0, "text": "Hello there."},
        {"start": 2.2, "end": 4.0, "text": "General Kenobi."},
    ]

    def test_srt_timestamp(self):
        self.assertEqual(subtitles.srt_timestamp(3661.5), "01:01:01,500")

    def test_hms(self):
        self.assertEqual(subtitles.hms(65), "01:05")
        self.assertEqual(subtitles.hms(3661), "01:01:01")

    def test_build_srt(self):
        out = subtitles.build_srt(self.CUES)
        self.assertIn("00:00:00,000 --> 00:00:02,000", out)
        self.assertIn("Hello there.", out)

    def test_build_txt_verbatim(self):
        out = subtitles.build_txt(self.CUES)
        self.assertIn("Hello there.", out)
        self.assertIn("General Kenobi.", out)

    def test_speaker_blocks(self):
        segs = [
            {"start": 0.0, "end": 1.0, "text": "Hi.", "speaker": "SPEAKER_00"},
            {"start": 1.0, "end": 2.0, "text": "Yo.", "speaker": "SPEAKER_01"},
        ]
        out = subtitles.speaker_blocks(segs)
        self.assertIn("SPEAKER_00: Hi.", out)
        self.assertIn("SPEAKER_01: Yo.", out)


if __name__ == "__main__":
    unittest.main()
