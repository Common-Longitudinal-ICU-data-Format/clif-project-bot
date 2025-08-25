# CLIF Project Bot Workflow

This document outlines the user flow and internal process for initiating and tracking CLIF job run requests via Slack.

---

## Overview

The CLIF Project Bot streamlines federated CLIF project coordination across the consortium by:
- Facilitating project releases through interactive modals
- Automatically extracting project metadata from GitHub repositories
- Managing site point-of-contact (POC) assignments
- Tracking project status across all sites
- Providing persistent data storage for all assignments and project states

---

## Active CLIF Sites

The bot tracks runs across 12 CLIF sites and databases:

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

---

## Commands

### `/clif-poc` - Assign Site Point of Contact

Opens an interactive modal with:
- **Site dropdown**: Select from all 12 CLIF sites
- **User selector**: Choose any Slack user as POC
- **Project field**: Optional project-specific assignment

**Features:**
- Persistent storage of all POC assignments
- Support for multiple POCs per site
- Project-specific or general site assignments
- Confirmation messages posted to #project-tracker

### `/clif-run` - Release New Project

Opens an interactive modal collecting:
- **GitHub Repository URL**: Link to the CLIF project repository
- **Project Name**: Human-readable project name
- **Result Box Link**: Link to results/data storage
- **Special Instructions**: Optional additional guidance for sites

**Automated Processing:**
1. Scrapes GitHub repository for metadata and tables required
2. Posts announcement in **#general** mentioning all registered POCs
3. Posts detailed tracking information in **#project-tracker**
4. Adds interactive status buttons for site responses

### `/clif-status` - View Project Dashboard

Displays a formatted table showing:
- **Rows**: All 12 CLIF sites
- **Columns**: All active projects (truncated names for readability)
- **Status indicators**:
  - ✅ Run Completed
  - 🛠 In Progress  
  - ❌ Will Not Participate
  - ❓ No response

The dashboard is posted publicly to #project-tracker for all users to view.

### `/clif-help` - Request CLIF Assistance

Opens a simple form for submitting help requests.

- **Summary**: Brief description of the issue
- **Details**: Longer explanation or question (supports multiline input)

Submitted tickets are posted to **#clif-help** (configurable via `HELP_CHANNEL`) so the CLIF team can follow up.

---

## Workflow Process

### 1. Project Release Flow

1. **User runs `/clif-run`**
2. **Modal opens** requesting project details
3. **User fills form** with GitHub URL, project name, result box, and instructions
4. **Bot processes** by:
   - Extracting tables required from repository README or metadata files
   - Creating formatted announcement
   - Storing project in persistent database
5. **Bot posts to #general**:
   ```
   🚀 New CLIF Project Release 🚀
   
   @user has released code for [Project Name]!
   
   📊 Tables required: [extracted list]
   📋 Result Box: [provided link] 
   🔧 Special Instructions: [user input]
   
   🔗 Repository: [GitHub URL]
   
   @poc1 @poc2 @poc3: Please clone the repository and begin your analysis!
   ```
6. **Bot posts tracking info to #project-tracker** with status buttons
7. **Sites can update status** using interactive buttons

### 2. POC Management Flow

1. **User runs `/clif-poc`**
2. **Modal opens** with site dropdown, user selector, and project field
3. **User assigns POC** for specific site (and optionally specific project)
4. **Bot saves assignment** to persistent JSON storage
5. **Confirmation posted** to #project-tracker
6. **POC gets tagged** in future project announcements

### 3. Status Tracking Flow

1. **User runs `/clif-status`**
2. **Bot generates formatted table** from stored project data
3. **Table posted publicly** to #project-tracker showing all site statuses
4. **Status updates persist** through bot restarts via JSON storage

### 4. Help Ticket Flow

1. **User runs `/clif-help`**
2. **Modal opens** requesting a summary and detailed description of the issue
3. **Bot posts ticket** to #clif-help with the user's information
4. **Team members follow up** in the channel to resolve the request

---

## Data Persistence

All bot data is stored in `clif_bot_data.json`:

```json
{
  "projects": {
    "github_url": {
      "metadata": {...},
      "site_status": {"site": "status"}
    }
  },
  "pocs": {"user_id": "site_name"},
  "poc_assignments": {
    "site": {"user_id": "project_or_general"}
  }
}
```

This ensures all project states, POC assignments, and status updates survive bot restarts and provide a complete audit trail.


