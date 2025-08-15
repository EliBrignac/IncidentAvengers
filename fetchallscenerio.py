#!/usr/bin/env python3
import os, sys, json, time, argparse, requests
from pathlib import Path
from typing import List, Dict

'''
run this script to fetch all scenarios from the hackathon api and save them to a json file using this command:
export HACK_BASE="https://sre-api-service-ext.bestegg.com"
export HACK_UA="Hackathon 8.2025"
python fetchallscenerio.py --out scenarios_full.json --per-file-dir scenarios/

optional:
# Fetch ALL scenarios, write combined file
python fetch_all_scenarios.py --out scenarios_full.json
'''
DEFAULT_BASE = os.getenv("HACK_BASE", "https://sre-api-service-ext.bestegg.com")
DEFAULT_UA   = os.getenv("HACK_UA",  "Hackathon 8.2025")
DEFAULT_AUTH = os.getenv("AUTH")  # e.g., "Bearer <TOKEN>"

LIST_PATH = "/hackathon/scenarios"
ITEM_PATH = "/hackathon/scenarios/{scenario_id}"

def build_headers() -> Dict[str, str]:
    h = {
        "User-Agent": DEFAULT_UA,
        "Accept": "application/json",
    }
    if DEFAULT_AUTH:
        h["Authorization"] = DEFAULT_AUTH
    return h

def get_json(url: str, session: requests.Session, retries: int = 3, backoff: float = 0.8):
    """GET JSON with simple retries/backoff."""
    for attempt in range(1, retries + 1):
        try:
            r = session.get(url, headers=build_headers(), timeout=20)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            if attempt == retries:
                raise
            time.sleep(backoff * attempt)

def fetch_all(base: str, session: requests.Session) -> List[Dict]:
    # 1) list scenarios (summaries)
    list_url = f"{base}{LIST_PATH}"
    summaries = get_json(list_url, session)
    if not isinstance(summaries, list):
        raise RuntimeError(f"Unexpected list response shape from {list_url}: {type(summaries)}")

    # 2) fetch each full scenario
    full = []
    for s in summaries:
        sid = s.get("scenario_id")
        if not sid:
            continue
        item_url = f"{base}{ITEM_PATH.format(scenario_id=sid)}"
        print(f"[INFO] Fetching {sid} …", file=sys.stderr)
        data = get_json(item_url, session)
        full.append(data)
    return full

def main():
    ap = argparse.ArgumentParser(description="Fetch full payloads for ALL hackathon scenarios.")
    ap.add_argument("--base", default=DEFAULT_BASE, help="Base URL (default env HACK_BASE or us1 host)")
    ap.add_argument("--out",  default="scenarios_full.json", help="Write combined JSON to this file")
    ap.add_argument("--per-file-dir", default="", help="If set, write one JSON file per scenario into this directory")
    args = ap.parse_args()

    base = args.base.rstrip("/")
    out  = Path(args.out)

    out.parent.mkdir(parents=True, exist_ok=True)
    if args.per_file_dir:
        Path(args.per_file_dir).mkdir(parents=True, exist_ok=True)

    with requests.Session() as sess:
        all_full = fetch_all(base, sess)

    # optional per-scenario files
    if args.per_file_dir:
        for item in all_full:
            sid = item.get("scenario_id", "unknown")
            Path(args.per_file_dir, f"{sid}.json").write_text(json.dumps(item, indent=2), encoding="utf-8")

    # combined file
    out.write_text(json.dumps(all_full, indent=2), encoding="utf-8")
    print(f"[OK] Wrote {len(all_full)} scenarios to {out}", file=sys.stderr)
    if args.per_file_dir:
        print(f"[OK] Also wrote per-scenario files to {args.per_file_dir}", file=sys.stderr)

if __name__ == "__main__":
    main()
