# Testing Nokwatch

This guide explains how to run the app, verify that features work, and (optionally) run automated tests.

## Before you start

1. **Use the project virtual environment** so all dependencies are available.
   - **Windows (PowerShell):** `.venv\Scripts\Activate.ps1`
   - **Windows (cmd):** `.venv\Scripts\activate.bat`
   - **Linux/macOS:** `source .venv/bin/activate`

2. **Install dependencies:**  
   `pip install -r requirements.txt`

3. **Configure `.env`** with at least SMTP settings (see `.env.example`).

4. **Start the app:**  
   `python app.py`  
   The app will be at `http://localhost:5000`.

## Quick checks in the UI

- **Test email** – Use "Test Email" in the header to confirm SMTP works.
- **Run a check** – Add a monitor, then use the play button on its card to run a check immediately.
- **Check history** – Open a monitor to see history, HTTP status, and (if enabled) diff/screenshots.

## Running automated tests

From the project root with the virtual environment activated:

```bash
pytest
```

This runs unit tests for core behavior (auth, templates, diff, notifications, credential encryption, AI with mocks, etc.). No app needs to be running.

**Optional – API/integration tests (app must be running):**

```bash
python tests/test_features.py
```

You’ll be prompted for an email address; the script will create test monitors, trigger checks, and clean up.

**Optional – Interactive monitor/email test:**

```bash
python tests/test_monitor.py
```

Follow the menu to test monitoring against httpbin.org and (optionally) send a test email.

## Verifying features manually

### Notifications

- **Email** – Set SMTP in `.env`, add a monitor with your email, trigger a match (or use "Test Email").
- **Discord** – In Advanced Options, add a notification channel, choose Discord, paste your webhook URL.
- **Slack** – Same as Discord, but choose Slack and paste the Slack webhook URL.
- **Cooldown** – Set "Notification Cooldown" on a monitor; trigger several matches and confirm you only get one notification per cooldown period.

### Advanced monitoring

- **HTTP status** – Set "HTTP Status Code Monitoring" to a code (e.g. 404). Use a URL that returns that code and confirm you get an alert.
- **Response time** – Set "Response Time Threshold" and use a slow URL; you should get an alert when the response exceeds that time.
- **JSON / API** – For a JSON URL, enable JSON monitoring and set a JSONPath (e.g. `$.key`); the monitor will match on the extracted value.
- **Auth** – In Advanced Options, add Basic Auth or custom headers/cookies for sites that require them.

### Other features

- **Templates** – When adding a monitor, choose "Start from template" to prefill settings.
- **Smart Setup** – Use "Smart Setup" to enter a URL and get suggested name/pattern/interval (optional AI).
- **Tags** – Add tags to monitors and filter by tag in the UI.
- **Export/Import** – Use Export to download all jobs as JSON; use Import to load them (e.g. on another machine).

## Troubleshooting

- **Test email not received** – Check `.env` SMTP settings, use an App Password for Gmail, and check spam.
- **Notifications not sent** – Confirm at least one channel is configured, check cooldown, and check app logs.
- **Advanced options not visible** – Expand "Advanced Options" in the Add/Edit Monitor form.
- **Database errors** – Ensure no other process is using `monitor.db`. If you need a clean start, you can remove `monitor.db` and restart the app (database will be recreated).

For more help, see the main [README](README.md) and the Troubleshooting section there.
