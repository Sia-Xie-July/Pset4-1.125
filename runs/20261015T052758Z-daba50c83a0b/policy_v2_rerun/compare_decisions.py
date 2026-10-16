"""Compare v1 and v2 selection decisions for the same eligible items (analysis only)."""
import json
import sys
from collections import Counter
from pathlib import Path

d = Path(sys.argv[1])
def load(name):
    return {r["item_id"]: r for r in map(json.loads, (d / name).read_text().splitlines())}
v1, v2 = load("decisions_v1.jsonl"), load("decisions_v2.jsonl")
titles = {r["item_id"]: r["title"] for r in map(json.loads, (d / "eligible.jsonl").read_text().splitlines())}
review = {"python-3-15": "A1", "built-using-my-voice": "A2", "gemini-4-argon-in-github": "A3",
          "a839345e": "R1", "b861e88b": "R2", "QobBTNIIX04": "D1"}
def tag(item):
    return next((v for k, v in review.items() if k in item), "")
print("# Policy v1 vs v2 — selection stage only\n")
print("Same run, same 28 eligible items, same prompts and model; only the policy snapshot differs.\n")
for label, dec in (("v1", v1), ("v2", v2)):
    c = Counter(r["decision"] for r in dec.values())
    pieces = Counter(p for r in dec.values() for p in r["piece_ids"])
    print(f"- {label}: accept {c['accept']}, reject {c['reject']}, defer {c['defer']}; "
          f"piece assignments 01={pieces['01']} 02={pieces['02']} 03={pieces['03']}")
print("\n| Review ID | Item | v1 | v2 | v2 reason (start) |\n|---|---|---|---|---|")
for item in v1:
    a, b = v1[item], v2[item]
    if (a["decision"], a["piece_ids"]) != (b["decision"], b["piece_ids"]) or tag(item):
        print(f"| {tag(item)} | {titles[item][:60]} | {a['decision']} {','.join(a['piece_ids'])} | "
              f"{b['decision']} {','.join(b['piece_ids'])} | {b['reason'][:160].replace('|', '/')} |")
