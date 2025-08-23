"""Slack Bolt application for coordinating CLIF project runs."""
from __future__ import annotations

import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from clif_bot.metadata import parse_repo
from clif_bot.state import StatusStore


app = App(token=os.environ.get("SLACK_BOT_TOKEN"), signing_secret=os.environ.get("SLACK_SIGNING_SECRET"))
store = StatusStore()


@app.command("/clif-run")
def handle_clif_run(ack, respond, command):
    ack()
    text = command.get("text", "").strip()
    if text.startswith("new"):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            respond("Usage: /clif-run new <GitHub Repo URL>")
            return
        repo = parts[1]
        metadata = parse_repo(repo)
        store.new_project(repo, metadata)
        message = (
            "📢 New CLIF Job Run Request\n"
            f"- Project: {metadata.project_name}\n"
            f"- Repo: {repo}\n"
            f"- Description: {metadata.description}\n"
            f"- Tables Required: {', '.join(metadata.tables_required) if metadata.tables_required else 'N/A'}"
        )
        channel = os.environ.get("JOB_TRACKER_CHANNEL", "#clif-job-tracker")
        app.client.chat_postMessage(channel=channel, text=message, blocks=[
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": message},
            },
            {
                "type": "actions",
                "block_id": repo,
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "✅ Completed"},
                        "value": f"{repo}|✅",
                        "action_id": "status_update",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "🛠 In Progress"},
                        "value": f"{repo}|🛠",
                        "action_id": "status_update",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "❌ Will Not Participate"},
                        "value": f"{repo}|❌",
                        "action_id": "status_update",
                    },
                ],
            },
        ])
        respond("Project announcement posted to channel.")
    elif text.startswith("status"):
        respond(store.status_table())
    else:
        respond("Usage: /clif-run new <GitHub Repo URL> | /clif-run status")


@app.command("/clif-poc")
def handle_clif_poc(ack, respond, command):
    ack()
    text = command.get("text", "").strip()
    if not text:
        respond("Usage: /clif-poc <site name> @user")
        return
    try:
        site, user = text.rsplit(" ", 1)
        user_id = user.strip().lstrip("<@"").rstrip(">").split("|")[0]
        store.set_poc(site, user_id)
        respond(f"Point-of-contact for {site} set to <@{user_id}>")
    except ValueError:
        respond("Usage: /clif-poc <site name> @user")


@app.action("status_update")
def handle_status_update(ack, body, respond):
    ack()
    user_id = body["user"]["id"]
    site = store.get_site_for_user(user_id)
    if not site:
        respond("You are not registered as a POC. Use /clif-poc to register.")
        return
    value = body["actions"][0]["value"]
    repo, status = value.split("|")
    store.set_site_status(repo, site, status)
    respond(f"Status for {site} set to {status}")


def main() -> None:
    handler = SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN"))
    handler.start()


if __name__ == "__main__":
    main()
