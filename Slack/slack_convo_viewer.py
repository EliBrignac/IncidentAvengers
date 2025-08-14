# -----------------------------
# This code scrapes Slack conversation data for all scenarios in the hackathon with the datetime stamp so we can integrate the same time stamp
# with Datadogs
# -----------------------------




#!/usr/bin/env python3
import argparse
import json
import sys
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import requests

UA = {"User-Agent": "Hackathon 8.2025"}

# -------- time utils --------
def to_utc_with_offset(ts: Optional[str]) -> Optional[str]:
    """
    Normalize an ISO8601 timestamp (naive, 'Z', or offset) to RFC3339 with +00:00.
    """
    if not ts:
        return None
    ts_norm = ts.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(ts_norm)
    except ValueError:
        ts_norm = ts_norm.split(".")[0] + "+00:00" if "+" not in ts_norm and "T" in ts_norm else ts_norm
        dt = datetime.fromisoformat(ts_norm)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.isoformat()

# -------- HTTP --------
def api_get(base_url: str, path: str) -> Any:
    url = base_url.rstrip("/") + path
    r = requests.get(url, headers=UA, timeout=30)
    r.raise_for_status()
    return r.json()

def api_post(base_url: str, path: str, payload: Dict[str, Any]) -> Any:
    url = base_url.rstrip("/") + path
    r = requests.post(url, json=payload, headers=UA, timeout=30)
    r.raise_for_status()
    if r.text and r.headers.get("content-type","").startswith("application/json"):
        return r.json()
    return {"status": "ok", "raw": r.text}

# -------- API slices --------
def list_scenarios(base_url: str) -> List[Dict[str, Any]]:
    return api_get(base_url, "/hackathon/scenarios")

def fetch_scenario_meta(base_url: str, scenario_id: str) -> Dict[str, Any]:
    """
    Pull the full scenario object so we can read created_at/updated_at.
    """
    return api_get(base_url, f"/hackathon/scenarios/{scenario_id}")

def fetch_slack(base_url: str, scenario_id: str) -> List[Dict[str, str]]:
    obj = api_get(base_url, f"/hackathon/scenarios/{scenario_id}/slack")
    return obj.get("slack_conversation", [])

# -------- main --------
def main():
    parser = argparse.ArgumentParser(description="Dump Slack for all scenarios with scenario timestamps.")
    parser.add_argument("--base-url", default="https://sre-api-service-ext.bestegg.com",
                        help="API base URL (default: %(default)s)")
    parser.add_argument("--out", default=None,
                        help="Optional path to write JSON output; prints to stdout if omitted")
    parser.add_argument("--reset", action="store_true",
                        help="Reset/seed scenarios before dumping (optional)")
    args = parser.parse_args()

    base_url = args.base_url
    try:
        if args.reset:
            print("Seeding scenarios…", file=sys.stderr)
            res = api_post(base_url, "/hackathon/reset", {})
            print(f"Seed result: {res}", file=sys.stderr)

        scenarios = list_scenarios(base_url)
        if not isinstance(scenarios, list) or not scenarios:
            print("No scenarios found.", file=sys.stderr)
            sys.exit(1)

        all_data = []
        for sc in scenarios:
            sid = sc.get("scenario_id")
            title = sc.get("title")
            try:
                # get full scenario to read timestamps
                meta = fetch_scenario_meta(base_url, sid)
                created_at = to_utc_with_offset(meta.get("created_at"))
                updated_at = to_utc_with_offset(meta.get("updated_at"))
            except requests.HTTPError as e:
                print(f"Warn: failed to fetch meta for {sid} ({title}): {e}", file=sys.stderr)
                created_at = None
                updated_at = None

            try:
                slack_msgs = fetch_slack(base_url, sid)
            except requests.HTTPError as e:
                print(f"Warn: failed to fetch slack for {sid} ({title}): {e}", file=sys.stderr)
                slack_msgs = []

            all_data.append({
                "scenario_id": sid,
                "title": title,
                "started_at_utc": created_at,   # scenario start time in UTC (+00:00)
                "updated_at_utc": updated_at,   # last update time in UTC (+00:00)
                "slack_conversation": slack_msgs
            })

        payload = json.dumps(all_data, indent=2, ensure_ascii=False)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(payload)
        else:
            print(payload)
    except requests.HTTPError as e:
        print(f"HTTP error: {e} | response={getattr(e.response,'text',None)}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
