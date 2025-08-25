# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Slack-integrated bot for coordinating CLIF (Common Longitudinal ICU data Format) project runs across a consortium of 11 research sites plus MIMIC-IV. The bot enables users to initiate project runs, track site responses, and manage point-of-contact information through Slack slash commands.

## Development Commands

### Installation
```bash
pip install -r requirements.txt
```

### Running the Application
```bash
python app.py
```

### Testing
```bash
python -m pytest tests/
# Or run specific test
python tests/test_metadata.py
```

## Environment Variables

Required environment variables for Slack integration:
- `SLACK_BOT_TOKEN` - Slack bot token for API access
- `SLACK_SIGNING_SECRET` - Slack signing secret for request verification  
- `SLACK_APP_TOKEN` - Slack app token for socket mode
- `JOB_TRACKER_CHANNEL` - Slack channel for posting announcements (defaults to "#clif-job-tracker")

## Architecture

### Core Components

**app.py** - Main Slack Bolt application with three slash commands:
- `/clif-run new <GitHub_Repo>` - Initiates a new project run
- `/clif-run status` - Shows status table of all active projects  
- `/clif-poc <site> @user` - Registers point-of-contact for a site

**clif_bot/metadata.py** - Repository metadata extraction:
- `ProjectMetadata` dataclass containing project_name, description, and tables_required
- `parse_repo()` function that attempts to read structured metadata files (project.yaml, metadata.json) or falls back to parsing README.md

**clif_bot/state.py** - In-memory state management:
- `StatusStore` class managing projects and point-of-contact mappings
- `ProjectStatus` dataclass tracking site responses per project
- Hardcoded list of 11 CLIF consortium sites plus MIMIC-IV

### Data Flow

1. User runs `/clif-run new <repo>` command
2. Bot calls `parse_repo()` to extract metadata from GitHub repository
3. Creates new `ProjectStatus` in `StatusStore` with default "❓" status for all sites
4. Posts announcement message in Slack channel with interactive buttons
5. Site representatives click buttons to update their status (✅/🛠/❌)
6. Status updates are stored in `StatusStore` and can be viewed via `/clif-run status`

### Site Management

The system tracks responses from these 12 entities:
- University of Chicago, Emory University, John Hopkins University, Northwestern University
- Oregon Health & Science University, Rush University, University of California San Francisco
- University of Michigan, University of Minnesota, University of Pennsylvania
- University of Toronto, MIMIC-IV

Point-of-contact mapping allows the bot to associate Slack users with specific sites for status updates.