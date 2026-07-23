#!/usr/bin/env python3
"""
Acquire a stream (any yt-dlp URL: YouTube, Vimeo, Twitch, …) as raw source Markdown.

Cloud-first: yt-dlp (pip) downloads the audio using the pip-bundled ffmpeg (imageio-ffmpeg,
no host tool), then OpenRouter STT transcribes. Diarization for podcasts uses a
diarization-capable STT model — no local torch/whisperx/pyannote.

Three intents, via --kind / --source-kind:
  default (no --kind)                      reference video   → 10-sources/videos/reference/<creator>/
  --kind zeitgeist --source-kind podcast-episode   → 50-zeitgeist/podcasts/<show>/ (diarized)
  --kind zeitgeist --source-kind cut               → 50-zeitgeist/podcasts/<show>/<parent>/cuts/

Source acquisition only — never writes to 20-wiki/ (that is axi25-ingest).

Usage:
    source.py stream <url>                    # reference (default)
    source.py stream <url> --probe            # metadata → you classify
    source.py stream <url> --kind zeitgeist --source-kind podcast-episode \\
                    --show flow-podcast --guest igor-akita --episode-id 312 --num-speakers 3
"""
import argparse
import sys
import urllib.request
from pathlib import Path

import yt_dlp

# allow running this handler standalone (put scripts/ on sys.path for `core`)
import sys as _sys, pathlib as _pathlib
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from core import frontmatter, media, slugify, subtitles, today, transcribe, vault_root


def suggest_kind(info: dict, url: str) -> tuple[str | None, str | None, str]:
    """Mechanical routing hint from URL + duration only — no hardcoded show registry."""
    duration = info.get("duration") or 0
    if "/shorts/" in url:
        return "zeitgeist", "cut", "high"
    if duration and duration < 180:
        return "zeitgeist", "cut", "medium"
    return None, None, "high"


def probe_summary(info: dict, url: str) -> str:
    dur = info.get("duration") or 0
    return "\n".join([
        "[probe] classify this yourself, then re-run with explicit flags:",
        f"  url            : {url}",
        f"  title          : {info.get('title') or ''}",
        f"  uploader       : {info.get('uploader') or ''}",
        f"  channel        : {info.get('channel') or ''}",
        f"  uploader_id    : {info.get('uploader_id') or ''}",
        f"  duration       : {subtitles.hms(dur)} ({int(dur)}s)",
        f"  is_shorts_url  : {'/shorts/' in url}",
        f"  suggested_slug : {slugify(info.get('title') or '')}",
        "",
        "  → reference video : (no --kind)",
        "  → podcast episode : --kind zeitgeist --source-kind podcast-episode --show <slug> --audience-proxy <proxy> --num-speakers <n>",
        "  → viral cut       : --kind zeitgeist --source-kind cut --show <slug> --parent-episode <slug> --cut-id <NNN>",
    ])


def fetch_metadata(url: str, cookies: str | None = None) -> dict:
    opts = {"quiet": True, "no_warnings": True, "skip_download": True}
    if cookies:
        opts["cookiefile"] = cookies
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False, process=False)


def download_audio(url: str, target_dir: Path, cookies: str | None = None) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    opts = {
        "format": "bestaudio/best",
        "outtmpl": str(target_dir / "audio.%(ext)s"),
        "ffmpeg_location": media.ffmpeg_dir(),  # pip-bundled ffmpeg, not a host tool
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "quiet": True,
        "no_warnings": True,
    }
    if cookies:
        opts["cookiefile"] = cookies
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])
    audio = target_dir / "audio.mp3"
    if not audio.exists():
        raise RuntimeError(f"Audio not produced at {audio}")
    return audio


def download_thumbnail(info: dict, target: Path) -> bool:
    thumbs = info.get("thumbnails") or []
    if not thumbs:
        return False
    best = sorted(thumbs, key=lambda t: t.get("width") or 0, reverse=True)[0]
    url = best.get("url")
    if not url:
        return False
    try:
        urllib.request.urlretrieve(url, target)
        return True
    except Exception as e:
        print(f"[warn] thumbnail download failed: {e}")
        return False


def format_chapters_section(info: dict) -> str:
    chapters = info.get("chapters") or []
    if not chapters:
        return ""
    lines = ["## Chapters", ""]
    for c in chapters:
        lines.append(f"- [{subtitles.hms(c.get('start_time', 0))}] {(c.get('title') or '').strip()}")
    lines.append("")
    return "\n".join(lines)


def _common_meta(info: dict, url: str, source_kind: str, lang: str | None) -> dict:
    upload_date = info.get("upload_date") or ""
    if len(upload_date) == 8:
        upload_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
    duration = info.get("duration") or 0
    return {
        "type": "source",
        "source_kind": source_kind,
        "title": info.get("title") or "",
        "author": info.get("uploader") or info.get("channel") or None,
        "lang": lang or None,
        "acquired": today(),
        "original_path": url,
        "video_id": info.get("id") or None,
        "channel": info.get("channel") or None,
        "uploader_id": info.get("uploader_id") or info.get("channel_id") or None,
        "upload_date": upload_date or None,
        "duration": subtitles.hms(duration) if duration else None,
        "duration_seconds": duration or None,
        "chapter_count": len(info.get("chapters") or []) or None,
    }


def _cover_embed(target: Path, filename: str) -> list[str]:
    if (target.with_suffix("") / filename).exists():
        return ["", f"![[{target.stem}/{filename}]]"]
    return []


def write_default_md(target: Path, info: dict, url: str, body: str, args) -> None:
    meta = _common_meta(info, url, "video-reference", args.lang)
    header = [f"# {meta['title']}", "", f"> Source: <{url}>"] + _cover_embed(target, "thumbnail.jpg")
    chapters_md = format_chapters_section(info)
    if chapters_md:
        header += ["", chapters_md.rstrip()]
    target.write_text(frontmatter.document(meta, body, header=header), encoding="utf-8")


def write_episode_md(target: Path, info: dict, url: str, body: str, args, speakers: list[str] | None = None) -> None:
    meta = _common_meta(info, url, "podcast-episode", args.lang)
    meta.update({
        "kind": "zeitgeist",
        "show": args.show,
        "guest": args.guest or None,
        "episode_id": args.episode_id or None,
        "audience_proxy": args.audience_proxy or None,
        "date_aired": meta.pop("upload_date", None),
        "captured_period": today()[:7],
    })
    labels = speakers or [f"SPEAKER_{i:02d}" for i in range(args.num_speakers or 2)]
    # names inferred during diarization are already resolved; the rest stay to be mapped
    lines = [(f"- {lbl}: ?" if lbl.startswith("SPEAKER_") else f"- {lbl} (inferred)") for lbl in labels]
    header = [f"# {meta['title']}", "", f"> Source: <{url}>"] + _cover_embed(target, "cover.jpg") + [
        "", "## Speakers", "", "Names inferred where the audio named them — fill in any remaining SPEAKER_NN:", "", "\n".join(lines),
    ]
    chapters_md = format_chapters_section(info)
    if chapters_md:
        header += ["", chapters_md.rstrip()]
    target.write_text(frontmatter.document(meta, body, header=header), encoding="utf-8")


def write_cut_md(target: Path, info: dict, url: str, body: str, args) -> None:
    meta = _common_meta(info, url, "cut", args.lang)
    meta.update({
        "kind": "zeitgeist",
        "show": args.show,
        "guest": args.guest or None,
        "parent_episode": args.parent_episode,
        "cut_id": args.cut_id or None,
        "timestamp_in_episode": args.timestamp_in_episode or None,
        "views_captured": args.cut_views or None,
        "captured_period": today()[:7],
    })
    header = [f"# {meta['title']}", "", f"> Source: <{url}>"]
    target.write_text(frontmatter.document(meta, body, header=header), encoding="utf-8")


def derive_creator(info: dict) -> str:
    raw = info.get("uploader_id") or info.get("channel") or info.get("uploader") or ""
    return slugify(raw.lstrip("@"))


def resolve_paths(args, info: dict) -> tuple[Path, Path | None, Path | None]:
    title = info.get("title", "")
    root = vault_root()

    if args.kind == "zeitgeist":
        if args.source_kind == "podcast-episode":
            if not args.show:
                raise SystemExit("[error] --show required for --source-kind podcast-episode")
            slug = args.slug or slugify(title)
            target_dir = root / "50-zeitgeist" / "podcasts" / args.show
            return target_dir / f"{slug}.md", target_dir / slug, target_dir / slug / "cover.jpg"
        if args.source_kind == "cut":
            if not args.show or not args.parent_episode:
                raise SystemExit("[error] --show and --parent-episode required for --source-kind cut")
            slug = args.slug or slugify(title)
            cut_id = (args.cut_id or "").strip()
            filename = f"{cut_id}-{slug}.md" if cut_id else f"{slug}.md"
            cuts_dir = root / "50-zeitgeist" / "podcasts" / args.show / args.parent_episode / "cuts"
            return cuts_dir / filename, None, None
        raise SystemExit(f"[error] --kind zeitgeist requires --source-kind podcast-episode or cut, got {args.source_kind!r}")

    creator = args.creator or derive_creator(info)
    slug = args.slug or slugify(title)
    if not creator or not slug:
        raise SystemExit(f"[error] could not derive creator/slug. uploader_id={info.get('uploader_id')!r} title={title!r}")
    creator_dir = root / "10-sources" / "videos" / "reference" / creator
    return creator_dir / f"{slug}.md", creator_dir / slug, creator_dir / slug / "thumbnail.jpg"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="source.py stream", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("url", help="Stream URL (YouTube / Vimeo / …)")
    p.add_argument("--kind", choices=["zeitgeist"], default=None, help="Routing kind. Omit for default reference-video.")
    p.add_argument("--source-kind", choices=["podcast-episode", "cut"], default=None, help="Required when --kind=zeitgeist")
    p.add_argument("--creator", help="Creator slug (default kind only)")
    p.add_argument("--slug", help="Slug for the .md filename")
    p.add_argument("--show", help="Show slug (zeitgeist only)")
    p.add_argument("--guest", help="Guest slug (zeitgeist only)")
    p.add_argument("--episode-id", help="Episode id/number (zeitgeist podcast-episode)")
    p.add_argument("--audience-proxy", help="Audience proxy label")
    p.add_argument("--parent-episode", help="Parent episode slug (zeitgeist cut)")
    p.add_argument("--cut-id", help="Sequential cut id within parent (zeitgeist cut)")
    p.add_argument("--cut-views", type=int, default=0, help="Views snapshot at capture time (zeitgeist cut)")
    p.add_argument("--timestamp-in-episode", help="HH:MM:SS where the cut starts in the parent episode")
    p.add_argument("--lang", default=None, help="Transcript language hint (ISO-639-1). Auto if omitted.")
    p.add_argument("--model", default=transcribe.DEFAULT_MODEL, help="OpenRouter STT model")
    p.add_argument("--diarize-model", default=transcribe.DEFAULT_DIARIZE_MODEL, help="OpenRouter diarization-capable STT model")
    p.add_argument("--chunk", type=float, default=600.0, help="STT chunk length in seconds")
    p.add_argument("--num-speakers", type=int, default=None, help="Speaker count hint (podcast-episode)")
    p.add_argument("--keep-audio", action="store_true", help="Keep raw audio after transcription")
    p.add_argument("--force", action="store_true", help="Re-run even if outputs exist")
    p.add_argument("--probe", action="store_true", help="Print raw metadata and exit — classify, then re-run")
    p.add_argument("--no-auto-detect", action="store_true", help="Disable mechanical kind auto-detection")
    p.add_argument("--cookies", help="Path to Netscape-format cookies file (anti-bot bypass)")
    args = p.parse_args(argv)

    print(f"[meta] fetching: {args.url}")
    info = fetch_metadata(args.url, cookies=args.cookies)

    if args.probe:
        print(probe_summary(info, args.url))
        return 0

    if not args.no_auto_detect and args.kind is None:
        detected_kind, detected_source_kind, confidence = suggest_kind(info, args.url)
        if detected_kind and confidence == "high":
            print(f"[auto-detect] kind={detected_kind} source-kind={detected_source_kind}")
            args.kind = detected_kind
            args.source_kind = args.source_kind or detected_source_kind
        elif detected_kind:
            print(f"[auto-detect] suggestion: --kind {detected_kind} --source-kind {detected_source_kind} "
                  f"({confidence}, not auto-applied) — running default reference-video.")

    md_path, sibling_dir, thumb_path = resolve_paths(args, info)
    print(f"[target] {md_path}")

    if md_path.exists() and not args.force:
        print("[skip] outputs already exist (use --force to re-run)")
        return 0

    md_path.parent.mkdir(parents=True, exist_ok=True)
    if sibling_dir is not None:
        sibling_dir.mkdir(parents=True, exist_ok=True)
    if thumb_path is not None:
        print("[thumb] downloading...")
        download_thumbnail(info, thumb_path)

    audio_dir = sibling_dir if sibling_dir is not None else md_path.parent
    print("[audio] downloading (yt-dlp + pip ffmpeg)...")
    audio = download_audio(args.url, audio_dir, cookies=args.cookies)

    try:
        is_podcast = args.kind == "zeitgeist" and args.source_kind == "podcast-episode"
        if is_podcast:
            segments = transcribe.transcribe_diarized(
                audio, language=args.lang, model=args.diarize_model,
                num_speakers=args.num_speakers, chunk_seconds=args.chunk,
            )
            speakers = sorted({s["speaker"] for s in segments if s.get("speaker")})
            write_episode_md(md_path, info, args.url, subtitles.speaker_blocks(segments), args, speakers=speakers)
        else:
            result = transcribe.transcribe(audio, language=args.lang, model=args.model, chunk_seconds=args.chunk)
            body = subtitles.build_txt(result["segments"])
            if args.kind == "zeitgeist" and args.source_kind == "cut":
                write_cut_md(md_path, info, args.url, body, args)
            else:
                write_default_md(md_path, info, args.url, body, args)
    except transcribe.TranscribeError as e:
        print(f"[stt] {e}", file=sys.stderr)
        print("      Set OPENROUTER_API_KEY in scripts/.env — https://openrouter.ai/keys")
        return 1

    if not args.keep_audio and audio.exists():
        audio.unlink()
        print(f"[cleanup] deleted raw audio: {audio.name}")

    print(f"\n[done] {md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
