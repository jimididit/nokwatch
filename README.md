# Website Monitor

A lightweight Python-based website monitoring tool designed to run on Raspberry Pi 4. Monitor multiple websites for content changes and receive email notifications when your specified criteria are met.

## Features

- **Multiple URL Monitoring**: Monitor multiple websites independently with custom configurations
- **Flexible Content Matching**: Use simple string matching or regex patterns
- **Configurable Check Intervals**: Set check frequency from 30 seconds to 1 hour per monitor
- **Email Notifications**: Receive email alerts when matches are found
- **Check History**: View detailed history of all checks for each monitor
- **Modern Web UI**: Sleek, dark-themed, mobile-first web interface
- **Resource Efficient**: Optimized for Raspberry Pi 4 (4GB RAM)

## Requirements

- Python 3.7 or higher
- Raspberry Pi 4 (or any Linux/Windows machine)
- SMTP email account (Zoho, Gmail, Outlook, etc.)

## Installation

### 1. Clone or Download the Project

```bash
cd /path/to/project
```

### 2. Create Virtual Environment (Recommended)

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the example environment file and edit it:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your-secret-key-here-change-in-production

# Database
DATABASE_PATH=monitor.db

# SMTP Configuration
SMTP_HOST=smtp.<gmail | outlook | zoho>.com
SMTP_PORT=587
SMTP_USERNAME=your-email@<provider>.com
SMTP_PASSWORD=your-password
SMTP_USE_TLS=True

# Application Settings
DEFAULT_CHECK_INTERVAL=300
```

**Important Notes:**

- For Zoho, use your regular password. If you have 2FA enabled, you may need to generate an App Password from your Zoho account settings
- Generate a strong `SECRET_KEY` for production (you can use: `python -c "import secrets; print(secrets.token_hex(32))"`)

### 5. Initialize Database

The database will be created automatically on first run, but you can also initialize it manually:

```bash
python models.py
```

## Running the Application

### Development Mode

```bash
python app.py
```

The application will be available at `http://localhost:5000`

### Production Mode (Raspberry Pi)

For production deployment on Raspberry Pi, use a production WSGI server like Gunicorn:

```bash
pip install gunicorn
gunicorn -w 2 -b 0.0.0.0:5000 app:app
```

## Running as a System Service (Raspberry Pi)

Create a systemd service file for automatic startup:

### 1. Create Service File

```bash
sudo nano /etc/systemd/system/website-monitor.service
```

### 2. Add Service Configuration

```ini
[Unit]
Description=Website Monitor Service
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/website-monitor
Environment="PATH=/home/pi/website-monitor/venv/bin"
ExecStart=/home/pi/website-monitor/venv/bin/gunicorn -w 2 -b 0.0.0.0:5000 app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Note:** Adjust paths (`/home/pi/website-monitor`) to match your installation directory.

### 3. Enable and Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable website-monitor.service
sudo systemctl start website-monitor.service
```

### 4. Check Service Status

```bash
sudo systemctl status website-monitor.service
```

### 5. View Logs

```bash
sudo journalctl -u website-monitor.service -f
```

## Transferring to Raspberry Pi

### Method 1: Using SCP (Secure Copy)

From your Windows machine:

```powershell
scp -r E:\Projects\WaitList pi@raspberrypi.local:/home/pi/website-monitor
```

### Method 2: Using Git

On Raspberry Pi:

```bash
git clone <your-repo-url> website-monitor
cd website-monitor
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your settings
```

### Method 3: Using rsync

From your Windows machine (if rsync is available):

```bash
rsync -avz --exclude 'venv' --exclude '__pycache__' --exclude '*.db' E:\Projects\WaitList\ pi@raspberrypi.local:/home/pi/website-monitor/
```

## Testing

### Manual Testing

You can test the monitoring functionality without waiting for real websites to change:

**Option 1: Run Check Now Button**

- In the web UI, each monitor card has a "▶️" button
- Click it to immediately trigger a check for that monitor
- Results will appear in the check history

**Option 2: Test Script**

- Run the test script: `python test_monitor.py`
- This provides several test scenarios:
  - Test with httpbin.org (known test service)
  - Test pattern matching (string/regex)
  - Test email notifications
- Useful for verifying functionality before deploying

**Option 3: Test Email Button**

- Click "Test Email" in the web UI header
- Sends a test email to verify SMTP configuration

### Test URLs for Development

You can use these test URLs to verify monitoring works:

- `https://httpbin.org/html` - Always contains "Herman Melville" text
- `https://httpbin.org/json` - Returns JSON data
- `https://example.com` - Simple static website

Example test monitor:

- URL: `https://httpbin.org/html`
- Match Type: String
- Pattern: `Herman Melville`
- Condition: Contains
- This should always find a match!

## Usage

### Web Interface

1. Open your browser and navigate to `http://raspberrypi-ip:5000` (or `http://localhost:5000` locally)
2. Click "Add Monitor" to create a new monitoring job
3. Fill in the form:
   - **Job Name**: A descriptive name for this monitor
   - **URL**: The website URL to monitor
   - **Check Interval**: How often to check (30s to 1h)
   - **Match Type**: String (exact text) or Regex (pattern matching)
   - **Pattern**: The text or regex pattern to search for
   - **Match Condition**: Contains or Does Not Contain
   - **Email Recipient**: Email address for notifications
4. Click "Save" to start monitoring

### Example Use Cases

**Waitlist Monitoring:**

- URL: `https://example.com/waitlist`
- Match Type: String
- Pattern: `Waitlist Open`
- Condition: Contains
- Check Interval: 5 minutes

**Content Change Detection:**

- URL: `https://example.com/page`
- Match Type: Regex
- Pattern: `Available|In Stock|Buy Now`
- Condition: Contains
- Check Interval: 1 minute

## API Endpoints

The application provides a REST API for programmatic access:

- `GET /api/jobs` - List all monitoring jobs
- `POST /api/jobs` - Create a new job
- `PUT /api/jobs/<id>` - Update a job
- `DELETE /api/jobs/<id>` - Delete a job
- `GET /api/jobs/<id>/history` - Get check history for a job
- `POST /api/jobs/<id>/toggle` - Toggle job active/inactive
- `GET /api/health` - Health check endpoint

## Troubleshooting

### Email Notifications Not Working

1. Verify SMTP credentials in `.env`
2. For Zoho, ensure you're using the correct password. If 2FA is enabled, use an App Password from Zoho account settings
3. Check firewall settings - port 587 (TLS) or 465 (SSL) must be open
4. Check application logs for error messages

### Database Issues

- The database file (`monitor.db`) is created automatically
- Ensure the application has write permissions in the directory
- If you need to reset, delete `monitor.db` and restart the application

### Scheduler Not Running Checks

1. Verify jobs are marked as "Active"
2. Check application logs for scheduler errors
3. Ensure the scheduler started successfully (check logs on startup)

### Performance Issues on Raspberry Pi

- Reduce check intervals for less frequent monitoring
- Limit the number of active monitors
- Ensure adequate free memory (check with `free -h`)
- Consider using a swap file if memory is constrained

## Security Considerations

- **Never commit `.env` file** to version control
- Use strong `SECRET_KEY` in production
- Run the application as a non-root user
- Use HTTPS in production (set up reverse proxy with nginx)
- Keep dependencies updated for security patches

## Project Structure

```
waitlist-monitor/
├── app.py                 # Main Flask application
├── models.py              # Database models
├── monitor.py             # Core monitoring logic
├── email_service.py       # Email notification service
├── scheduler.py           # Task scheduler
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variables template
├── static/                # Frontend assets
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
├── templates/             # HTML templates
│   ├── index.html
│   └── base.html
└── README.md             # This file
```

## License

This project is open source and available for personal use.

## Support

For issues or questions:

1. Check the troubleshooting section above
2. Review application logs
3. Check that all dependencies are installed correctly

## Contributing

Contributions are welcome! Please ensure code follows PEP 8 style guidelines and includes appropriate error handling.
