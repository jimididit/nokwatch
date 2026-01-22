# Testing Guide for Phase 0 & Phase 1 Features

This guide helps you test all the features implemented in Phase 0 (Security Updates) and Phase 1 (Core Enhancements).

## Prerequisites

1. **Install/Update Dependencies**

   ```bash
   pip install --upgrade -r requirements.txt
   ```

2. **Verify Package Versions**

   ```bash
   pip show requests werkzeug
   ```

   Should show:
   - `requests` version `2.32.4`
   - `werkzeug` version `3.1.5`

3. **Configure Environment Variables**
   Make sure your `.env` file has SMTP credentials configured:

   ```env
   SMTP_HOST=smtp.gmail.com  # or your provider
   SMTP_PORT=587
   SMTP_USERNAME=your-email@example.com
   SMTP_PASSWORD=your-app-password
   SMTP_USE_TLS=True
   ```

4. **Start the Flask Application**

   ```bash
   python app.py
   ```

   The app should be running at `http://localhost:5000`

## Automated Testing

Run the comprehensive test script:

```bash
python test_features.py
```

This will test:

- Health check endpoint
- Test email functionality
- Creating monitors (basic and advanced)
- Getting all jobs
- Manual check triggers
- Check history
- Updating monitors
- Notification channels
- And more...

## Manual Testing Checklist

### Phase 0: Security Updates ✓

- [x] **Dependencies Updated**
  - Verify `requests==2.32.4` and `werkzeug==3.1.5` are installed
  - Application starts without errors

### Phase 1: Core Enhancements

#### 1. Test Email Functionality

1. Open the web UI at `http://localhost:5000`
2. Click the "Test Email" button in the header
3. Enter your email address when prompted
4. Check your inbox for the test email
5. Verify the email contains SMTP configuration details

**Expected Result:** You receive a test email with SMTP configuration details.

**Troubleshooting:**

- Check `.env` file has correct SMTP credentials
- For Gmail: Use an App Password, not your regular password
- Check firewall allows port 587 (TLS) or 465 (SSL)
- Check application logs for error messages

#### 2. Advanced Options Accordion

1. Click "Add Monitor" button
2. Fill in basic fields (name, URL, etc.)
3. Scroll down to "Advanced Options"
4. Click on "Advanced Options" to expand/collapse

**Expected Result:** The accordion expands and shows:

- Notification Cooldown dropdown
- HTTP Status Code Monitoring input
- Response Time Threshold input
- Notification Channels section

**Troubleshooting:**

- If accordion doesn't expand, check browser console for JavaScript errors
- Verify CSS is loading correctly (check Network tab)

#### 3. Notification Throttling

1. Create a new monitor
2. Set "Notification Cooldown" to "5 minutes"
3. Save the monitor
4. Trigger multiple checks manually (using "Run Check Now")
5. Check notification behavior

**Expected Result:** Notifications are throttled - only one notification per cooldown period.

#### 4. HTTP Status Code Monitoring

1. Create a monitor with:
   - URL: `https://httpbin.org/status/404`
   - HTTP Status Code Monitoring: `404`
2. Save and wait for check, or trigger manually
3. Check if notification is sent when 404 is returned

**Expected Result:** Notification is sent when the specified HTTP status code is detected.

#### 5. Response Time Threshold

1. Create a monitor with:
   - URL: `https://httpbin.org/delay/6` (6 second delay)
   - Response Time Threshold: `5.0` seconds
2. Save and trigger check
3. Check if notification is sent when response time exceeds threshold

**Expected Result:** Notification is sent when response time exceeds the threshold.

#### 6. Multiple Notification Channels

1. Create or edit a monitor
2. Expand "Advanced Options"
3. Click "+ Add Channel"
4. Select channel type (email, discord, or slack)
5. Configure the channel:
   - **Email**: Enter comma-separated email addresses
   - **Discord**: Enter Discord webhook URL
   - **Slack**: Enter Slack webhook URL
6. Save the monitor

**Expected Result:**

- Channel is added and displayed in the form
- When a match is found, notifications are sent to all configured channels

**Testing Email Channels:**

- Add an email channel with multiple addresses: `email1@example.com, email2@example.com`
- Trigger a check that finds a match
- Verify both email addresses receive notifications

**Testing Discord (Optional):**

- Create a Discord webhook in your Discord server
- Add Discord channel with webhook URL
- Trigger a match
- Check Discord channel for notification

**Testing Slack (Optional):**

- Create a Slack webhook in your Slack workspace
- Add Slack channel with webhook URL
- Trigger a match
- Check Slack channel for notification

#### 7. Monitor History with HTTP Status

1. Create a monitor and let it run a few checks
2. Click on the monitor card to view history
3. Check that history entries show HTTP status codes

**Expected Result:** Check history displays HTTP status codes for each check.

#### 8. Update Monitor Settings

1. Edit an existing monitor
2. Change advanced settings (throttle, status code, response time)
3. Save changes
4. Verify settings are persisted

**Expected Result:** Updated settings are saved and applied to future checks.

## Common Issues & Solutions

### Issue: Test Email Not Received

**Possible Causes:**

1. SMTP credentials incorrect
2. Firewall blocking SMTP port
3. Email provider blocking automated emails
4. Email in spam folder

**Solutions:**

- Verify `.env` file has correct credentials
- Check application logs for SMTP errors
- Try checking spam folder
- For Gmail: Enable "Less secure app access" or use App Password

### Issue: Advanced Options Not Expanding

**Possible Causes:**

1. JavaScript errors
2. CSS not loading
3. Browser compatibility

**Solutions:**

- Check browser console (F12) for errors
- Verify all CSS/JS files are loading
- Try a different browser
- Clear browser cache

### Issue: Notifications Not Sending

**Possible Causes:**

1. Notification throttling active
2. No channels configured
3. SMTP/webhook configuration incorrect

**Solutions:**

- Check notification throttle settings
- Verify at least one notification channel is configured
- Check application logs for errors
- Test email/webhook separately

### Issue: Database Migration Errors

**Possible Causes:**

1. Existing database schema conflicts
2. Database locked

**Solutions:**

- Delete `monitor.db` and restart app (will recreate with new schema)
- Ensure no other process is using the database
- Check file permissions

## Verification Commands

### Check Package Versions

```bash
pip show requests werkzeug flask
```

### Check Database Schema

```bash
python -c "from models import init_db; init_db(); print('Database initialized')"
```

### Check Application Logs

Monitor logs while testing:

```bash
python app.py
```

Watch for error messages in the console output.

## Next Steps

After verifying all Phase 0 and Phase 1 features work correctly, you can proceed to Phase 2 (Advanced Features) from the development plan.
