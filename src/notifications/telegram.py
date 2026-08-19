import os
import requests
from typing import List, Dict, Any

def send_telegram_notification(top_jobs: List[Dict[str, Any]]) -> bool:
    """
    Sends free Telegram notifications if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are configured.
    """
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        return False

    if not top_jobs:
        return True

    lines = ["🔥 *Daily Job Intelligence — Top Shortlist*\n"]
    for j in top_jobs[:5]:
        score = j.get("match_score", 0)
        company = j.get("company", "Company")
        title = j.get("title", "Role")
        url = j.get("url", "#")
        lines.append(f"• *{company}* — {title}\n  Score: `{score}/100` | [Apply Now]({url})\n")

    message_text = "\n".join(lines)
    api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    try:
        resp = requests.post(api_url, json={
            "chat_id": chat_id,
            "text": message_text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        print(f"Telegram notification failed: {e}")
        return False
