"""Email notification service for monitoring alerts."""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict

from core.config import Config

logger = logging.getLogger(__name__)

def send_notification(job: Dict, match_status: Dict, is_test: bool = False) -> bool:
    """
    Send email notification when a match is found, or send a test email.
    
    Args:
        job: Dictionary containing job configuration
        match_status: Dictionary containing match status information
        is_test: Boolean indicating if this is a test email
    
    Returns:
        Boolean indicating if email was sent successfully
    """
    if not Config.SMTP_USERNAME or not Config.SMTP_PASSWORD:
        logger.warning("SMTP credentials not configured. Skipping email notification.")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = Config.SMTP_USERNAME
        msg['To'] = job['email_recipient']
        
        if is_test:
            msg['Subject'] = "Website Monitor - Test Email"
        else:
            msg['Subject'] = f"Website Monitor Alert: {job['name']}"
        
        # Create email body
        if is_test:
            text_body = f"""
Website Monitor - Test Email

This is a test email to verify your SMTP configuration is working correctly.

If you received this email, your email settings are configured properly!

Test Details:
- SMTP Host: {Config.SMTP_HOST}
- SMTP Port: {Config.SMTP_PORT}
- From: {Config.SMTP_USERNAME}
- To: {job['email_recipient']}
- Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

You can now use the Website Monitor application to receive notifications when your monitored websites match your criteria.
            """
        else:
            match_text = "MATCH FOUND" if match_status.get('match_found') else "NO MATCH"
            condition_text = "contains" if job.get('match_condition') == 'contains' else "does not contain"
            
            text_body = f"""
Website Monitor Alert

Job Name: {job['name']}
URL: {job['url']}
Status: {match_text}

The website was checked and the pattern "{job.get('match_pattern', 'N/A')}" ({condition_text}) was found.

Check Details:
- Response Time: {match_status.get('response_time', 0):.2f} seconds
- Content Length: {match_status.get('content_length', 0)} characters
- Check Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Visit the monitoring dashboard to view more details.
            """
        
        if is_test:
            html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #2196F3; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .detail {{ margin: 10px 0; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        .success {{ color: #4CAF50; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>Website Monitor - Test Email</h2>
        </div>
        <div class="content">
            <p class="success">✓ SMTP Configuration Successful!</p>
            <p>This is a test email to verify your SMTP configuration is working correctly.</p>
            <p>If you received this email, your email settings are configured properly!</p>
            <hr>
            <div class="detail"><strong>SMTP Host:</strong> {Config.SMTP_HOST}</div>
            <div class="detail"><strong>SMTP Port:</strong> {Config.SMTP_PORT}</div>
            <div class="detail"><strong>From:</strong> {Config.SMTP_USERNAME}</div>
            <div class="detail"><strong>To:</strong> {job['email_recipient']}</div>
            <div class="detail"><strong>Test Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
            <hr>
            <p>You can now use the Website Monitor application to receive notifications when your monitored websites match your criteria.</p>
        </div>
        <div class="footer">
            <p>This is an automated test email from Website Monitor</p>
        </div>
    </div>
</body>
</html>
            """
        else:
            match_text = "MATCH FOUND" if match_status.get('match_found') else "NO MATCH"
            condition_text = "contains" if job.get('match_condition') == 'contains' else "does not contain"
            
            html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .detail {{ margin: 10px 0; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>Website Monitor Alert</h2>
        </div>
        <div class="content">
            <div class="detail"><strong>Job Name:</strong> {job['name']}</div>
            <div class="detail"><strong>URL:</strong> <a href="{job['url']}">{job['url']}</a></div>
            <div class="detail"><strong>Status:</strong> <span style="color: #4CAF50; font-weight: bold;">{match_text}</span></div>
            <div class="detail"><strong>Pattern:</strong> {job.get('match_pattern', 'N/A')}</div>
            <div class="detail"><strong>Condition:</strong> {condition_text}</div>
            <hr>
            <div class="detail"><strong>Response Time:</strong> {match_status.get('response_time', 0):.2f} seconds</div>
            <div class="detail"><strong>Content Length:</strong> {match_status.get('content_length', 0)} characters</div>
            <div class="detail"><strong>Check Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        </div>
        <div class="footer">
            <p>This is an automated notification from Website Monitor</p>
        </div>
    </div>
</body>
</html>
            """
        
        # Attach parts
        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))
        
        # Send email
        if Config.SMTP_USE_TLS:
            server = smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(Config.SMTP_HOST, Config.SMTP_PORT)
        
        server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Email notification sent successfully to {job['email_recipient']}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP authentication failed: {e}")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error occurred: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to send email notification: {e}", exc_info=True)
        return False
