# CLIF Project Bot Workflow

This document outlines the user flow and internal process for initiating and tracking CLIF job run requests via Slack.

---

## 1. Command Initiation

**Trigger:**  
User issues the slash command:

`/clif-run new <GitHub Repo URL>`

Example:  
`/clif-run new https://github.com/Common-Longitudinal-ICU-data-Format/CLIF-eligibility-for-mobilization`


---

## 2. Repository Parsing

Once the command is received, the bot:

- Clones or fetches the repository.
- Reads structured metadata (e.g., `project.yaml` or `metadata.json`) when available:
  - `project_name`
  - `description`
  - `tables_required`
- If metadata is absent, extracts basic information from `README.md` as a fallback.

---

## 3. Slack Thread Creation

The bot posts a message in #clif-job-tracker in the [CLIF Slack](clifworld.slack.com) with the extracted project details and pings the channels

**Example message:**

The bot then starts tracking site responses.

📢 New CLIF Job Run Request

• Project: Eligibility for Mobilization
• Repo: https://github.com/
...
• Description: Determine which ICU patients meet mobilization eligibility criteria.
• Tables Required: patient, hospitalization, vitals, patient_assessments

Reply with a reaction or button:
– :white_check_mark: Run Completed
– :hammer_and_wrench: In Progress
– :x: Will Not Participate
---

## 4. Site Status Updates

Participating sites indicate their progress via:

- Emoji reactions on the bot’s thread (✅, 🛠, or ❌), or
- A follow-up command:
