# Nokwatch

[![CI](https://github.com/jimididit/nokwatch/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/jimididit/nokwatch/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A lightweight Python-based website monitoring tool. Can run on low-resource devices like a Raspberry Pi (see [Limited-resource devices](#limited-resource-devices)). Monitor multiple websites for content changes and get notifications by email, Discord, or Slack when your criteria are met.

---

**Contents**

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Plugins](#plugins)
- [Limited-resource devices](#limited-resource-devices)
- [Production (e.g. Raspberry Pi)](#production-eg-raspberry-pi)
- [Running as a System Service (Raspberry Pi)](#running-as-a-system-service-raspberry-pi)
- [API](#api)
- [Security](#security)
- [Troubleshooting](#troubleshooting)
- [License](#license)
- [Credits](#credits)

---

## Features

- **Multiple monitors** - Track many URLs with separate names, intervals, and patterns
- **Content matching** - String or regex; match when the page contains (or does not contain) text
- **Notifications** - Email, Discord webhooks, and Slack webhooks; multiple channels per monitor
- **Notification cooldown** - Throttle alerts so you don’t get spammed
- **HTTP status & response time** - Alert on specific status codes or when the site is slow
- **JSON/API monitoring** - Monitor JSON responses using JSONPath
- **Auth** - Basic Auth, custom headers, and cookies for protected pages
- **Tags** - Organize and filter monitors by tags
- **Templates** - Start from pre-built templates (e.g. waitlist, availability, status page)
- **Smart Setup** - Enter a URL and get suggested name, pattern, and interval (optional AI)
- **AI content detection** - Use OpenAI to detect semantic changes (optional; requires API key)
- **Check history** - View past checks, HTTP status, content diff, and optional screenshots
- **Export/Import** - Backup or move your monitors as JSON
- **Web UI** - Dark-themed, mobile-friendly interface; run checks on demand
- **Plugins** - Extend Nokwatch with optional plugins (Scanner for listing pages -eBay, Amazon, etc.; more in development)

## Requirements

- Python 3.10+
- SMTP account for email (Gmail, Outlook, Zoho, etc.); Discord/Slack optional
- Optional: OpenAI API key for Smart Setup AI and AI content detection

## Installation

1. **Clone and enter the project**

   ```bash
   git clone https://github.com/jimididit/nokwatch.git
   cd nokwatch
   ```

2. **Create and activate a virtual environment**

   ```bash
   python3 -m venv .venv
   # Windows (PowerShell): .venv\Scripts\Activate.ps1
   # Linux/macOS: source .venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**

   ```bash
   cp .env.example .env
   ```

   Edit `.env`: set `SECRET_KEY`, SMTP settings, and optionally `OPENAI_API_KEY` and `ENCRYPTION_KEY` (see [SECURITY.md](SECURITY.md) for encrypting auth credentials and notification config).  
   For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833), not your normal password.

5. **Run the app**

   ```bash
   python app.py
   ```

   Open `http://localhost:5000` in your browser. The database is created automatically on first run.

## Usage

1. Open the web UI at `http://localhost:5000` (or your server’s IP and port).
2. Click **Add Monitor** and fill in name, URL, check interval, match type, pattern, and notification email.
3. Use **Advanced Options** to add Discord/Slack, set cooldown, HTTP status or response time alerts, JSON path, auth, tags, or AI detection.
4. Use **Smart Setup** to paste a URL and get suggested settings, or **Start from template** when adding a monitor.
5. Use the play button on a monitor card to run a check immediately; open the card to see history, diff, and screenshots.

See [TESTING.md](TESTING.md) for step-by-step checks and troubleshooting.

## Plugins

Nokwatch supports optional plugins that add new job types and UI. Plugins share the same database and dashboard: you can manage all jobs (standard monitors and plugin jobs) from the main UI, and use the same notifications, tags, and cooldowns.

### Installing plugins

- **From the UI** – Open **Modules** in the menu to see available plugins. Install or uninstall from there (requires network; plugins are installed via pip).
- **From the command line** – From the project root with your venv active:  
  `pip install nokwatch-scan`  
  (or install from source: `pip install -e plugins/nokwatch-scan`). Restart the app so it picks up the plugin.

**Source code:** The **nokwatch-scan** plugin source is included in this repo under `plugins/nokwatch-scan`. Future plugins will live in a dedicated **nokwatch-plugins** repository (separate from the main Nokwatch repo).

### nokwatch-scan (Scanner)

The **Scanner** plugin monitors listing pages (e.g. eBay, job boards, classifieds) for new or changed items.

- **Listing scan jobs** – Configure a URL and an extractor (JSONPath for JSON APIs, or CSS selectors for HTML). Nokwatch fetches the page on a schedule, extracts items (title, URL, price), and notifies you when new items appear or match your filters.
- **Filters** – Optional text pattern and price range (min/max) to narrow results.
- **Scanner UI** – Use **Scanner** in the menu to add, edit, and manage scan jobs; run a check immediately to test.
- **Dashboard** – Scan jobs appear on the main dashboard. You can edit shared options (notifications, tags, cooldown, auth) from the main **Edit Monitor** dialog; for extractor config, use the Scanner’s edit page.

*More plugins are in development* (e.g. additional job types and integrations).

## Limited-resource devices

If you run Nokwatch on a device with limited disk or memory, use the minimal requirements for a smaller install (no AI features, no screenshots, no test deps). Core monitoring, notifications, and the Web UI still work:

```bash
pip install -r requirements-minimal.txt
```

## Production (e.g. Raspberry Pi)

- For a smaller install on limited resources, see [Limited-resource devices](#limited-resource-devices).
- Use a production WSGI server:  
  `pip install gunicorn` then  
  `gunicorn -w 2 -b 0.0.0.0:5000 app:app`
- Run as a systemd service so it starts on boot (example below).
- Use HTTPS via a reverse proxy (e.g. nginx). Never commit `.env` or your database.

## Running as a System Service (Raspberry Pi)

Create `/etc/systemd/system/nokwatch.service`:

```ini
[Unit]
Description=Nokwatch Website Monitor
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/nokwatch
Environment="PATH=/home/pi/nokwatch/.venv/bin"
ExecStart=/home/pi/nokwatch/.venv/bin/gunicorn -w 2 -b 0.0.0.0:5000 app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then: `sudo systemctl daemon-reload && sudo systemctl enable nokwatch.service && sudo systemctl start nokwatch.service`.  
Adjust paths to match your install directory.

## API

**Jobs**

- `GET /api/jobs` - List jobs (optional `?tag=name`)
- `POST /api/jobs` - Create job
- `PUT /api/jobs/<id>` - Update job
- `DELETE /api/jobs/<id>` - Delete job
- `GET /api/jobs/<id>/history` - Check history
- `GET /api/jobs/<id>/statistics` - Job statistics
- `POST /api/jobs/<id>/toggle` - Toggle active/inactive
- `POST /api/jobs/<id>/run-check` - Run check now
- `GET /api/jobs/<id>/notification-channels` - List notification channels
- `POST /api/jobs/<id>/notification-channels` - Add/replace notification channels
- `DELETE /api/jobs/<id>/notification-channels/<channel_id>` - Remove channel

**Tags**

- `GET /api/tags` - List tags
- `POST /api/tags` - Create tag

**Templates & setup**

- `GET /api/templates` - List monitor templates
- `POST /api/wizard/analyze` - Smart Setup analysis

**Export / import**

- `GET /api/export` - Export all jobs (JSON)
- `POST /api/import` - Import jobs

**Other**

- `GET /api/health` - Health check
- `GET /api/statistics` - Global statistics (optional `?hours=24`)
- `POST /api/test-email` - Send test email
- `GET /api/modules` - List available/installed plugins
- `POST /api/modules/install` - Install plugin
- `POST /api/modules/uninstall` - Uninstall plugin
- `POST /api/restart` - Restart app (if enabled)

**Plugin APIs** (when the plugin is installed)

- Scanner: `GET /api/scan/jobs`, `POST /api/scan/jobs`, `GET /api/scan/jobs/<id>`, `PUT /api/scan/jobs/<id>`, `DELETE /api/scan/jobs/<id>`

## Security

- Auth credentials and notification channel config are stored in the database; you can encrypt them at rest by setting `ENCRYPTION_KEY` in `.env` (see [SECURITY.md](SECURITY.md)). Restrict access to the app and database files.
- See [SECURITY.md](SECURITY.md) for details and how to report security issues.

## Troubleshooting

- **Email not received** - Check `.env` SMTP settings; use an App Password for Gmail; check spam and firewall (port 587 or 465).
- **Checks not running** - Ensure the monitor is Active and the app/scheduler started without errors (check logs).
- **Database issues** - Ensure the app has write permission in the project directory. To reset, remove `monitor.db` and restart (DB will be recreated).

## License

MIT - see [LICENSE](LICENSE).

## Credits

Developed as part of the Nokturnal project by jimididit.
