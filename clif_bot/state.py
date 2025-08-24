from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .metadata import ProjectMetadata

SITES = [
    "University of Chicago",
    "Emory University",
    "John Hopkins University",
    "Northwestern University",
    "Oregon Health & Science University",
    "Rush University",
    "University of California San Francisco",
    "University of Michigan",
    "University of Minnesota",
    "University of Pennsylvania",
    "University of Toronto",
    "MIMIC-IV",
]


@dataclass
class ProjectStatus:
    metadata: ProjectMetadata
    site_status: Dict[str, str] = field(
        default_factory=lambda: {site: "❓" for site in SITES}
    )


class StatusStore:
    """In-memory store for project and point-of-contact information."""

    def __init__(self) -> None:
        self.projects: Dict[str, ProjectStatus] = {}
        self.pocs: Dict[str, str] = {}  # user_id -> site name

    # --- POC management -------------------------------------------------
    def set_poc(self, site: str, user_id: str) -> None:
        self.pocs[user_id] = site

    def get_site_for_user(self, user_id: str) -> str | None:
        return self.pocs.get(user_id)

    # --- Project tracking -----------------------------------------------
    def new_project(self, repo_url: str, metadata: ProjectMetadata) -> None:
        self.projects[repo_url] = ProjectStatus(metadata)

    def set_site_status(self, repo_url: str, site: str, status: str) -> None:
        self.projects[repo_url].site_status[site] = status

    def status_table(self) -> str:
        if not self.projects:
            return "No active projects."
        headers = ["Site"] + [p.metadata.project_name for p in self.projects.values()]
        rows: List[List[str]] = []
        for site in SITES:
            row = [site]
            for proj in self.projects.values():
                row.append(proj.site_status.get(site, "❓"))
            rows.append(row)
        # Simple tab-separated table
        lines = ["\t".join(headers)]
        for row in rows:
            lines.append("\t".join(row))
        return "\n".join(lines)
