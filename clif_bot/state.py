from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
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
    """Persistent store for project and point-of-contact information."""

    def __init__(self, data_file: str = "clif_bot_data.json") -> None:
        self.data_file = data_file
        self.projects: Dict[str, ProjectStatus] = {}
        self.pocs: Dict[str, str] = {}  # user_id -> site name
        self.poc_assignments: Dict[str, Dict[str, str]] = {}  # site -> {user_id: project}
        self.table_pocs: Dict[str, str] = {}  # table name -> user_id
        self.load_data()

    def load_data(self) -> None:
        """Load data from JSON file if it exists."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                
                # Load projects
                for repo_url, proj_data in data.get('projects', {}).items():
                    metadata = ProjectMetadata(
                        project_name=proj_data['metadata']['project_name'],
                        description=proj_data['metadata']['description'],
                        tables_required=proj_data['metadata']['tables_required']
                    )
                    self.projects[repo_url] = ProjectStatus(
                        metadata=metadata,
                        site_status=proj_data['site_status']
                    )
                
                # Load POCs
                self.pocs = data.get('pocs', {})
                self.poc_assignments = data.get('poc_assignments', {})
                self.table_pocs = data.get('table_pocs', {})
                
            except Exception as e:
                print(f"Error loading data: {e}")

    def save_data(self) -> None:
        """Save data to JSON file."""
        try:
            data = {
                'projects': {},
                'pocs': self.pocs,
                'poc_assignments': self.poc_assignments,
                'table_pocs': self.table_pocs,
            }
            
            # Convert projects to serializable format
            for repo_url, proj_status in self.projects.items():
                data['projects'][repo_url] = {
                    'metadata': asdict(proj_status.metadata),
                    'site_status': proj_status.site_status
                }
            
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Error saving data: {e}")

    # --- POC management -------------------------------------------------
    def set_poc(self, site: str, user_id: str, project: str = None) -> None:
        """Set a POC for a site, optionally for a specific project."""
        self.pocs[user_id] = site
        
        if site not in self.poc_assignments:
            self.poc_assignments[site] = {}
        
        if project:
            self.poc_assignments[site][user_id] = project
        else:
            self.poc_assignments[site][user_id] = "General"
        
        self.save_data()

    def get_site_for_user(self, user_id: str) -> str | None:
        return self.pocs.get(user_id)
    
    def get_poc_assignments(self, site: str = None) -> Dict[str, Dict[str, str]]:
        """Get POC assignments, optionally filtered by site."""
        if site:
            return {site: self.poc_assignments.get(site, {})}
        return self.poc_assignments
    
    def get_all_poc_mentions(self) -> str:
        """Get a string of all POC mentions for announcements."""
        if not self.pocs:
            return "Site POCs"
        # Group by site to handle multiple POCs per site
        site_pocs = {}
        for user_id, site in self.pocs.items():
            if site not in site_pocs:
                site_pocs[site] = []
            site_pocs[site].append(f"<@{user_id}>")
        
        mentions = []
        for site in SITES:
            if site in site_pocs:
                mentions.extend(site_pocs[site])
        
        if mentions:
            return " ".join(mentions)
        return "Site POCs"

    # --- Table POC management ------------------------------------------
    def set_table_poc(self, table: str, user_id: str) -> None:
        """Assign a POC to a specific CLIF table."""
        self.table_pocs[table] = user_id
        self.save_data()

    def get_table_poc(self, table: str) -> str | None:
        """Get the POC user_id for a given table."""
        return self.table_pocs.get(table)

    # --- Project tracking -----------------------------------------------
    def new_project(self, repo_url: str, metadata: ProjectMetadata) -> None:
        self.projects[repo_url] = ProjectStatus(metadata)
        self.save_data()

    def set_site_status(self, repo_url: str, site: str, status: str) -> None:
        self.projects[repo_url].site_status[site] = status
        self.save_data()

    def status_table(self) -> str:
        if not self.projects:
            return "No active projects."
        
        # Get project names and create shorter versions if needed
        projects = list(self.projects.values())
        project_names = []
        for proj in projects:
            name = proj.metadata.project_name
            # Truncate long project names for better table formatting
            if len(name) > 25:
                name = name[:22] + "..."
            project_names.append(name)
        
        # Calculate column widths
        site_width = max(len("Site"), max(len(site) for site in SITES))
        col_widths = [site_width] + [max(8, len(name)) for name in project_names]
        
        # Create header
        header_parts = ["Site".ljust(site_width)]
        for i, name in enumerate(project_names):
            header_parts.append(name.ljust(col_widths[i + 1]))
        
        lines = [" | ".join(header_parts)]
        lines.append("-" * (sum(col_widths) + 3 * (len(col_widths) - 1)))
        
        # Create rows
        for site in SITES:
            row_parts = [site.ljust(site_width)]
            for i, proj in enumerate(projects):
                status = proj.site_status.get(site, "❓")
                row_parts.append(status.center(col_widths[i + 1]))
            lines.append(" | ".join(row_parts))
        
        return "\n".join(lines)
