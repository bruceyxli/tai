"""
Generate diff markdown for batch test videos.
Shows raw transcript vs smart reading side-by-side with del/ins markup.
"""
import json, pathlib, difflib, re, sys

sys.stdout.reconfigure(encoding='utf-8')

BASE = pathlib.Path("d:/tai/tai/rag/test_output/batch_test")

VIDEOS = [
    ("TED · The danger of a single story",       "TED Talk · Chimamanda Adichie (18.6 min)", "TED talk / monologue"),
    ("Veritasium · The Surprising Secret of Synchronization", "Veritasium · Synchronization (19.4 min)", "Science documentary"),
    ("MIT 18_01 · Single Variable Calculus L1",  "MIT 18.01 · Single Variable Calculus (51.5 min)", "STEM lecture"),
    ("Python tutorial · Corey Schafer decorators","Python Decorators · Corey Schafer (30.3 min)", "Coding tutorial"),
]

# Sections to highlight per video (0-based indices)
PICKS = {
    "TED · The danger of a single story":       [1, 6, 13, 18],
    "Veritasium · The Surprising Secret of Synchronization": [1, 7, 11, 19],
    "MIT 18_01 · Single Variable Calculus L1":  [0, 3, 8, 15],
    "Python tutorial · Corey Schafer decorators": [0, 2, 5, 10],
}


def word_diff_raw(raw: str, out: str) -> str:
    """Mark words removed in raw (red del) vs kept verbatim."""
    raw_words = raw.split()
    out_words = out.split()
    matcher = difflib.SequenceMatcher(None, raw_words, out_words, autojunk=False)
    parts = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        chunk = " ".join(raw_words[i1:i2])
        if tag == "equal":
            parts.append(chunk)
        elif tag in ("replace", "delete"):
            parts.append(f"<del>{chunk}</del>")
        # insert: raw had nothing here, skip
    return " ".join(parts) if parts else raw


def word_diff_out(raw: str, out: str) -> str:
    """Mark words in output that are new/transformed (green ins) vs verbatim."""
    raw_words = raw.split()
    out_words = out.split()
    matcher = difflib.SequenceMatcher(None, raw_words, out_words, autojunk=False)
    parts = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        chunk = " ".join(out_words[j1:j2])
        if tag == "equal":
            parts.append(chunk)
        elif tag in ("replace", "insert"):
            parts.append(f"<ins>{chunk}</ins>")
        # delete: out dropped these, skip
    return " ".join(parts) if parts else out


def load_video(folder: str):
    d = BASE / folder
    # raw transcript json
    raw_json = next(
        (f for f in d.iterdir() if f.suffix == ".json" and "smart" not in f.name), None
    )
    sr_json = next(
        (f for f in d.iterdir() if "smart_reading" in f.name and f.suffix == ".json"), None
    )
    if not raw_json or not sr_json:
        return None, None
    with open(raw_json, encoding="utf-8") as f:
        raw_segs = json.load(f)
    with open(sr_json, encoding="utf-8") as f:
        sr_segs = json.load(f)
    return raw_segs, sr_segs


def build_raw_lookup(raw_segs):
    """Map (start_time, end_time) → text, filtering title entries."""
    entries = [
        s for s in raw_segs
        if not str(s.get("speaker","")).startswith("title")
        and s.get("start time",0) != s.get("end time",0)
    ]
    return entries


CSS = """<style>
del { background: #ffd7d7; color: #8b0000; text-decoration: line-through; padding: 1px 2px; border-radius: 2px; }
ins { background: #d4edda; color: #155724; text-decoration: none; padding: 1px 2px; border-radius: 2px; }
.section { border: 1px solid #e1e4e8; border-radius: 6px; padding: 16px; margin-bottom: 24px; }
.timestamp { font-size: 12px; color: #888; font-family: monospace; margin-bottom: 4px; }
.title-row { font-size: 14px; margin-bottom: 10px; }
.label { font-size: 11px; font-weight: bold; color: #666; text-transform: uppercase; margin-top: 12px; margin-bottom: 4px; }
.stat { font-size: 12px; background: #f6f8fa; border-radius: 4px; padding: 6px 12px; margin-bottom: 8px; font-family: monospace; }
.video-section { margin-bottom: 56px; }
.video-label { background: #0366d6; color: white; padding: 8px 16px; border-radius: 6px; font-size: 15px; }
table { border-collapse: collapse; width: 100%; margin: 16px 0; font-size: 13px; }
th { background: #f6f8fa; padding: 6px 12px; border: 1px solid #ddd; text-align: left; }
td { padding: 6px 12px; border: 1px solid #ddd; }
hr { border: none; border-top: 2px solid #e1e4e8; margin: 32px 0; }
</style>"""

lines = []
lines.append("# Smart Reading — Batch Test Diff Report\n")
lines.append("## 4 Video Types: TED Talk / Science Doc / STEM Lecture / Coding Tutorial\n")
lines.append(CSS)
lines.append("\n---\n")

# Overall summary table
lines.append("## Overall Stats\n")
lines.append("<table>")
lines.append("<tr><th>Video</th><th>Type</th><th>Duration</th><th>Sections</th><th>Raw words</th><th>Output words</th><th>Compression</th></tr>")

summary_rows = [
    ("TED Talk · Chimamanda Adichie", "Monologue / humanities", "18.6 min", 27, 3035, 1310, "2.3×"),
    ("Veritasium · Synchronization", "Science documentary", "19.4 min", 34, 3356, 1197, "2.8×"),
    ("MIT 18.01 · Calculus L1", "STEM lecture", "51.5 min", 49, 5923, 1663, "3.6×"),
    ("Python Decorators · Corey Schafer", "Coding tutorial", "30.3 min", 31, 5145, 1329, "3.9×"),
]
for label, vtype, dur, sec, raw, out, comp in summary_rows:
    lines.append(f"<tr><td>{label}</td><td>{vtype}</td><td>{dur}</td><td>{sec}</td>"
                 f"<td>{raw:,}w</td><td><strong>{out:,}w</strong></td><td><strong>{comp}</strong></td></tr>")
lines.append("</table>\n\n---\n")

for folder, label, vtype in VIDEOS:
    raw_segs, sr_segs = load_video(folder)
    if raw_segs is None:
        continue

    raw_entries = build_raw_lookup(raw_segs)
    picks = PICKS[folder]
    total_raw = sum(len(s.get("text content","").split()) for s in raw_entries)
    total_out = sum(len(s.get("content","").split()) for s in sr_segs)
    comp = f"{total_raw/total_out:.1f}×" if total_out else "N/A"

    lines.append(f'<div class="video-section">')
    lines.append(f'<h2 class="video-label">{label} &nbsp;·&nbsp; {vtype}</h2>\n')
    lines.append(f"**{total_raw:,}w → {total_out:,}w &nbsp;({comp} compression) &nbsp;| "
                 f"{len(sr_segs)} sections**\n")

    for pick in picks:
        if pick >= len(sr_segs):
            continue
        sec = sr_segs[pick]
        t0, t1 = sec["start_time"], sec["end_time"]
        title = sec["title"]
        out_text = sec["content"]

        # Find raw segments that overlap this time window
        raw_chunk_words = []
        for rs in raw_entries:
            rs_t0 = rs.get("start time", 0)
            rs_t1 = rs.get("end time", 0)
            if rs_t1 < t0 - 2:
                continue
            if rs_t0 > t1 + 2:
                break
            raw_chunk_words.append(rs.get("text content", "").strip())
        raw_text = " ".join(raw_chunk_words)

        if not raw_text:
            continue

        raw_wc = len(raw_text.split())
        out_wc = len(out_text.split())
        comp_sec = f"{raw_wc/out_wc:.1f}×" if out_wc else "N/A"

        diff_raw = word_diff_raw(raw_text, out_text)
        diff_out = word_diff_out(raw_text, out_text)

        lines.append(f'\n<div class="section">')
        lines.append(f'<div class="timestamp">⏱ {t0:.1f}s → {t1:.1f}s</div>')
        lines.append(f'<div class="title-row">📌 <strong>{title}</strong></div>')
        lines.append(f'<div class="stat">Raw: {raw_wc}w → Smart Reading: {out_wc}w &nbsp;({comp_sec} compression)</div>')
        lines.append(f'\n<div class="label">▼ Raw — red = removed</div>\n')
        lines.append(diff_raw)
        lines.append(f'\n<div class="label">▲ Smart Reading — green = transformed</div>\n')
        lines.append(diff_out)
        lines.append('\n</div>\n\n---\n')

    lines.append('</div>\n\n---\n')

out_path = pathlib.Path("d:/tai/tai/rag/test_output/batch_test/batch_diff_report.md")
out_path.write_text("\n".join(lines), encoding="utf-8")
print(f"Written: {out_path} ({out_path.stat().st_size // 1024}KB)")
