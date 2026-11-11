"""
Automated Downloader for 50 Real-World CCTV & Violence Surveillance Videos
Source: AIRTLab Benchmark Video Dataset (IEEE & Data in Brief Research Benchmark)
Saves directly into: sample_videos/
"""

import os
import sys
import time
import urllib.request
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "sample_videos"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

GITHUB_BASE = "https://raw.githubusercontent.com/airtlab/A-Dataset-for-Automatic-Violence-Detection-in-Videos/master/violence-detection-dataset"

# 35 Real Violent / Crime Surveillance Videos + 15 Normal / False-Positive Surveillance Baseline Videos = 50 Total
VIDEOS_TO_DOWNLOAD = []

# 35 Violent / Physical Fight & Crime Clips
for i in range(1, 36):
    url = f"{GITHUB_BASE}/violent/cam1/{i}.mp4"
    dest = OUTPUT_DIR / f"real_crime_violent_{i:02d}.mp4"
    VIDEOS_TO_DOWNLOAD.append((url, dest, f"Crime / Violence Incident #{i}"))

# 15 Normal CCTV Baseline Clips
for i in range(1, 16):
    url = f"{GITHUB_BASE}/non-violent/cam1/{i}.mp4"
    dest = OUTPUT_DIR / f"real_cctv_normal_{i:02d}.mp4"
    VIDEOS_TO_DOWNLOAD.append((url, dest, f"Normal CCTV Baseline #{i}"))


def download_all(limit=50):
    print("=" * 70)
    print("[*] DOWNLOADING 50 REAL-WORLD CCTV SURVEILLANCE & CRIME VIDEOS")
    print(f"[*] Destination: {OUTPUT_DIR}")
    print("[*] Source: AIRTLab CCTV Dataset (Full HD Real Surveillance Clips)")
    print("=" * 70)

    success_count = 0
    failed_count = 0

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    targets = VIDEOS_TO_DOWNLOAD[:limit]

    for idx, (url, dest_path, desc) in enumerate(targets, 1):
        if dest_path.exists() and dest_path.stat().st_size > 50000:
            print(f"[{idx:02d}/{len(targets):02d}] Already exists: {dest_path.name} ({dest_path.stat().st_size // 1024} KB)")
            success_count += 1
            continue

        print(f"[{idx:02d}/{len(targets):02d}] Downloading {desc} -> {dest_path.name} ... ", end="", flush=True)
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=20) as resp, open(dest_path, "wb") as out_file:
                chunk = resp.read()
                out_file.write(chunk)
            
            size_kb = dest_path.stat().st_size // 1024
            print(f"DONE ({size_kb} KB)")
            success_count += 1
            time.sleep(0.1)
        except Exception as e:
            print(f"FAILED: {e}")
            failed_count += 1

    print("\n" + "=" * 70)
    print(f"[+] Download Summary: {success_count} Succeeded, {failed_count} Failed.")
    print(f"[*] All real surveillance videos are ready in: {OUTPUT_DIR}")
    print("=" * 70)


if __name__ == "__main__":
    download_all(50)
