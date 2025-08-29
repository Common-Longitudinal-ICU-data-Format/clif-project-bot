from __future__ import annotations

import base64
import os
from typing import List

import requests

MCIDE_BASE = "https://api.github.com/repos/Common-Longitudinal-ICU-data-Format/CLIF/contents/mCIDE"
RAW_BASE = "https://raw.githubusercontent.com/Common-Longitudinal-ICU-data-Format/CLIF/main/mCIDE"
REPO = "Common-Longitudinal-ICU-data-Format/CLIF"

def fetch_tables() -> List[str]:
    """Return the list of CLIF tables available in mCIDE."""
    response = requests.get(MCIDE_BASE)
    response.raise_for_status()
    data = response.json()
    return [item["name"] for item in data if item["type"] == "dir" and not item["name"].startswith("00_")]

def fetch_variables(table: str) -> List[str]:
    """Return the list of *_category variables for a given table."""
    response = requests.get(f"{MCIDE_BASE}/{table}")
    response.raise_for_status()
    variables = []
    for item in response.json():
        name = item["name"]
        if name.endswith("_categories.csv"):
            # file name pattern: clif_{table}_{var}_categories.csv
            var = name.removeprefix(f"clif_{table}_").removesuffix("_categories.csv")
            variables.append(var)
    return variables

def fetch_category_values(table: str, variable: str) -> List[str]:
    """Return permissible values for a variable from its CSV."""
    url = f"{RAW_BASE}/{table}/clif_{table}_{variable}_categories.csv"
    response = requests.get(url)
    if response.status_code != 200:
        return []
    return [line.strip() for line in response.text.splitlines() if line.strip()]

def update_category_csv(table: str, variable: str, new_value: str) -> str:
    """Append a new value to the variable's CSV and create a pull request.

    Returns the URL of the created pull request.
    """
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN not set")
    path = f"mCIDE/{table}/clif_{table}_{variable}_categories.csv"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}

    # Get current file content
    file_resp = requests.get(f"https://api.github.com/repos/{REPO}/contents/{path}", headers=headers)
    file_resp.raise_for_status()
    file_data = file_resp.json()
    content = base64.b64decode(file_data["content"]).decode("utf-8")
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    if new_value in lines:
        raise ValueError("Value already exists")
    lines.append(new_value)
    updated = "\n".join(lines) + "\n"
    encoded = base64.b64encode(updated.encode()).decode()

    # Create branch
    main_ref = requests.get(f"https://api.github.com/repos/{REPO}/git/ref/heads/main", headers=headers)
    main_ref.raise_for_status()
    sha = main_ref.json()["object"]["sha"]
    branch_name = f"mcide-{table}-{variable}-{new_value}".replace(" ", "-")
    requests.post(
        f"https://api.github.com/repos/{REPO}/git/refs",
        headers=headers,
        json={"ref": f"refs/heads/{branch_name}", "sha": sha},
    ).raise_for_status()

    # Update file on new branch
    requests.put(
        f"https://api.github.com/repos/{REPO}/contents/{path}",
        headers=headers,
        json={
            "message": f"Add {new_value} to {variable}",
            "content": encoded,
            "branch": branch_name,
            "sha": file_data["sha"],
        },
    ).raise_for_status()

    # Create pull request
    pr_resp = requests.post(
        f"https://api.github.com/repos/{REPO}/pulls",
        headers=headers,
        json={
            "title": f"Add {new_value} to {table}.{variable}",
            "head": branch_name,
            "base": "main",
        },
    )
    pr_resp.raise_for_status()
    return pr_resp.json().get("html_url", "")
