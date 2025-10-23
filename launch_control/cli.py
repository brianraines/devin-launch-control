"""
CLI implementation for the devin launch control.
"""

from argparse import ArgumentParser
from .houston import MissionControl


def _build_parser():
    """
    Configure and return the argument parser used by the CLI.
    """

    # Step: configure argparse.
    parser = ArgumentParser(description="Generate Devin AI sessions.")

    parser.add_argument(
        "-s",
        "--stack",
        choices=["asg", "p2d", "cle"],
        required=True,
        help="The GitHub stack to launch the session for. (asg, p2d, cle)",
    )

    parser.add_argument(
        "-j",
        "--jira",
        required=False,
        help="The Jira ticket to launch the session for. (P2D-18, P2D-1816, P2D-1793)",
    )

    parser.add_argument(
        "-t",
        "--type",
        choices=["unit", "integration", "prompt"],
        default="unit",
        help="The type of session to launch. (unit, integration, prompt)",
    )

    parser.add_argument(
        "-tt",
        "--target-type",
        choices=["module", "class", "function", "scenario"],
        default="class",
        help="The target type to launch the session for, if the type is unit. (module, class, function)",
    )

    parser.add_argument(
        "-p",
        "--prompt",
        required=False,
        help="The prompt to send to Devin AI if the type is prompt.",
    )

    parser.add_argument(
        "-l",
        "--limit",
        default=5,
        required=False,
        help="The number of sessions to launch. (default: 5)",
    )

    parser.add_argument(
        "-d", "--debug", required=False, action="store_true", help="Enable debug mode."
    )

    return parser


def _validate_args(args):
    """
    Ensure the parsed arguments respect the documented bounds and relationships.
    """

    if args.type not in ["unit", "integration", "prompt"]:
        raise ValueError(
            "Invalid session type. Must be one of: unit, integration, prompt."
        )

    if args.type == "prompt" and not args.prompt:
        raise ValueError("Prompt is required when type is prompt.")

    if args.type == "integration":
        args.target_type = "scenario"
    elif args.type == "unit":
        unit_targets = {"module", "class", "function"}
        target_type = getattr(args, "target_type", "class")
        if target_type not in unit_targets:
            raise ValueError(
                "Target type must be one of module, class, or function for unit sessions."
            )

    if args.limit is not None:
        args.limit = int(args.limit)

    if args.stack == "asg":
        args.repo = "tii-assisted-grading-services"
        args.jira = "P2D-18"
    elif args.stack == "p2d":
        args.repo = "paper-to-digital-services"
        args.jira = "P2D-1816"
    elif args.stack == "cle":
        args.repo = "tii-checklist-editor-services"
        args.jira = "P2D-1793"
    else:
        raise ValueError(f"Invalid stack: {args.stack}")


def main():
    """
    Entry point: parse input, validate, load targets, and launch sessions.
    """

    # Step: parse input.
    parser = _build_parser()
    args = parser.parse_args()

    # Step: validate input.
    _validate_args(args)

    # Step: launch sessions.
    mc = MissionControl(args)
    mc.launch()
