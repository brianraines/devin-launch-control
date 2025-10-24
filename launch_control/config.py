"""
Shared configuration constants for the launch control package.
"""

from typing import Dict

STACK_CONFIG: Dict[str, Dict[str, str]] = {
    "asg": {"repo": "tii-assisted-grading-services", "default_jira": "P2D-18"},
    "p2d": {"repo": "paper-to-digital-services", "default_jira": "P2D-1816"},
    "cle": {"repo": "tii-checklist-editor-services", "default_jira": "P2D-1793"},
}
