"""core — internal shared library for the axi25-source acquisition skill.

The foundation the four handlers (book/article/stream/audio) build on. Kept light:
this __init__ imports only the stdlib-only `vault` helpers. Import the rest explicitly:

    from core import slugify, vault_root, sha256_of, today      # stdlib
    from core.frontmatter import dump, document                 # needs pyyaml
    from core.subtitles import build_srt, build_txt, hms, speaker_blocks  # stdlib
    from core.openrouter import chat, OpenRouterError           # stdlib (LLM cleanup)
    from core.transcribe import transcribe, transcribe_diarized, TranscribeError  # stdlib + ffmpeg-pip
    from core.vision import ocr_image, VisionError              # stdlib
    from core.media import ffmpeg_exe, duration_seconds, extract_chunk, extract_frame  # imageio-ffmpeg
    from core.envkeys import resolve                             # stdlib
"""
from __future__ import annotations

from .vault import sha256_of, slugify, today, vault_root

__all__ = ["slugify", "vault_root", "sha256_of", "today"]
__version__ = "2.0.0"
