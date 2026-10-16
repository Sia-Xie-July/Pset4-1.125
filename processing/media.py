"""Download/probe/transcribe helpers belonging only to extract_content."""
import hashlib
import json
import os
import subprocess
from pathlib import Path

import requests
from yt_dlp import YoutubeDL
from processing.transcripts import normalize, parse
from lib.records import asset_path


class ItemFailure(Exception):
    pass


class QuietLogger:
    def debug(self, message): pass
    def warning(self, message): pass
    def error(self, message): pass


def ydl_options(**extra):
    return {"quiet": True, "no_warnings": True, "logger": QuietLogger(),
            "socket_timeout": 30, "retries": 1, **extra}


def youtube_info(url):
    # Select audio during metadata resolution too: process_info keeps the
    # selected format rather than reselecting it from the download options.
    with YoutubeDL(ydl_options(noplaylist=True, format="bestaudio/best")) as ydl:
        return ydl.extract_info(url, download=False)


def youtube_download(info, directory):
    options = ydl_options(noplaylist=True, format="bestaudio/best", outtmpl=str(directory / "original.%(ext)s"))
    with YoutubeDL(options) as ydl:
        ydl.process_info(dict(info))
    files = [p for p in directory.glob("original.*") if not p.name.endswith((".part", ".ytdl"))]
    if len(files) != 1:
        raise ItemFailure("Media download did not produce a complete file")
    return files[0]


def podcast_download(url, directory):
    path = directory / "original.audio"
    with requests.get(url, stream=True, timeout=(10, 60)) as response:
        response.raise_for_status()
        with path.open("wb") as output:
            for chunk in response.iter_content(1024 * 1024):
                output.write(chunk)
    if not path.stat().st_size:
        raise ItemFailure("Downloaded media is empty")
    return path


def duration(path):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
                            capture_output=True, text=True, timeout=30)
    try:
        value = float(json.loads(result.stdout)["format"]["duration"])
        if result.returncode or value <= 0:
            raise ValueError
        return value
    except (ValueError, KeyError):
        raise ItemFailure("Unable to establish recording duration") from None


def timed_native(candidate, info, warnings):
    choices = []
    if candidate["kind"] == "youtube":
        preferences = os.getenv("TRANSCRIPT_LANGUAGES", "en,en-US,en-GB").split(",")
        for origin, tracks in (("manual", info.get("subtitles", {})), ("automatic", info.get("automatic_captions", {}))):
            languages = [lang for lang in preferences if lang in tracks]
            # Manual subtitles in another language still outrank generated tracks.
            languages += [lang for lang in sorted(tracks) if lang not in languages and lang != "live_chat"]
            for lang in languages:
                entries = sorted(tracks[lang], key=lambda t: {"json3": 0, "vtt": 1, "srt": 2, "ttml": 3}.get(t.get("ext"), 9))
                for track in entries:
                    if track.get("ext") in ("json3", "vtt", "srt", "ttml"):
                        choices.append((track["url"], origin == "automatic", origin, lang))
    else:
        choices = [(t["url"], False, "podcast_feed", None) for t in candidate.get("transcript_urls", [])]
    for url, rolling, origin, lang in choices:
        try:
            response = requests.get(url, timeout=(10, 30))
            response.raise_for_status()
            segments = parse(response.content, rolling=rolling)
            return segments, {"method": "native_captions", "model": None, "origin": origin, "language": lang}
        except (requests.RequestException, ValueError, KeyError, TypeError, AttributeError, SyntaxError, UnicodeError):
            warnings.append("Native transcript unavailable or lacks usable timestamps; trying next option")
    return None, None


_models = {}


def transcribe(path, directory):
    from faster_whisper import WhisperModel
    model_name = os.getenv("WHISPER_MODEL", "base")
    device = os.getenv("WHISPER_DEVICE", "cpu")
    compute = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
    converted = directory / "transcription.wav"
    result = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(path), "-vn", "-ar", "16000", "-ac", "1", str(converted)],
                            capture_output=True, timeout=120)
    if result.returncode:
        raise ItemFailure("ffmpeg audio conversion failed")
    key = (model_name, device, compute)
    try:
        if key not in _models:
            _models[key] = WhisperModel(model_name, device=device, compute_type=compute)
        generated, info = _models[key].transcribe(str(converted), beam_size=1)
        segments = normalize([(s.start, s.end, s.text) for s in generated])
    except Exception as exc:
        raise ItemFailure(f"faster-whisper operation failed ({type(exc).__name__}); check dependencies/model access") from None
    return segments, {"method": "faster_whisper", "model": model_name, "device": device,
                      "compute_type": compute, "language": info.language, "executed": True}


def file_hash(path):
    hasher = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def retain_file(source, folder, suffix):
    folder = asset_path(Path.cwd(),folder.as_posix())
    folder.mkdir(parents=True, exist_ok=True)
    digest = file_hash(source)
    target = asset_path(Path.cwd(),(folder.relative_to(Path.cwd()) / (digest + suffix)).as_posix())
    if target.exists():
        if file_hash(target) != digest:
            raise ItemFailure("Existing content-addressed asset is corrupt")
    else:
        # Hard-link publishes the complete file atomically without overwrite.
        try:
            os.link(source, target)
        except FileExistsError:
            if file_hash(target) != digest:
                raise ItemFailure("Concurrent asset hash mismatch") from None
    return target.relative_to(Path.cwd()).as_posix(), digest
