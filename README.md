# CLIF Project Bot 🤖

A Slack-integrated bot to streamline federated CLIF project coordination across the consortium.  
This tool enables users to initiate and track each "CLIF project run" after releasing their code directly from Slack using a simple `/clif-run new [GITHUB_REPO]` command.

## 🔧 Core Features
- Auto-scrapes GitHub project metadata (e.g., name, description, tables required)
- Posts a summary in a designated Slack channel
- Allows sites to self-report job run status (✅, 🛠, ❌)
- Sends weekly reminder notifications to each site PI that has not completed the project run
- Tracks overall site responses and progress

## 🚀 Getting Started

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set the following environment variables for your Slack workspace:

```
SLACK_BOT_TOKEN=xxxx
SLACK_SIGNING_SECRET=xxxx
SLACK_APP_TOKEN=xxxx
JOB_TRACKER_CHANNEL=#clif-job-tracker  # optional
```

3. Run the Bolt application:

```bash
python app.py
```

The app exposes three slash commands:

- `/clif-run new <GitHub Repo>` – announce a new project run
- `/clif-run status` – view a table of site responses
- `/clif-poc <site> @user` – register a point-of-contact for a site
- `/clif-issues` – create a new issue in the CLIF repository

## 🧪 Status
**Under active development.**  
Expect rapid iteration and breaking changes. Contributions welcome!

## 💡 About CLIF
This bot supports the mission of the [Common Longitudinal ICU data Format (CLIF)](http://clif-icu.com/), which promotes transparency, interoperability, and federated data science in critical care.

---

© CLIF Consortium – Open collaboration encouraged.
