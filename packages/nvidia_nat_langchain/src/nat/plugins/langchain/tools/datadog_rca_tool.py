# SPDX-FileCopyrightText: Copyright (c) 2025, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig
from typing import Dict, Any, List, Optional
import os
import json
import requests
from datetime import datetime, timedelta, timezone
from collections import Counter

class DataDogRCAConfig(FunctionBaseConfig, name="datadog_rca"):
    """
    Tool that retrieves and analyzes DataDog metrics and logs for root cause analysis.
    """
    base_url: str = "https://sre-api-service-ext.bestegg.com"
    default_scenario_id: str = "22222222-2222-2222-2222-222222222222"
    default_env: str = "prod"
    window_minutes: int = 30

# Helper functions
def parse_tag_value(tag_prefix: str, tags: List[str]) -> Optional[str]:
    for t in tags:
        if t.startswith(tag_prefix):
            return t.split(":", 1)[1]
    return None

def collect_buckets(datadog_payloads: List[Dict]) -> tuple[Dict, Counter, Counter]:
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

@register_function(config_type=DataDogRCAConfig)
async def datadog_rca(tool_config: DataDogRCAConfig, builder: Builder):
    """
    A tool that retrieves and analyzes DataDog metrics and logs for root cause analysis.
    """
    async def _get_analysis(service: str, metric_name: str, scenario_id: str = "", window_minutes: int = 30) -> Dict:
        """
        Retrieve and analyze DataDog metrics and logs for a specific service.
        
        Args:
            service: The name of the service to analyze
            metric_name: The name of the metric to analyze
            scenario_id: Optional ID of a specific scenario. If empty, uses the default scenario.
            window_minutes: Time window in minutes to analyze (default: 30)
            
        Returns:
            Dict: Analysis results including metrics, logs, and potential root causes
        """
        try:
            # Use provided scenario_id or default
            scenario_id = scenario_id or tool_config.default_scenario_id
            
            # Fetch data from DataDog
            url = f"{tool_config.base_url}/hackathon/scenarios/{scenario_id}/datadog"
            headers = {
                "User-Agent": "Hackathon 8.2025",
                "Accept": "application/json",
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            payloads = response.json().get("datadog_payloads", [])
            
            # Process the data
            logs_buckets, dependencies, operations = collect_buckets(payloads)
            
            # Get time window
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(minutes=window_minutes)
            
            # Format metric series
            metric_series = [
                {
                    "key": item["value"],
                    "points": [[int(end_time.timestamp()) * 1000, item["count"]]]
                }
                for item in logs_buckets["by_version"]
            ]
            
            # Build the result
            result = {
                "time_window": {
                    "from": start_time.isoformat(),
                    "to": end_time.isoformat()
                },
                "service": service,
                "metric": metric_name,
                "env": tool_config.default_env,
                "analysis": {
                    "top_versions": logs_buckets["by_version"],
                    "top_hosts": logs_buckets["by_host"],
                    "error_codes": logs_buckets["by_error_code"],
                    "dependencies": [{"name": k, "count": v} for k, v in dependencies.most_common(5)],
                    "operations": [{"name": k, "count": v} for k, v in operations.most_common(5)]
                },
                "insights": []
            }
            
            # Add some basic insights
            if logs_buckets["by_error_code"]:
                top_error = logs_buckets["by_error_code"][0]
                result["insights"].append(
                    f"Top error code: {top_error['value']} ({top_error['count']} occurrences)"
                )
                
            if dependencies:
                top_dep = dependencies.most_common(1)[0]
                result["insights"].append(
                    f"Most active dependency: {top_dep[0]} ({top_dep[1]} calls)"
                )
                
            return result
            
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to fetch data from DataDog: {str(e)}"}
        except Exception as e:
            return {"error": f"An error occurred during analysis: {str(e)}"}

    # Create and yield the function info for the tool
    yield FunctionInfo.from_fn(
        _get_analysis,
        description="""This tool retrieves and analyzes DataDog metrics and logs for root cause analysis.
                    
                    Args:
                        service: The name of the service to analyze
                        metric_name: The name of the metric to analyze
                        scenario_id: Optional ID of a specific scenario. If empty, uses the default scenario.
                        window_minutes: Time window in minutes to analyze (default: 30)
                        
                    Returns:
                        Dict: Analysis results including metrics, logs, and potential root causes
                    """,
    )
