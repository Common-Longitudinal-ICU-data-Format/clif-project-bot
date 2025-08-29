"""Slack Bolt application for coordinating CLIF project runs."""
from __future__ import annotations

import os
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import requests

from clif_bot.metadata import parse_repo
from clif_bot.state import StatusStore
from clif_bot import mcide

load_dotenv()


app = App(token=os.environ.get("SLACK_BOT_TOKEN"), signing_secret=os.environ.get("SLACK_SIGNING_SECRET"))
store = StatusStore()


@app.command("/clif-run")
def handle_clif_run(ack, respond, command, client):
    ack()
    
    # Open modal for project details (no URL parameter needed)
    modal_view = {
        "type": "modal",
        "callback_id": "clif_project_modal",
        "title": {"type": "plain_text", "text": "CLIF Project Release"},
        "submit": {"type": "plain_text", "text": "Release Project"},
        "close": {"type": "plain_text", "text": "Cancel"},
        "blocks": [
            {
                "type": "input",
                "block_id": "github_url_block",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "github_url",
                    "placeholder": {"type": "plain_text", "text": "https://github.com/Common-Longitudinal-ICU-data-Format/project-name"}
                },
                "label": {"type": "plain_text", "text": "GitHub Repository URL"}
            },
            {
                "type": "input",
                "block_id": "project_name_block",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "project_name",
                    "placeholder": {"type": "plain_text", "text": "Enter project name"}
                },
                "label": {"type": "plain_text", "text": "Project Name"}
            },
            {
                "type": "input",
                "block_id": "result_box_block",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "result_box_link",
                    "placeholder": {"type": "plain_text", "text": "Enter result box link"}
                },
                "label": {"type": "plain_text", "text": "Result Box Link"}
            },
            {
                "type": "input",
                "block_id": "special_instructions_block",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "special_instructions",
                    "multiline": True,
                    "placeholder": {"type": "plain_text", "text": "Enter any special instructions"}
                },
                "label": {"type": "plain_text", "text": "Special Instructions"},
                "optional": True
            }
        ]
    }
    
    try:
        client.views_open(trigger_id=command["trigger_id"], view=modal_view)
    except Exception as e:
        respond(f"Error opening modal: {str(e)}")

@app.command("/mCIDE")
def handle_mcide(ack, respond, command, client):
    """Open modal for adding a new mCIDE category level."""
    ack()
    try:
        tables = mcide.fetch_tables()
        if not tables:
            respond("No tables available.")
            return
        table_options = [
            {"text": {"type": "plain_text", "text": t}, "value": t}
            for t in tables
        ]
        table = tables[0]
        variables = mcide.fetch_variables(table)
        variable_options = [
            {"text": {"type": "plain_text", "text": v}, "value": v}
            for v in variables
        ]
        variable = variables[0] if variables else ""
        values = mcide.fetch_category_values(table, variable) if variable else []

        modal_view = {
            "type": "modal",
            "callback_id": "mcide_modal",
            "title": {"type": "plain_text", "text": "mCIDE"},
            "submit": {"type": "plain_text", "text": "Submit"},
            "close": {"type": "plain_text", "text": "Cancel"},
            "blocks": [
                {
                    "type": "input",
                    "block_id": "table_block",
                    "element": {
                        "type": "static_select",
                        "action_id": "mcide_table_select",
                        "options": table_options,
                        "initial_option": {
                            "text": {"type": "plain_text", "text": table},
                            "value": table,
                        },
                    },
                    "label": {"type": "plain_text", "text": "CLIF Table"},
                },
                {
                    "type": "input",
                    "block_id": "variable_block",
                    "element": {
                        "type": "static_select",
                        "action_id": "mcide_variable_select",
                        "options": variable_options,
                        "initial_option": {
                            "text": {"type": "plain_text", "text": variable},
                            "value": variable,
                        } if variable else None,
                    },
                    "label": {"type": "plain_text", "text": "Category Variable"},
                    "optional": False,
                },
                {
                    "type": "section",
                    "block_id": "values_block",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Existing values:* " + ", ".join(values) if values else "*Existing values:*",
                    },
                },
                {
                    "type": "input",
                    "block_id": "new_value_block",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "new_value",
                    },
                    "label": {"type": "plain_text", "text": "New Value"},
                },
            ],
        }

        client.views_open(trigger_id=command["trigger_id"], view=modal_view)
    except Exception as e:
        respond(f"Error opening modal: {e}")


@app.action("mcide_table_select")
def mcide_table_changed(ack, body, client):
    ack()
    table = body["actions"][0]["selected_option"]["value"]
    variables = mcide.fetch_variables(table)
    variable_options = [
        {"text": {"type": "plain_text", "text": v}, "value": v}
        for v in variables
    ]
    variable = variables[0] if variables else ""
    values = mcide.fetch_category_values(table, variable) if variable else []

    view = body["view"]
    view["blocks"][1]["element"]["options"] = variable_options
    if variable:
        view["blocks"][1]["element"]["initial_option"] = {
            "text": {"type": "plain_text", "text": variable},
            "value": variable,
        }
    view["blocks"][2]["text"]["text"] = (
        "*Existing values:* " + ", ".join(values) if values else "*Existing values:*"
    )
    client.views_update(
        view_id=body["view"]["id"], hash=body["view"]["hash"], view=view
    )


@app.action("mcide_variable_select")
def mcide_variable_changed(ack, body, client):
    ack()
    table = body["view"]["state"]["values"]["table_block"]["mcide_table_select"]["selected_option"]["value"]
    variable = body["actions"][0]["selected_option"]["value"]
    values = mcide.fetch_category_values(table, variable)
    view = body["view"]
    view["blocks"][2]["text"]["text"] = (
        "*Existing values:* " + ", ".join(values) if values else "*Existing values:*"
    )
    client.views_update(
        view_id=body["view"]["id"], hash=body["view"]["hash"], view=view
    )


@app.view("mcide_modal")
def handle_mcide_submission(ack, body, client):
    ack()
    state = body["view"]["state"]["values"]
    table = state["table_block"]["mcide_table_select"]["selected_option"]["value"]
    variable = state["variable_block"]["mcide_variable_select"]["selected_option"]["value"]
    new_value = state["new_value_block"]["new_value"]["value"]
    user_id = body["user"]["id"]
    try:
        pr_url = mcide.update_category_csv(table, variable, new_value)
        client.chat_postMessage(channel=user_id, text=f"Created PR: {pr_url}")
    except Exception as e:
        client.chat_postMessage(channel=user_id, text=f"Error updating categories: {e}")
=======
@app.view("clif_issue_modal")
def handle_issue_submission(ack, body, client):
    ack()

    user_id = body["user"]["id"]
    values = body["view"]["state"]["values"]
    title = values["title_block"]["title_input"]["value"]
    description = (
        values["description_block"]["description_input"].get("value") or ""
    )

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        client.chat_postMessage(channel=user_id, text="GITHUB_TOKEN is not set.")
        return

    url = (
        "https://api.github.com/repos/Common-Longitudinal-ICU-data-Format/CLIF/issues"
    )
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    payload = {"title": title, "body": description}

    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 201:
            issue_url = response.json().get("html_url")
            client.chat_postMessage(channel=user_id, text=f"Issue created: {issue_url}")
        else:
            client.chat_postMessage(
                channel=user_id,
                text=f"Failed to create issue: {response.text}",
            )
    except Exception as e:
        client.chat_postMessage(channel=user_id, text=f"Error creating issue: {e}")


@app.command("/clif-issues")
def handle_clif_issues(ack, respond, command, client):
    ack()

    modal_view = {
        "type": "modal",
        "callback_id": "clif_issue_modal",
        "title": {"type": "plain_text", "text": "New CLIF Issue"},
        "submit": {"type": "plain_text", "text": "Create Issue"},
        "close": {"type": "plain_text", "text": "Cancel"},
        "blocks": [
            {
                "type": "input",
                "block_id": "title_block",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "title_input",
                    "placeholder": {"type": "plain_text", "text": "Enter issue title"},
                },
                "label": {"type": "plain_text", "text": "Title"},
            },
            {
                "type": "input",
                "block_id": "description_block",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "description_input",
                    "multiline": True,
                    "placeholder": {"type": "plain_text", "text": "Describe the issue"},
                },
                "label": {"type": "plain_text", "text": "Description"},
                "optional": True,
            },
        ],
    }

    try:
        client.views_open(trigger_id=command["trigger_id"], view=modal_view)
    except Exception as e:
        respond(f"Error opening modal: {str(e)}")


@app.command("/clif-status")
def handle_clif_status(ack, respond, command):
    ack()
    status_table = store.status_table()
    if status_table == "No active projects.":
        respond(status_table)
        return
    
    # Post the status table to the channel as a public message
    channel = os.environ.get("JOB_TRACKER_CHANNEL", "#project-tracker")
    try:
        app.client.chat_postMessage(
            channel=channel, 
            text=f"📊 CLIF Project Status Dashboard\n```\n{status_table}\n```"
        )
        respond("Status dashboard posted to channel.")
    except Exception as e:
        # Fallback to private response if channel posting fails
        respond(f"```\n{status_table}\n```")


@app.command("/clif-site-poc")
def handle_clif_site_poc(ack, respond, command, client):
    ack()
    
    # Create site options for dropdown
    site_options = []
    for site in ["University of Chicago", "Emory University", "John Hopkins University", 
                 "Northwestern University", "Oregon Health & Science University", "Rush University",
                 "University of California San Francisco", "University of Michigan", 
                 "University of Minnesota", "University of Pennsylvania", "University of Toronto", "MIMIC-IV"]:
        site_options.append({
            "text": {"type": "plain_text", "text": site},
            "value": site
        })
    
    # Create project options from active projects
    project_options = [
        {
            "text": {"type": "plain_text", "text": "General (all projects)"},
            "value": "General"
        }
    ]
    
    # Add active projects to dropdown
    for repo_url, project_status in store.projects.items():
        project_name = project_status.metadata.project_name
        # Truncate long project names for dropdown
        display_name = project_name[:50] + "..." if len(project_name) > 50 else project_name
        project_options.append({
            "text": {"type": "plain_text", "text": display_name},
            "value": project_name
        })
    
    # Open modal for POC assignment
    modal_view = {
        "type": "modal",
        "callback_id": "clif_site_poc_modal",
        "title": {"type": "plain_text", "text": "Assign Site POC"},
        "submit": {"type": "plain_text", "text": "Assign POC"},
        "close": {"type": "plain_text", "text": "Cancel"},
        "blocks": [
            {
                "type": "input",
                "block_id": "site_block",
                "element": {
                    "type": "static_select",
                    "placeholder": {"type": "plain_text", "text": "Select a CLIF site"},
                    "options": site_options,
                    "action_id": "site_select"
                },
                "label": {"type": "plain_text", "text": "CLIF Site"}
            },
            {
                "type": "input",
                "block_id": "user_block",
                "element": {
                    "type": "users_select",
                    "placeholder": {"type": "plain_text", "text": "Select a user"},
                    "action_id": "user_select"
                },
                "label": {"type": "plain_text", "text": "Point of Contact"}
            },
            {
                "type": "input",
                "block_id": "project_block",
                "element": {
                    "type": "static_select",
                    "placeholder": {"type": "plain_text", "text": "Select a project"},
                    "options": project_options,
                    "action_id": "project_select"
                },
                "label": {"type": "plain_text", "text": "Project"},
                "optional": True
            }
        ]
    }
    
    try:
        client.views_open(trigger_id=command["trigger_id"], view=modal_view)
    except Exception as e:
        respond(f"Error opening modal: {str(e)}")


@app.command("/clif-table-poc")
def handle_clif_table_poc(ack, respond, command, client):
    ack()
    try:
        tables = mcide.fetch_tables()
        if not tables:
            respond("No tables available.")
            return
        table_options = [
            {"text": {"type": "plain_text", "text": t}, "value": t} for t in tables
        ]
        table = tables[0]
        poc_user = store.get_table_poc(table)
        poc_text = (
            f"*Current POC:* <@{poc_user}>" if poc_user else "*Current POC:* _Unassigned_"
        )
        modal_view = {
            "type": "modal",
            "callback_id": "clif_table_poc_modal",
            "title": {"type": "plain_text", "text": "Table POC"},
            "submit": {"type": "plain_text", "text": "Send"},
            "close": {"type": "plain_text", "text": "Cancel"},
            "blocks": [
                {
                    "type": "input",
                    "block_id": "table_block",
                    "element": {
                        "type": "static_select",
                        "action_id": "table_poc_table_select",
                        "options": table_options,
                        "initial_option": {
                            "text": {"type": "plain_text", "text": table},
                            "value": table,
                        },
                    },
                    "label": {"type": "plain_text", "text": "CLIF Table"},
                },
                {
                    "type": "section",
                    "block_id": "poc_block",
                    "text": {"type": "mrkdwn", "text": poc_text},
                },
                {
                    "type": "input",
                    "block_id": "question_block",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "question_input",
                        "multiline": True,
                    },
                    "label": {"type": "plain_text", "text": "Question"},
                },
                {
                    "type": "input",
                    "block_id": "claim_block",
                    "optional": True,
                    "element": {
                        "type": "checkboxes",
                        "action_id": "claim_checkbox",
                        "options": [
                            {
                                "text": {"type": "plain_text", "text": "Claim POC if unassigned"},
                                "value": "claim",
                            }
                        ],
                    },
                    "label": {"type": "plain_text", "text": "POC Ownership"},
                },
            ],
        }
        client.views_open(trigger_id=command["trigger_id"], view=modal_view)
    except Exception as e:
        respond(f"Error opening modal: {e}")


@app.command("/clif-help")
def handle_clif_help(ack, command, client, respond):
    """Open a modal for users to request CLIF assistance."""
    ack()

    modal_view = {
        "type": "modal",
        "callback_id": "clif_help_modal",
        "title": {"type": "plain_text", "text": "Request CLIF Help"},
        "submit": {"type": "plain_text", "text": "Submit Ticket"},
        "close": {"type": "plain_text", "text": "Cancel"},
        "blocks": [
            {
                "type": "input",
                "block_id": "summary_block",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "summary_input",
                    "placeholder": {"type": "plain_text", "text": "Brief summary"},
                },
                "label": {"type": "plain_text", "text": "Summary"},
            },
            {
                "type": "input",
                "block_id": "details_block",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "details_input",
                    "multiline": True,
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Describe your issue or question",
                    },
                },
                "label": {"type": "plain_text", "text": "Details"},
            },
        ],
    }

    try:
        client.views_open(trigger_id=command["trigger_id"], view=modal_view)
    except Exception as e:
        respond(f"Error opening modal: {str(e)}")


@app.view("clif_project_modal")
def handle_modal_submission(ack, body, client):
    ack()
    
    # Extract form data
    user_id = body["user"]["id"]
    values = body["view"]["state"]["values"]
    
    repo = values["github_url_block"]["github_url"]["value"]
    project_name = values["project_name_block"]["project_name"]["value"]
    result_box_link = values["result_box_block"]["result_box_link"]["value"]
    special_instructions = values["special_instructions_block"]["special_instructions"]["value"] or "None"
    
    # Parse the GitHub repo for metadata
    metadata = parse_repo(repo)
    store.new_project(repo, metadata)
    
    # Get user info to mention them
    try:
        user_info = client.users_info(user=user_id)
        user_name = user_info["user"]["real_name"] or user_info["user"]["name"]
        user_mention = f"<@{user_id}>"
    except:
        user_mention = f"<@{user_id}>"
        user_name = "User"
    
    # Create announcement message for #general
    tables_list = ", ".join(metadata.tables_required) if metadata.tables_required else "None specified"
    poc_mentions = store.get_all_poc_mentions()
    
    announcement = (
        f"🚀 **New CLIF Project Release** 🚀\n\n"
        f"{user_mention} has released code for **{project_name}**!\n\n"
        f"📊 **Tables required:** {tables_list}\n"
        f"📋 **Result Box:** {result_box_link}\n"
        f"🔧 **Special Instructions:** {special_instructions}\n\n"
        f"🔗 **Repository:** {repo}\n\n"
        f"**{poc_mentions}:** Please clone the repository and begin your analysis!"
    )
    
    # Post to #general channel
    try:
        result = client.chat_postMessage(
            channel="#general",
            text=announcement,
            blocks=[
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": announcement}
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
                }
            ]
        )
        print(f"Successfully posted to #general: {result.get('ok', False)}")
        
        # Also post to project tracker for internal tracking
        tracker_message = (
            f"📢 New CLIF Job Run Request\n"
            f"- Project: {project_name}\n"
            f"- Repo: {repo}\n"
            f"- Description: {metadata.description}\n"
            f"- Tables Required: {tables_list}\n"
            f"- Result Box: {result_box_link}\n"
            f"- Special Instructions: {special_instructions}"
        )
        
        channel = os.environ.get("JOB_TRACKER_CHANNEL", "#project-tracker")
        client.chat_postMessage(
            channel=channel,
            text=tracker_message,
            blocks=[
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": tracker_message}
                }
            ]
        )

    except Exception as e:
        print(f"Error posting announcement: {e}")


@app.view("clif_site_poc_modal")
def handle_site_poc_modal_submission(ack, body, client):
    ack()
    
    # Extract form data
    values = body["view"]["state"]["values"]
    
    site = values["site_block"]["site_select"]["selected_option"]["value"]
    user_id = values["user_block"]["user_select"]["selected_user"]
    
    # Handle project selection from dropdown (optional field)
    project = None
    if "project_block" in values and values["project_block"]["project_select"]["selected_option"]:
        project = values["project_block"]["project_select"]["selected_option"]["value"]
        if project == "General":
            project = None  # Treat "General" as no specific project
    
    # Set the POC assignment
    store.set_poc(site, user_id, project)
    
    # Get user info for confirmation
    try:
        user_info = client.users_info(user=user_id)
        user_name = user_info["user"]["real_name"] or user_info["user"]["name"]
    except:
        user_name = f"<@{user_id}>"
    
    # Send confirmation message
    project_text = f" for project '{project}'" if project else " (General)"
    confirmation_message = f"✅ {user_name} has been assigned as POC for {site}{project_text}"
    
    # Post confirmation to the channel
    try:
        channel = os.environ.get("JOB_TRACKER_CHANNEL", "#project-tracker")
        client.chat_postMessage(
            channel=channel,
            text=confirmation_message
        )
    except Exception as e:
        print(f"Error posting POC confirmation: {e}")


@app.action("table_poc_table_select")
def table_poc_table_changed(ack, body, client):
    ack()
    table = body["actions"][0]["selected_option"]["value"]
    poc_user = store.get_table_poc(table)
    poc_text = (
        f"*Current POC:* <@{poc_user}>" if poc_user else "*Current POC:* _Unassigned_"
    )
    view = body["view"]
    for block in view["blocks"]:
        if block.get("block_id") == "poc_block":
            block["text"]["text"] = poc_text
    client.views_update(view_id=body["view"]["id"], hash=body["view"]["hash"], view=view)


@app.view("clif_table_poc_modal")
def handle_table_poc_modal_submission(ack, body, client):
    ack()
    state = body["view"]["state"]["values"]
    table = state["table_block"]["table_poc_table_select"]["selected_option"]["value"]
    question = state["question_block"]["question_input"]["value"]
    claim_selected = bool(
        state.get("claim_block", {})
        .get("claim_checkbox", {})
        .get("selected_options")
    )
    user_id = body["user"]["id"]
    poc_user = store.get_table_poc(table)
    if not poc_user and claim_selected:
        store.set_table_poc(table, user_id)
        poc_user = user_id
        claim_msg = "You are now the POC for this table. "
    else:
        claim_msg = ""
    if poc_user:
        client.chat_postMessage(
            channel=poc_user,
            text=f"📥 Question about *{table}* from <@{user_id}>:\n{question}",
        )
        client.chat_postMessage(
            channel=user_id,
            text=f"{claim_msg}Your question has been sent to <@{poc_user}>.",
        )
    else:
        client.chat_postMessage(
            channel=user_id,
            text="No POC is assigned to this table.",
        )


@app.view("clif_help_modal")
def handle_help_modal_submission(ack, body, client):
    """Post submitted help requests to a dedicated channel."""
    ack()

    user_id = body["user"]["id"]
    values = body["view"]["state"]["values"]
    summary = values["summary_block"]["summary_input"]["value"]
    details = values["details_block"]["details_input"]["value"]

    channel = os.environ.get("HELP_CHANNEL", "#clif-help")
    message = (
        f"🆘 *CLIF Help Ticket*\n"
        f"*Submitted by:* <@{user_id}>\n"
        f"*Summary:* {summary}\n"
        f"*Details:* {details}"
    )

    try:
        client.chat_postMessage(channel=channel, text=message)
    except Exception as e:
        print(f"Error posting help ticket: {e}")


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
