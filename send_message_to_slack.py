import requests
import os
import slack_bot_tokens

def send_slack_message(channel_id, text):
    url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {slack_bot_tokens.SLACK_BOT_TOKEN}"
    }
    payload = {
        "channel": channel_id,
        "text": text
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception(f"Request failed: {response.status_code} - {response.text}")
    data = response.json()
    if not data.get("ok"):
        raise Exception(f"Slack API error: {data.get('error')}")
    print("Message sent successfully!")
# Example usage
send_slack_message(slack_bot_tokens.CHANNEL_ID, "Hello from my Slackbot! :wave:")