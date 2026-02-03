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

**Plugin and job-type tests:**

- **`tests/test_plugin_jobs.py`** – API tests for job-type-aware behavior: `GET /api/jobs` returns `job_type`, `POST /api/jobs` with `job_type: listing_scan` (relaxed match fields), `PUT /api/jobs` with plugin columns and empty pattern for scan jobs, export/import including `job_type` and plugin columns. These use a temporary test DB (see `conftest.py`); run with the project venv and dependencies installed (`pip install -r requirements.txt`).
- **`tests/test_nokwatch_scan.py`** – Unit tests for the nokwatch-scan plugin: `listing_extractor` (JSON/HTML extraction, JSONPath), `check_listing_page` (with mocked HTTP). Some tests are skipped if `jsonpath-ng` or `beautifulsoup4` are not installed. The plugin is loaded from `plugins/nokwatch-scan/src` when running pytest from the project root.

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

### nokwatch-scan plugin

To test the Scanner plugin (listing scan for JSON/HTML pages):

1. **Install the plugin** (if not already):

   ```bash
   pip install -e plugins/nokwatch-scan
   ```

2. **Restart the app** and open **Scanner** from the menu (or go to `/scan/`).

3. **Create a scan job** with a public JSON API. Example using JSONPlaceholder:

   - **Name:** `JSONPlaceholder posts`
   - **URL:** `https://jsonplaceholder.typicode.com/posts/` (trailing slash so item URLs resolve correctly)
   - **Match pattern:** leave empty or use `e.g.` to match items with "e.g." in the title
   - **Email:** your email (for notifications if a match is found)
   - **Extractor config** (expand "Extractor config (JSON)"):

     ```json
     {
       "items_path": "$[*]",
       "item_id": "$.id",
       "item_url": "$.id",
       "item_title": "$.title",
       "item_price": ""
     }
     ```

     Note: JSONPlaceholder doesn't have per-item URLs; `item_url` is optional. For APIs with `html_url` or `url`, use those paths instead.

4. **Run Check** – On the Scanner list, click **Run Check** for your job.

5. **Verify** – Open the main **Monitors** page; your scan job appears there. Expand it to see check history. The first run will treat all extracted items as "new" (match), so you may get a notification if configured. Later runs compare against `seen_item_ids`; only newly appearing items trigger a match.

**Alternative – GitHub Issues API:**

- **URL:** `https://api.github.com/repos/python/cpython/issues?per_page=10`
- **Extractor config:**

  ```json
  {
    "items_path": "$[*]",
    "item_id": "$.id",
    "item_url": "$.html_url",
    "item_title": "$.title",
    "item_price": ""
  }
  ```

GitHub may rate-limit unauthenticated requests; JSONPlaceholder is more reliable for quick tests.

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
