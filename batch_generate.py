#!/usr/bin/env python3
"""
Queue a batch of video topics to the MoneyPrinter API.

The DB-backed queue processes one job at a time, so you can enqueue a whole
list at once and walk away — the worker renders them sequentially. Each
finished video (and its metadata .txt) lands in the output/ folder.

Usage:
  python3 batch_generate.py                      # reads topics.txt
  python3 batch_generate.py mytopics.txt
  python3 batch_generate.py --aspect 16:9        # default aspect for all
  python3 batch_generate.py --voice en_us_001 --wait

topics.txt format:
  - One topic per line.
  - Blank lines and lines starting with '#' are ignored.
  - Optional per-line aspect override:  Why cats purr | 1:1

Environment:
  MP_API_BASE   Backend base URL (default: http://localhost:8080)
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

API_BASE = os.environ.get("MP_API_BASE", "http://localhost:8080").rstrip("/")
VALID_ASPECTS = {"9:16", "16:9", "1:1", "4:5"}


def _post(path, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API_BASE + path, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get(path):
    with urllib.request.urlopen(API_BASE + path, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def parse_topics(path):
    """Yield (subject, aspect_override_or_None) tuples from a topics file."""
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            aspect = None
            if "|" in line:
                line, _, maybe_aspect = line.rpartition("|")
                line = line.strip()
                maybe_aspect = maybe_aspect.strip()
                if maybe_aspect in VALID_ASPECTS:
                    aspect = maybe_aspect
                elif maybe_aspect:
                    print(f"  [!] Ignoring unknown aspect '{maybe_aspect}' for: {line}")
            if line:
                yield line, aspect


def wait_for_job(job_id, poll=10):
    """Block until a job reaches a terminal state; return the job dict."""
    while True:
        try:
            job = _get(f"/api/jobs/{job_id}")["job"]
        except urllib.error.URLError as err:
            print(f"  [!] Poll error: {err}; retrying...")
            time.sleep(poll)
            continue
        state = job.get("state")
        if state in ("completed", "failed", "cancelled"):
            return job
        time.sleep(poll)


def main():
    parser = argparse.ArgumentParser(description="Batch-queue MoneyPrinter topics.")
    parser.add_argument("topics_file", nargs="?", default="topics.txt")
    parser.add_argument("--aspect", default="9:16", choices=sorted(VALID_ASPECTS),
                        help="Default aspect ratio (per-line overrides win).")
    parser.add_argument("--voice", default="en_us_001", help="TikTok TTS voice.")
    parser.add_argument("--model", default="llama3.1:8b", help="Ollama model.")
    parser.add_argument("--paragraphs", type=int, default=1, help="Script length.")
    parser.add_argument("--min-duration", type=int, default=60, dest="min_duration",
                        help="Minimum video length in seconds (0 = use --paragraphs).")
    parser.add_argument("--threads", type=int, default=6,
                        help="CPU threads for video encoding.")
    parser.add_argument("--prompt", default="", help="Optional custom prompt.")
    parser.add_argument("--wait", action="store_true",
                        help="Wait for each job to finish before queuing the next.")
    args = parser.parse_args()

    if not os.path.exists(args.topics_file):
        print(f"Topics file not found: {args.topics_file}")
        print("Create one (one topic per line) or pass a path. See --help.")
        sys.exit(1)

    topics = list(parse_topics(args.topics_file))
    if not topics:
        print(f"No topics found in {args.topics_file}.")
        sys.exit(1)

    print(f"Queuing {len(topics)} topic(s) to {API_BASE} "
          f"(default aspect {args.aspect}, voice {args.voice})\n")

    queued = []
    for i, (subject, aspect_override) in enumerate(topics, 1):
        aspect = aspect_override or args.aspect
        payload = {
            "videoSubject": subject,
            "aiModel": args.model,
            "voice": args.voice,
            "paragraphNumber": args.paragraphs,
            "aspectRatio": aspect,
            "minDuration": args.min_duration,
            "threads": args.threads,
            "customPrompt": args.prompt,
        }
        try:
            resp = _post("/api/generate", payload)
        except urllib.error.URLError as err:
            print(f"[{i}/{len(topics)}] FAILED to queue '{subject}': {err}")
            print("  Is the backend running?  docker compose ps")
            continue

        job_id = resp.get("jobId")
        print(f"[{i}/{len(topics)}] queued '{subject}' ({aspect}) -> {job_id}")
        queued.append((subject, job_id))

        if args.wait and job_id:
            job = wait_for_job(job_id)
            if job.get("state") == "completed":
                print(f"        done -> {job.get('resultPath')}")
            else:
                print(f"        {job.get('state')}: {job.get('errorMessage')}")

    print(f"\nDone. {len(queued)} job(s) queued.")
    if not args.wait:
        print("They render sequentially in the background. Watch progress at "
              "http://localhost:8001 or check the output/ folder.")


if __name__ == "__main__":
    main()
