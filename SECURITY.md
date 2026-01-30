# Security

## How your data is stored

- **Monitor auth settings** (Basic Auth username/password, custom headers, cookies) and **notification channel settings** (email addresses, Discord/Slack webhook URLs) are stored in the database.
- **Credential encryption (optional):** If you set `ENCRYPTION_KEY` in `.env` (see `.env.example`), these values are encrypted at rest using Fernet (symmetric encryption). Without `ENCRYPTION_KEY`, they are stored as plain text for backward compatibility. Existing plain-text data continues to work; new and updated values are encrypted when the key is set.
- If someone gains access to your database or backup, they can read **plain-text** values. With encryption enabled, they would need your `ENCRYPTION_KEY` to decrypt. Protect your database file, backups, and `.env` (including `ENCRYPTION_KEY`) accordingly.

## What you should do

- **Do not commit `.env`** or your database file to version control.
- Use a **strong `SECRET_KEY`** in production (see `.env.example`).
- **Optional:** Set **`ENCRYPTION_KEY`** to encrypt auth credentials and notification channel config in the database. Generate a key with:  
  `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
- Run the app as a **non-root user** with minimal permissions.
- Use **HTTPS** in production (e.g. a reverse proxy like nginx).
- Restrict **filesystem and database access** to the app so only it can read/write its data.
- Keep **dependencies updated** so you get security fixes.

## Reporting a security issue

If you find a security vulnerability, please report it responsibly (e.g. via GitHub private vulnerability reporting or a private email to the maintainer) rather than opening a public issue.
