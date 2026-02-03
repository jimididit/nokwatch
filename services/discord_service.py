"""Discord webhook notification service."""
import logging
import requests
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

def send_discord_notification(webhook_url: str, job: Dict, match_status: Dict, is_test: bool = False) -> bool:
    """
    Send notification to Discord via webhook.
    
    Args:
        webhook_url: Discord webhook URL
        job: Dictionary containing job configuration
        match_status: Dictionary containing match status information
        is_test: Boolean indicating if this is a test notification
    
    Returns:
        Boolean indicating if notification was sent successfully
    """
    try:
        if is_test:
            embed = {
                "title": "Website Monitor - Test Notification",
                "description": "This is a test notification to verify your Discord webhook is configured correctly.",
                "color": 3447003,  # Blue
                "fields": [
                    {"name": "Status", "value": "✓ Configuration Successful!", "inline": False},
                    {"name": "Webhook URL", "value": webhook_url[:50] + "...", "inline": False},
                    {"name": "Test Time", "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "inline": False}
                ],
                "footer": {"text": "Website Monitor Test"},
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            match_text = "✅ MATCH FOUND" if match_status.get('match_found') else "❌ NO MATCH"
            condition_text = "contains" if job.get('match_condition') == 'contains' else "does not contain"
            color = 3066993 if match_status.get('match_found') else 15158332  # Green or Red
            fields = [
                {"name": "URL", "value": job['url'], "inline": False},
                {"name": "Response Time", "value": f"{match_status.get('response_time', 0):.2f} seconds", "inline": True},
                {"name": "Content Length", "value": f"{match_status.get('content_length', 0)} characters", "inline": True},
                {"name": "Check Time", "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "inline": False}
            ]
            matched_items = match_status.get('matched_items') or []
            if matched_items:
                items_text = "\n".join(
                    f"• [{it.get('title', 'N/A')[:50]}]({it.get('url', '')}) | {it.get('price', '')}"
                    for it in matched_items[:10]
                )
                if len(matched_items) > 10:
                    items_text += f"\n... and {len(matched_items) - 10} more"
                fields.insert(1, {"name": "New Items", "value": items_text or "—", "inline": False})
            if match_status.get('screenshot_path'):
                fields.append({"name": "Screenshot", "value": match_status.get('screenshot_path', ''), "inline": False})

            embed = {
                "title": f"Website Monitor Alert: {job['name']}",
                "description": f"**Status:** {match_text}\n\n**Pattern:** `{job.get('match_pattern', 'N/A')}` ({condition_text})",
                "color": color,
                "fields": fields,
                "footer": {"text": "Website Monitor"},
                "timestamp": datetime.utcnow().isoformat()
            }
        
        payload = {
            "embeds": [embed]
        }
        
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        
        logger.info(f"Discord notification sent successfully for job {job.get('id', 'test')}")
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Discord notification: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending Discord notification: {e}", exc_info=True)
        return False
