# Security

## How your data is stored

- **Monitor auth settings** (e.g. Basic Auth username/password, custom headers, cookies) are stored in the database as plain text (JSON).
- **Notification channel settings** (e.g. email addresses, Discord/Slack webhook URLs) are also stored as plain text in the database.

If someone gains access to your database or backup, they can read these values. Protect your database file and backups accordingly.

## What you should do

- **Do not commit `.env`** or your database file to version control.
- Use a **strong `SECRET_KEY`** in production (see `.env.example`).
- Run the app as a **non-root user** with minimal permissions.
- Use **HTTPS** in production (e.g. a reverse proxy like nginx).
- Restrict **filesystem and database access** to the app so only it can read/write its data.
- Keep **dependencies updated** so you get security fixes.

## Reporting a security issue

If you find a security vulnerability, please report it responsibly (e.g. via GitHub private vulnerability reporting or a private email to the maintainer) rather than opening a public issue.
