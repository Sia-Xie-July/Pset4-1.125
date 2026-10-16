"""Exact-version/locator verification, shared by editorial/content/review only."""
import re
import subprocess
from datetime import date, timedelta
from pathlib import Path

from data.versioning import version_id
from lib.records import asset_path, canonical, load_json, utc_timestamp, validate_item
from lib.schemas import BRIEF, DECISION, REFERENCE, validate
from lib.stage_runtime import InvalidInput, OperationalFailure, records


class Evidence:
    def __init__(self, items, metadata):
        self.items, self.text, self.segments = {}, {}, {}
        try:
            upper = date.fromisoformat(metadata["as_of_date"])
        except (KeyError, ValueError):
            raise InvalidInput("Invalid run as-of date") from None
        if upper.isoformat() != metadata["as_of_date"]:
            raise InvalidInput("Run as-of date must use YYYY-MM-DD")
        self.as_of_date = upper.isoformat()
        for item in items:
            validate_item(item)
            if metadata.get("mode") == "live" and item.get("fixture") is True:
                raise InvalidInput("Fictional fixture evidence cannot support a live publication run")
            key = item["item_id"], item["version_id"]
            if key in self.items or any(existing[0] == key[0] for existing in self.items):
                raise InvalidInput("Eligible evidence must contain one version per underlying item")
            try:
                published = utc_timestamp(item["published_at"]).date()
            except ValueError:
                raise InvalidInput("Ineligible/unknown publication date in editorial evidence") from None
            if not upper - timedelta(days=29) <= published <= upper:
                raise InvalidInput("Evidence falls outside the run's inclusive date window")
            fetched = subprocess.run(["bash", "data/store.sh", "get", *key], capture_output=True, text=True)
            if fetched.returncode:
                if "Requested item/version not found" in fetched.stderr:
                    raise InvalidInput("Evidence source version is not stored")
                raise OperationalFailure("Cannot retrieve evidence through store.sh")
            saved = load_json(fetched.stdout)
            for field in ("item_id", "version_id", "source_id", "publisher_id", "kind", "title", "url", "published_at"):
                if item[field] != saved[field]:
                    raise InvalidInput("Eligible metadata differs from its stored source version")
            if version_id(saved, Path.cwd()) != saved["version_id"]:
                raise OperationalFailure("Retained source assets no longer match their evidence version")
            self.items[key] = saved
            self.text[key] = asset_path(Path.cwd(), saved["text_path"]).read_text(encoding="utf-8") if saved["text_path"] else None
            self.segments[key] = load_json(asset_path(Path.cwd(), saved["segments_path"]).read_text(encoding="utf-8")) if saved["segments_path"] else []

    def payload(self, keys=None):
        # Media segments already contain the full transcript. Sending the joined
        # text again wastes context and can exceed a provider's input limit.
        return [{"item": item, "text": self.text[key] if item["kind"] == "feed" else None,
                 "segments": self.segments[key]}
                for key, item in self.items.items() if keys is None or key in keys]

    def reference(self, ref, allowed=None):
        validate(REFERENCE, ref)
        key = ref["item_id"], ref["version_id"]
        if key not in self.items or allowed is not None and key not in allowed:
            raise InvalidInput("Claim references an unselected/unknown exact evidence version")
        locator = ref["locator"]
        if self.items[key]["kind"] == "feed":
            if locator["type"] != "text" or not locator["quote"].strip() or locator["quote"] not in (self.text[key] or ""):
                raise InvalidInput("Exact evidence quote does not exist in retained source text")
        elif locator["type"] != "segment" or not any(seg["segment_id"] == locator["segment_id"] for seg in self.segments[key]):
            raise InvalidInput("Evidence segment does not exist in retained transcript")

    def decisions(self, values):
        keys = set()
        for decision in values:
            validate(DECISION, decision)
            key = decision["item_id"], decision["version_id"]
            if key not in self.items or key in keys or len(set(decision["piece_ids"])) != len(decision["piece_ids"]):
                raise InvalidInput("Decisions must identify each eligible item exactly once")
            if decision["decision"] == "accept" and not decision["piece_ids"] or decision["decision"] != "accept" and decision["piece_ids"]:
                raise InvalidInput("Accepted items need piece assignments; reject/defer assignments must be empty")
            keys.add(key)
        if keys != set(self.items):
            raise InvalidInput("Decision output is incomplete")

    def briefs(self, values, accepted=None):
        if len(values) != 3 or {b.get("piece_id") for b in values if isinstance(b, dict)} != {"01", "02", "03"}:
            raise InvalidInput("Exactly three unique brief IDs 01, 02, 03 are required")
        arguments, all_claims, kinds = set(), set(), set()
        for brief in values:
            validate(BRIEF, brief)
            argument = brief["argument"].strip().casefold()
            if argument in arguments:
                raise InvalidInput("The briefs repeat the same central argument")
            arguments.add(argument)
            publishers = set()
            for claim in brief["claims"]:
                if claim["claim_id"] in all_claims or not re.fullmatch(re.escape(brief["piece_id"]) + r"-c[1-9]\d*", claim["claim_id"]):
                    raise InvalidInput("Claim IDs must be unique and scoped to their piece")
                all_claims.add(claim["claim_id"])
                allowed = accepted[brief["piece_id"]] if accepted is not None else None
                for ref in claim["evidence"]:
                    self.reference(ref, allowed)
                    source = self.items[ref["item_id"], ref["version_id"]]
                    publishers.add(source["publisher_id"])
                    kinds.add(source["kind"])
            if len(publishers) < 3:
                raise InvalidInput("Each brief must actually cite at least three independent publishers")
        if kinds != {"feed", "youtube", "podcast"}:
            raise InvalidInput("All three input types must contribute evidence to the series")

    def source_notes(self, brief):
        notes = ["## Sources", ""]
        for claim in brief["claims"]:
            notes.append("- **" + claim["claim_id"] + "**: " + claim["statement"])
            for ref in claim["evidence"]:
                key = ref["item_id"], ref["version_id"]
                source = self.items[key]
                locator = ref["locator"]
                url = source["url"]
                if locator["type"] == "segment":
                    seg = next(s for s in self.segments[key] if s["segment_id"] == locator["segment_id"])
                    passage = f"{seg['start_seconds']:g}–{seg['end_seconds']:g} seconds: {seg['text']}"
                    if source["kind"] == "youtube":
                        url += ("&" if "?" in url else "?") + "t=" + str(int(seg["start_seconds"]))
                else:
                    passage = '"' + locator["quote"] + '"'
                notes.append(f"  - [{source['title']}]({url}) — {passage} (version `{ref['version_id']}`).")
        return "\n".join(notes) + "\n"


def eligible(run, metadata):
    with (run / "eligible.jsonl").open(encoding="utf-8") as stream:
        return Evidence(records(stream), metadata)


def accepted_by_piece(evidence, decisions):
    evidence.decisions(decisions)
    result = {piece: set() for piece in ("01", "02", "03")}
    for decision in decisions:
        if decision["decision"] == "accept":
            for piece in decision["piece_ids"]:
                result[piece].add((decision["item_id"], decision["version_id"]))
    return result
