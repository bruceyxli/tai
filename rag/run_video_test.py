"""
Minimal video-only test: bypasses directory_service to avoid MinerU dependency.
Directly calls VideoConverter -> apply_markdown_structure -> smart reading.
"""
import logging
import sys
import json
import uuid
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

VIDEO_FILE = Path("d:/tai/tai/rag/scraper/downloads/Object-Oriented Programming.mp4")
OUTPUT_DIR = Path("d:/tai/tai/rag/test_output/cs61a_oop_v2")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    from file_conversion_router.conversion.video_converter import VideoConverter

    file_uuid = str(uuid.uuid4())
    converter = VideoConverter(
        course_name="CS 61A",
        course_code="CS61A",
        file_uuid=file_uuid,
    )

    logging.info(f"Converting: {VIDEO_FILE}")
    (chunks, metadata), elapsed = converter.convert(
        VIDEO_FILE,
        OUTPUT_DIR,
        VIDEO_FILE.parent,
    )
    logging.info(f"Done in {elapsed:.1f}s. Chunks: {len(chunks)}")

    smart_reading = metadata.get("smart_reading") if isinstance(metadata, dict) else None
    if smart_reading:
        out = OUTPUT_DIR / f"{VIDEO_FILE.name}_smart_reading.json"
        with open(out, "w", encoding="utf-8") as f:
            json.dump(smart_reading, f, ensure_ascii=False, indent=2)
        logging.info(f"Smart reading: {len(smart_reading)} sections → {out}")
        for s in smart_reading:
            print(f"  [{s['start_time']:.1f}s-{s['end_time']:.1f}s] {s['title']}")
    else:
        logging.warning("No smart_reading in metadata")
