from __future__ import annotations

from dataclasses import dataclass
from typing import List
import re
import requests
import yaml


@dataclass
class ProjectMetadata:
    """Structured metadata about a CLIF project."""

    project_name: str
    description: str
    tables_required: List[str]


def _github_raw_url(repo_url: str, path: str) -> str:
    owner_repo = repo_url.rstrip("/").split("github.com/")[1]
    return f"https://raw.githubusercontent.com/{owner_repo}/main/{path}"


def parse_repo(repo_url: str) -> ProjectMetadata:
    """Fetch and parse project metadata from a GitHub repository.

    The function first attempts to read a ``project.yaml`` or ``metadata.json``
    file from the repository.  If neither exist, it falls back to parsing the
    ``README.md`` for a title, a one-line description, and a simple
    ``tables required`` list.
    """

    # Try structured metadata files first
    for path in ("project.yaml", "metadata.json"):
        url = _github_raw_url(repo_url, path)
        response = requests.get(url)
        if response.status_code == 200:
            if path.endswith(".yaml"):
                data = yaml.safe_load(response.text)
            else:
                data = response.json()
            project_name = data.get("project_name") or data.get("name") or ""
            description = data.get("description", "")
            tables = data.get("tables_required", [])
            return ProjectMetadata(project_name, description, tables)

    # Fall back to README parsing
    url = _github_raw_url(repo_url, "README.md")
    response = requests.get(url)
    project_name = ""
    description = ""
    tables_required: List[str] = []
    if response.status_code == 200:
        lines = response.text.splitlines()
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if not project_name:
                project_name = re.sub(r"^#*\s*", "", stripped)
                continue
            if not description:
                description = stripped
            match = re.search(r"tables? required[:\-]?\s*(.*)", stripped, re.I)
            if match:
                tables_required = [t.strip() for t in re.split(r"[,;]", match.group(1)) if t.strip()]
        if not project_name:
            project_name = repo_url.rstrip("/").split("/")[-1]
    return ProjectMetadata(project_name, description, tables_required)
