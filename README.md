# monitoringbot

This repository includes a lightweight reporting scheduler that aggregates monitoring
events from the last hour, renders an HTML summary, exports the raw data as CSV,
and delivers everything through an email or Slack-style file channel.

## Running the report scheduler

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Ensure the SQLite database contains an `events` table with the columns
   `id`, `occurred_at` (ISO timestamp), `severity`, `source`, and `message`.
3. Execute the job with the desired severity filters:
   ```bash
   python -m scheduler.reports --db-path /path/to/events.db --template-dir reports/templates \
       --output-dir /tmp/reports --channel slack --severities critical error warning
   ```

The Slack channel implementation writes the HTML and CSV artifacts to the chosen
output directory so the reports can be inspected without external services.
