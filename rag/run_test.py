"""
Quick test script: run conversion pipeline on the downloaded YouTube video.
Usage: python run_test.py
"""
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

CONFIG = Path(__file__).parent / "test_video_config.yaml"

if __name__ == "__main__":
    from file_conversion_router.utils.course_processor import convert_directory

    print(f"Starting pipeline for config: {CONFIG}")
    convert_directory(CONFIG, auto_embed=False)   # auto_embed=False: 先跳过 embedding，专注跑通转换
    print("Done. Check test_output/ for results.")
