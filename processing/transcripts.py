"""Timed transcript parsing/normalization owned by extract_content."""
import html
import json
import math
import re
import xml.etree.ElementTree as ET


def timestamp(value):
    parts = str(value).replace(",", ".").split(":")
    return sum(float(v) * 60 ** n for n, v in enumerate(reversed(parts)))


def normalize(rows, rolling=False):
    segments = []
    for start, end, text in rows:
        if not isinstance(text, str) or isinstance(start, bool) or isinstance(end, bool):
            raise ValueError("Transcript text/timestamps have invalid types")
        try:
            start, end = float(start), float(end)
        except (TypeError, ValueError):
            raise ValueError("Transcript has no usable timestamps") from None
        if not math.isfinite(start) or not math.isfinite(end) or not 0 <= start < end:
            raise ValueError("Transcript has invalid timestamps")
        text = html.unescape(re.sub(r"<[^>]*>", "", text))
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            continue
        if segments and start < segments[-1]["start_seconds"]:
            raise ValueError("Transcript timestamps are out of order")
        if rolling and segments:
            previous = segments[-1]
            # Only remove exact repeats/word overlap in touching rolling cues;
            # actual repeated phrases later in the recording remain evidence.
            if start <= previous["end_seconds"] + 0.1:
                if text == previous["text"]:
                    previous["end_seconds"] = max(end, previous["end_seconds"])
                    continue
                old, new = previous["text"].split(), text.split()
                for size in range(min(len(old), len(new)), 0, -1):
                    if old[-size:] == new[:size]:
                        text = " ".join(new[size:])
                        break
        if text:
            segments.append({"segment_id": f"s-{len(segments)+1:06d}", "start_seconds": start,
                             "end_seconds": end, "text": text})
    if not segments:
        raise ValueError("Transcript has no usable timed speech")
    return segments


def bound_asr_segments(segments, duration):
    """Use the measured audio endpoint; never extend a recording to fit ASR."""
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("Invalid measured audio duration")
    bounded, clipped, discarded = [], 0, 0
    for segment in segments:
        if segment["start_seconds"] >= duration:
            discarded += 1
            continue
        row = dict(segment)
        if row["end_seconds"] > duration:
            row["end_seconds"] = duration
            clipped += 1
        bounded.append(row)
    if not bounded:
        raise ValueError("No ASR speech falls within the measured recording")
    return bounded, {"measured_duration_seconds": duration,
                     "clipped_end_count": clipped, "discarded_after_end_count": discarded}


def parse(content, rolling=False):
    text = content.decode("utf-8-sig")
    stripped = text.lstrip()
    rows = []
    if stripped.startswith(("{", "[")):
        obj = json.loads(text)
        if isinstance(obj, dict) and "events" in obj:  # YouTube json3
            for event in obj["events"]:
                if "tStartMs" in event and "dDurationMs" in event:
                    rows.append((event["tStartMs"] / 1000, (event["tStartMs"] + event["dDurationMs"]) / 1000,
                                 "".join(s.get("utf8", "") for s in event.get("segs", []))))
        else:
            for seg in obj.get("segments", []) if isinstance(obj, dict) else obj:
                rows.append((seg.get("start_seconds", seg.get("startTime", seg.get("start"))),
                             seg.get("end_seconds", seg.get("endTime", seg.get("end"))), seg.get("text", seg.get("body", ""))))
    elif "-->" in text:  # SRT / WebVTT (inline word timestamps removed as tags)
        lines = text.replace("\r\n", "\n").splitlines()
        for i, line in enumerate(lines):
            if "-->" not in line:
                continue
            before, after = line.split("-->", 1)
            body = []
            for following in lines[i+1:]:
                if not following.strip() or "-->" in following:
                    break
                body.append(following)
            rows.append((timestamp(before.strip()), timestamp(after.strip().split()[0]), " ".join(body)))
    elif stripped.startswith("<") and "<" in text:
        if "<!DOCTYPE" in text.upper() or "<!ENTITY" in text.upper():
            raise ValueError("Unsupported transcript XML")
        tree = ET.fromstring(text)
        for e in tree.iter():
            if e.tag.split("}")[-1] == "text" and "start" in e.attrib and "dur" in e.attrib:
                start = float(e.attrib["start"])
                rows.append((start, start + float(e.attrib["dur"]), "".join(e.itertext())))
            elif e.tag.split("}")[-1] == "p" and "begin" in e.attrib and "end" in e.attrib:
                rows.append((timestamp(e.attrib["begin"]), timestamp(e.attrib["end"]), "".join(e.itertext())))
    return normalize(rows, rolling=rolling)
