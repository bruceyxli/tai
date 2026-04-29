"""
Batch video test: download diverse video types, run smart reading pipeline, report stats.
"""
import json
import logging
import subprocess
import sys
import time
import uuid
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

DOWNLOAD_DIR = Path("d:/tai/tai/rag/scraper/downloads/batch_test")
OUTPUT_DIR   = Path("d:/tai/tai/rag/test_output/batch_test")
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Video playlist ────────────────────────────────────────────────────────────
# (label, url, category, language)
VIDEOS = [
    (
        "TED · The danger of a single story",
        "https://www.youtube.com/watch?v=D9Ihs241zeg",
        "TED talk / storytelling monologue",
        "en",
    ),
    (
        "Veritasium · The Surprising Secret of Synchronization",
        "https://www.youtube.com/watch?v=t-_VPRCtiUg",
        "Science documentary / informal narration",
        "en",
    ),
    (
        "MIT 18.01 · Single Variable Calculus L1",
        "https://www.youtube.com/watch?v=7K1sB05pE0A",
        "University lecture / STEM",
        "en",
    ),
    (
        "Bilibili · 十分钟了解黑洞",
        "https://www.bilibili.com/video/BV1Ux411j7CM",
        "Chinese science popularization",
        "zh",
    ),
    (
        "Python tutorial · Corey Schafer decorators",
        "https://www.youtube.com/watch?v=FsAPt_9Bf3U",
        "Coding tutorial / screencasting",
        "en",
    ),
]
# ─────────────────────────────────────────────────────────────────────────────


def download_video(label: str, url: str) -> Path | None:
    """Download video with yt-dlp, return local mp4 path or None on failure."""
    safe_label = "".join(c if c.isalnum() or c in " ·-_" else "_" for c in label)[:60]
    out_tmpl = str(DOWNLOAD_DIR / f"{safe_label}.%(ext)s")

    # Check if already downloaded
    existing = list(DOWNLOAD_DIR.glob(f"{safe_label}.*mp4"))
    if existing:
        logger.info(f"[SKIP] Already downloaded: {existing[0].name}")
        return existing[0]

    cmd = [
        str(Path("d:/tai/tai/rag/.venv/Scripts/yt-dlp.exe")),
        "--no-playlist",
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "-o", out_tmpl,
        url,
    ]
    logger.info(f"[DOWNLOAD] {label}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"yt-dlp failed:\n{result.stderr[-500:]}")
        return None

    found = list(DOWNLOAD_DIR.glob(f"{safe_label}*.mp4"))
    return found[0] if found else None


def run_pipeline(label: str, video_path: Path, category: str) -> dict:
    """Run smart reading pipeline on a single video, return stats dict."""
    from file_conversion_router.conversion.video_converter import VideoConverter

    out_dir = OUTPUT_DIR / video_path.stem
    out_dir.mkdir(parents=True, exist_ok=True)

    file_uuid = str(uuid.uuid4())
    converter = VideoConverter(
        course_name="BatchTest",
        course_code="BATCH",
        file_uuid=file_uuid,
    )

    logger.info(f"[PIPELINE] {label}")
    t0 = time.perf_counter()
    try:
        (chunks, metadata), elapsed = converter.convert(
            video_path, out_dir, video_path.parent
        )
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        return {"label": label, "category": category, "error": str(e)}

    smart_reading = metadata.get("smart_reading") if isinstance(metadata, dict) else None

    stats = {
        "label": label,
        "category": category,
        "video_file": video_path.name,
        "chunks": len(chunks),
        "pipeline_elapsed_s": round(elapsed, 1),
    }

    if smart_reading:
        total_input_words  = sum(len(s.get("content", "").split()) for s in smart_reading)
        # raw word count from the markdown transcript
        md_path = out_dir / (video_path.stem + ".md")
        raw_words = 0
        if md_path.exists():
            raw_words = len(md_path.read_text(encoding="utf-8").split())

        duration_s = smart_reading[-1]["end_time"] - smart_reading[0]["start_time"] if smart_reading else 0

        stats.update({
            "sections": len(smart_reading),
            "raw_words": raw_words,
            "output_words": total_input_words,
            "compression": round(raw_words / total_input_words, 1) if total_input_words else 0,
            "video_duration_min": round(duration_s / 60, 1),
            "sample_titles": [s["title"] for s in smart_reading[:3]],
        })

        # Save JSON sidecar
        out_json = out_dir / f"{video_path.name}_smart_reading.json"
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(smart_reading, f, ensure_ascii=False, indent=2)
        logger.info(f"  → {len(smart_reading)} sections, {raw_words}w → {total_input_words}w "
                    f"({stats['compression']}x), {elapsed:.0f}s")
    else:
        stats["sections"] = 0
        logger.warning("  → No smart_reading output")

    return stats


def print_report(all_stats: list[dict]) -> None:
    print("\n" + "=" * 90)
    print("BATCH TEST REPORT")
    print("=" * 90)
    header = f"{'Label':<42} {'Category':<30} {'Dur':>5} {'Sec':>4} {'Raw':>6} {'Out':>6} {'Comp':>5} {'Time':>6}"
    print(header)
    print("-" * 90)
    for s in all_stats:
        if "error" in s:
            print(f"{s['label'][:41]:<42} {'ERROR: ' + s['error'][:25]}")
            continue
        print(
            f"{s['label'][:41]:<42} "
            f"{s['category'][:29]:<30} "
            f"{s.get('video_duration_min', 0):>5.1f} "
            f"{s.get('sections', 0):>4} "
            f"{s.get('raw_words', 0):>6} "
            f"{s.get('output_words', 0):>6} "
            f"{s.get('compression', 0):>5.1f}x "
            f"{s.get('pipeline_elapsed_s', 0):>5.0f}s"
        )
    print("=" * 90)
    print("\nSample titles per video:")
    for s in all_stats:
        if "sample_titles" in s:
            print(f"\n  [{s['label'][:50]}]")
            for t in s["sample_titles"]:
                print(f"    • {t}")


if __name__ == "__main__":
    all_stats = []

    for label, url, category, lang in VIDEOS:
        print(f"\n{'─'*80}")
        print(f"  {label}  [{category}]")
        print(f"{'─'*80}")

        video_path = download_video(label, url)
        if video_path is None:
            all_stats.append({"label": label, "category": category, "error": "download failed"})
            continue

        stats = run_pipeline(label, video_path, category)
        all_stats.append(stats)

        # Save partial report after each video
        with open(OUTPUT_DIR / "batch_stats.json", "w", encoding="utf-8") as f:
            json.dump(all_stats, f, ensure_ascii=False, indent=2)

    print_report(all_stats)
