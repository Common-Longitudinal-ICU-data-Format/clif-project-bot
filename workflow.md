# CLIF Project Bot Workflow

This document outlines the user flow and internal process for initiating and tracking CLIF job run requests via Slack.

---
## 0. Check active CLIF sites

In version 0.1, the CLIF project bot will track runs across 11 CLIF sites and the MIMIC-IV database:

1. University of Chicago
2. Emory University
3. John Hopkins University
4. Northwestern University
5. Oregon Health & Science University
6. Rush University
7. University of California San Francisco
8. University of Michigan
9. University of Minnesota
10. University of Pennsylvania
11. University of Toronto
12. MIMIC-IV

In near future versions, the CLIF bot will automatically identify CLIF sites from https://clif-consortium.shinyapps.io/clif-cohort-dashboard/ daily to update this list.

A long run feature update could be automated running of the project against MIMIC-IV, however this will require additional data use and project modification considerations

The point of contact (POC) for each CLIF Site will be designated with a command

`/clif-poc`

This will return a dropdown menu of active CLIF sites and a field to designate an active CLIF slack user with the (e.g. @user) 

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

- Project: Eligibility for Mobilization
- Repo: <GitHub Repo URL>
- Description: Determine which ICU patients meet mobilization eligibility criteria.
- Tables Required: patient, hospitalization, vitals, patient_assessments

Reply by clicking a button:
– ✅ : Run Completed
– 🛠 : In Progress
– ❌ : Will Not Participate

---

## 4. CLIF project status update

Any user can query the status of all active CLIF projects with the following command

`/clif-run status`

This returns a dashboard table with columns that correspond to all active CLIF projects and rows that correspond to CLIF sites. Each cell has values:

– ✅ : Run Completed
– 🛠 : In Progress
– ❌ : Will Not Participate
- ❓: No response

The bot will also post this weekly to the #clif-job-tracker and create a thread of reminder messages for sites that have not yet responded ❓. The reminder messages will have a reaction button option


