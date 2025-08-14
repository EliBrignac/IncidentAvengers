import os, sys, json, requests
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

HACK_BASE = os.getenv("HACK_BASE", "https://sre-api-service-ext.bestegg.com")
SCENARIO_ID = os.getenv("SCENARIO_ID", "22222222-2222-2222-2222-222222222222")  # default to your scenario
MOCK_FILE = Path("mock_datadog.json")  # local fallback file
ENV = "prod"

def iso(dt): return dt.isoformat()
def now_window(minutes=30):
    now = datetime.now(timezone.utc)
    return now - timedelta(minutes=minutes), now

def hack_get(path):
    url = f"{HACK_BASE}{path}"
    headers = {
        "User-Agent": "Hackathon 8.2025",   # required by the admin’s gateway
        "Accept": "application/json",
    }
    auth = os.getenv("AUTH")  # optional future token, e.g., "Bearer <TOKEN>"
    if auth:
        headers["Authorization"] = auth
    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()
    return r.json()

def get_datadog_payloads():
    """Try real API, else fallback to local mock file."""
    try:
        print("[INFO] Trying live API...")
        return hack_get(f"/hackathon/scenarios/{SCENARIO_ID}/datadog").get("datadog_payloads", [])
    except requests.exceptions.HTTPError as e:
        print(f"[WARN] API request failed ({e}). Falling back to local mock file...")
    except requests.exceptions.RequestException as e:
        print(f"[WARN] Network error ({e}). Using local mock file...")

    if MOCK_FILE.exists():
        with open(MOCK_FILE) as f:
            return json.load(f).get("datadog_payloads", [])
    else:
        raise FileNotFoundError(f"Mock file not found: {MOCK_FILE}")

def parse_tag_value(tag_prefix, tags):
    for t in tags:
        if t.startswith(tag_prefix):
            return t.split(":", 1)[1]
    return None

def add_pct(buckets_dict):
    """Add 'pct' field to each bucket list based on total count."""
    for key in ["by_version", "by_host", "by_error_code"]:
        items = buckets_dict.get(key, [])
        total = sum(i.get("count", 0) for i in items) or 1
        for i in items:
            i["pct"] = round(100.0 * i.get("count", 0) / total, 2)
    return buckets_dict

def collect_buckets(datadog_payloads):
    by_version = Counter()
    by_host = Counter()
    by_error_code = Counter()
    dependencies = Counter()
    operations = Counter()

    for p in datadog_payloads:
        tags = p.get("tags", []) or []
        ver = parse_tag_value("version:", tags)
        host = parse_tag_value("host:", tags)
        errc = parse_tag_value("error.code:", tags)

        if ver:  by_version[ver] += 1
        if host: by_host[host] += 1
        if errc: by_error_code[errc] += 1

        dep = (parse_tag_value("peer.service:", tags) or
               parse_tag_value("db.instance:", tags) or
               parse_tag_value("http.host:", tags) or
               parse_tag_value("net.peer.name:", tags))
        if dep: dependencies[dep] += 1

        op = parse_tag_value("operation:", tags) or p.get("name")
        if op: operations[op] += 1

    def top_list(counter, k=5):
        return [{"value": val, "count": cnt} for val, cnt in counter.most_common(k)]

    return {
        "by_version": top_list(by_version),
        "by_host": top_list(by_host),
        "by_error_code": top_list(by_error_code),
    }, dependencies, operations

def build_compact_json(service, metric):
    start, end = now_window(30)
    payloads = get_datadog_payloads()
    logs_buckets, dependencies, operations = collect_buckets(payloads)

    metric_series = [
        {
            "key": item["value"],
            "points": [[int(end.timestamp()) * 1000, item["count"]]]
        }
        for item in logs_buckets["by_version"]
    ]
    metric_check = {"metric": metric, "split_by": "version", "series": metric_series}

    spans_sample = {
        "top_dependency": dependencies.most_common(1)[0][0] if dependencies else None,
        "top_operation": operations.most_common(1)[0][0] if operations else None,
        "sample": []
    }

    meta = {
        "window_minutes": 30,
        "semantics": {
            "logs_top_buckets": {
                "by_version": "Top version tags observed among monitor payloads in the time window.",
                "by_host": "Top host tags observed among monitor payloads in the time window.",
                "by_error_code": "Top error.code tags or inferred categories when tags are absent."
            },
            "counts_meaning":
                "count = number of monitor items matching the facet within the window (NOT request volume).",
            "metric_check":
                "Synthetic per-version magnitude using the bucket counts as a single point for visualization/localization.",
            "spans_sample":
                "Heuristic summary of likely dependency/operation from tags or monitor names; no raw spans in mock."
        },
        "sources": {
            "datadog_monitors": "https://docs.datadoghq.com/monitors/",
            "datadog_tags": "https://docs.datadoghq.com/getting_started/tagging/",
            "logs_analytics_api": "https://docs.datadoghq.com/api/latest/logs/",
            "metrics_timeseries_api": "https://docs.datadoghq.com/api/latest/metrics/",
            "events_api": "https://docs.datadoghq.com/api/latest/events/",
            "spans_search_api": "https://docs.datadoghq.com/api/latest/spans/",
            "latency_pXX_explainer": "https://docs.datadoghq.com/dashboards/guide/percentiles/",
            "http_error_rates": "https://docs.datadoghq.com/monitors/types/metric/#anomaly-and-outliers"
        }
    }

    return {
        "time_window": {"from": iso(start), "to": iso(end)},
        "service": service,
        "env": ENV,
        "logs_top_buckets": logs_buckets,
        "metric_check": metric_check,
        "events_near_spike": [],
        "spans_sample": spans_sample
    }

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python datadog_rca.py <service-name> <error-metric-name>")
        sys.exit(2)
    service = sys.argv[1]
    metric = sys.argv[2]
    print(json.dumps(build_compact_json(service, metric), indent=2))
