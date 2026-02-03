# nokwatch-scan

Listing scan plugin for [Nokwatch](https://github.com/jimididit/nokwatch). Monitors listing pages (e.g. eBay, job boards, classifieds) for new or changed items and notifies you via Nokwatch’s email, Discord, or Slack channels.

## Requirements

- **Nokwatch** (main app) installed and running
- Python 3.10+
- `requests`, `beautifulsoup4`, `jsonpath-ng` (installed automatically with this plugin)

## Installation

With your Nokwatch environment active:

```bash
pip install nokwatch-scan
```

Or from source (e.g. from the Nokwatch repo):

```bash
pip install -e plugins/nokwatch-scan
```

Restart Nokwatch so it picks up the plugin. **Scanner** will appear in the menu; open it to add and manage listing scan jobs.

## What it does

- **Listing scan jobs** – Configure a URL and an extractor (JSONPath for JSON APIs, or CSS selectors for HTML). Nokwatch fetches the page on a schedule, extracts items (title, URL, price), and notifies you when new items appear or match your filters.
- **Filters** – Optional text pattern and price range (min/max) to narrow results.
- **Scanner UI** – Add, edit, and run scan jobs from **Scanner** in the Nokwatch menu. Scan jobs also appear on the main dashboard; edit shared options (notifications, tags, cooldown) from the main **Edit Monitor** dialog.

## License

MIT
