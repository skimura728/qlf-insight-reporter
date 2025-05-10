# 📊 QLF Insight Reporter

A daily automation bot that pulls GA4 event data from BigQuery and posts a summary report to Notion every morning.

## ✅ Features

- Connects to BigQuery linked to GA4 (Google Analytics 4)
- Summarizes Android / Web app event data (daily + cumulative)
- Posts formatted Markdown reports to a Notion page
- Runs automatically every day at 6:00 AM JST using Render Cron Job

## 🛠 Tech Stack

- Python 3
- Google Cloud BigQuery
- Notion API
- Render (Cron Job)
- GitHub + `render.yaml`

## ⚙️ Environment Variables (configured in Render)

| Key                           | Purpose                                  |
|------------------------------|-------------------------------------------|
| `NOTION_API_TOKEN`           | Notion integration token                  |
| `NOTION_PAGE_ID`             | Destination Notion page ID                |
| `GOOGLE_APPLICATION_CREDENTIALS` | `/etc/secrets/qlf-key.json` (path to secret key) |

## 🔐 Secret File

- `qlf-key.json` (Google Cloud service account key)
- Upload this to Render → Secret Files and mount to `/etc/secrets/qlf-key.json`

## ⏰ Schedule Configuration

Set the following in Render Cron Job:

- Schedule: `0 21 * * *` (runs at 6:00 AM JST daily)
- Command: `python app_worker.py`

## 📄 Notion Report Example

```
# QLF Report - 2025-05-11

## Android
📅 Latest: events_20250510
- page_view: 15
- scroll: 9

🗓 Cumulative
- page_view: 120
- user_engagement: 43

## Web
📅 Latest: events_20250510
- screen_view: 7
- app_open: 5
```

## 📁 Project Structure

```
app.py                # Main execution script
requirements.txt      # Python dependencies
render.yaml           # Render Cron Job definition
```

## ✨ License

MIT