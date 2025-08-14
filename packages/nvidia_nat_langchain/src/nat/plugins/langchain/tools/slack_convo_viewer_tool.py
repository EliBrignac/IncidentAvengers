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
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import requests

UA = {"User-Agent": "Hackathon 8.2025"}

# Slack Conversation Viewer tool configuration
class SlackConvoViewerConfig(FunctionBaseConfig, name="slack_convo_viewer"):
    """
    Tool that retrieves Slack conversations for a given scenario.
    """
    base_url: str = "https://sre-api-service-ext.bestegg.com"
    reset_scenarios: bool = False

# Time utility function
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

# API helper functions
def api_get(base_url: str, path: str) -> Any:
    url = base_url.rstrip("/") + path
    r = requests.get(url, headers=UA, timeout=30)
    r.raise_for_status()
    return r.json()

def list_scenarios(base_url: str) -> List[Dict[str, Any]]:
    return api_get(base_url, "/hackathon/scenarios")

def fetch_scenario_meta(base_url: str, scenario_id: str) -> Dict[str, Any]:
    """Pull the full scenario object to read created_at/updated_at."""
    return api_get(base_url, f"/hackathon/scenarios/{scenario_id}")

def fetch_slack(base_url: str, scenario_id: str) -> List[Dict[str, str]]:
    obj = api_get(base_url, f"/hackathon/scenarios/{scenario_id}/slack")
    return obj.get("slack_conversation", [])

# Slack conversation viewer tool
@register_function(config_type=SlackConvoViewerConfig)
async def slack_convo_viewer(tool_config: SlackConvoViewerConfig, builder: Builder):
    """
    A tool that retrieves Slack conversations for scenarios.
    """
    async def _get_conversations(scenario_id: str = "") -> str:
        """
        Retrieve Slack conversations for a specific scenario or all scenarios.
        
        Args:
            scenario_id: ID of a specific scenario. If empty, returns conversations for all scenarios.
            
        Returns:
            str: Formatted string containing the conversations.
        """
        try:
            if tool_config.reset_scenarios:
                # Reset/seed scenarios if requested
                reset_url = f"{tool_config.base_url}/hackathon/reset"
                requests.post(reset_url, json={}, headers=UA, timeout=30)
            
            scenarios = list_scenarios(tool_config.base_url)
            if not scenarios:
                return "No scenarios found."
                
            result = []
            for sc in scenarios:
                sid = sc.get("scenario_id", "")
                title = sc.get("title", "Untitled")
                
                # If a specific scenario_id was provided, skip others
                if scenario_id and scenario_id.strip() and sid != scenario_id:
                    continue
                    
                try:
                    # Get scenario metadata
                    meta = fetch_scenario_meta(tool_config.base_url, sid)
                    created_at = to_utc_with_offset(meta.get("created_at"))
                    updated_at = to_utc_with_offset(meta.get("updated_at"))
                    
                    # Get Slack conversations
                    slack_msgs = fetch_slack(tool_config.base_url, sid)
                    
                    # Format the output
                    scenario_info = f"Scenario: {title} (ID: {sid})\nCreated: {created_at}\nUpdated: {updated_at}\n"
                    
                    if not slack_msgs:
                        scenario_info += "No Slack messages found for this scenario.\n"
                    else:
                        scenario_info += "Slack Conversation:\n"
                        for msg in slack_msgs:
                            user = msg.get("user", "Unknown")
                            text = msg.get("text", "")
                            ts = msg.get("ts", "")
                            scenario_info += f"{ts} - {user}: {text}\n"
                    
                    result.append(scenario_info)
                    
                except Exception as e:
                    result.append(f"Error processing scenario {sid} ({title}): {str(e)}")
                
                # If we were looking for a specific scenario, we can stop after finding it
                if scenario_id and sid == scenario_id:
                    break
            
            if not result:
                if scenario_id and scenario_id.strip():
                    return f"No scenario found with ID: {scenario_id}"
                return "No scenarios found."
                
            return "\n\n---\n\n".join(result)
            
        except Exception as e:
            return f"An error occurred while fetching Slack conversations: {str(e)}"

    # Create and yield the function info for the tool
    yield FunctionInfo.from_fn(
        _get_conversations,
        description=("""This tool retrieves Slack conversations for one or more scenarios.
                    
                    Args:
                        scenario_id (str, optional): ID of a specific scenario to retrieve. 
                            If not provided, returns conversations for all scenarios.
                    """),
    )
