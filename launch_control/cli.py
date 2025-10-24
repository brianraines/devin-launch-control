"""
CLI implementation for the devin launch control.
"""

from argparse import ArgumentParser, Namespace

from .config import STACK_CONFIG
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

    parser.add_argument("-j", "--jira", help="Jira ticket to associate with launch.")

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
        type=int,
        default=5,
        required=False,
        help="The number of sessions to launch. (default: 5)",
    )

    parser.add_argument(
        "-d", "--debug", required=False, action="store_true", help="Enable debug mode."
    )

    return parser


def _validate_args(args: Namespace) -> None:
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

    try:
        stack_config = STACK_CONFIG[args.stack]
    except KeyError as exc:  # pragma: no cover - guarded by argparse
        raise ValueError(f"Invalid stack: {args.stack}") from exc

    args.repo = stack_config["repo"]
    if not args.jira:
        args.jira = stack_config["default_jira"]


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
