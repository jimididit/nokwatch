"""Slack webhook notification service."""
import logging
import requests
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

def send_slack_notification(webhook_url: str, job: Dict, match_status: Dict, is_test: bool = False) -> bool:
    """
    Send notification to Slack via webhook.
    
    Args:
        webhook_url: Slack webhook URL
        job: Dictionary containing job configuration
        match_status: Dictionary containing match status information
        is_test: Boolean indicating if this is a test notification
    
    Returns:
        Boolean indicating if notification was sent successfully
    """
    try:
        if is_test:
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "Website Monitor - Test Notification"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "✓ *Configuration Successful!*\n\nThis is a test notification to verify your Slack webhook is configured correctly."
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Test Time:*\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        }
                    ]
                }
            ]
        else:
            match_text = "✅ MATCH FOUND" if match_status.get('match_found') else "❌ NO MATCH"
            condition_text = "contains" if job.get('match_condition') == 'contains' else "does not contain"
            
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"Website Monitor Alert: {job['name']}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Status:* {match_text}\n*Pattern:* `{job.get('match_pattern', 'N/A')}` ({condition_text})"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*URL:*\n<{job['url']}|{job['url']}>"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Response Time:*\n{match_status.get('response_time', 0):.2f}s"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Content Length:*\n{match_status.get('content_length', 0)} chars"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Check Time:*\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        }
                    ]
                }
            ]
        
        payload = {
            "blocks": blocks
        }
        
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        
        logger.info(f"Slack notification sent successfully for job {job.get('id', 'test')}")
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Slack notification: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending Slack notification: {e}", exc_info=True)
        return False
