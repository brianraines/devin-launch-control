"""
Houston is the core Mission Control of the devin launch control system.
"""

import json
from pathlib import Path
from typing import Iterable, List, Mapping, Optional, Tuple

from .api import DevinAPI
from .config import STACK_CONFIG
from .rocket_fuel import RocketFuel


class MissionControl:
    """
    Houston is the core Mission Control of the devin launch control system.
    """

    def __init__(self, args):
        self.args = args

        provided_repo = getattr(args, "repo", None)
        if provided_repo:
            self.repo = provided_repo
            return

        stack = getattr(args, "stack", None)
        if stack not in STACK_CONFIG:
            raise ValueError(f"Invalid stack: {stack}")

        self.repo = STACK_CONFIG[stack]["repo"]
        setattr(self.args, "repo", self.repo)

    def debug(self, message: str):
        """
        Emit debug output when the debug flag is enabled.
        """

        if getattr(self.args, "debug", False):
            print(message)

    def launch(self):
        """
        Go for launch! 🚀🚀🚀
        """

        # What args are we working with?
        self.debug(f"Args: {self.args}")

        # Get the targets for the session
        print("Getting targets...")
        targets = self.get_targets()
        if targets:
            self.debug("Targets:")
            self.debug(json.dumps(targets, indent=2))
        else:
            self.debug("Targets: []")

        # Build prompts from the targets
        print("Building prompts...")
        prompts = self.build_prompts(targets)
        if prompts:
            self.debug("Prompts:")
            self.debug(json.dumps(prompts, indent=2))
        else:
            self.debug("Prompts: []")

        self.launch_prompts(prompts)

        print("Houston, we have liftoff! 🚀🚀🚀")

    def get_targets(self):
        """
        Get the targets for the session.
        """

        if self.args.type != "prompt":
            target_path = (
                Path(__file__).resolve().parent.parent
                / "targets"
                / self.args.target_type.lower()
                / f"{self.args.stack.lower()}.json"
            )
            if not target_path.exists():
                raise FileNotFoundError(
                    f"Target configuration not found at {target_path}"
                )
            return json.loads(target_path.read_text(encoding="utf-8"))

        return []

    def build_prompts(self, targets: Iterable[Mapping]) -> List[str]:
        """
        Build prompts from the targets.
        """

        fuel = RocketFuel(self.args, self.repo)
        return fuel.build_prompts(targets)

    def launch_prompts(self, prompts: List[str]):
        """
        Launch the prompts.
        """

        api = DevinAPI()

        for entry in prompts:
            prompt_data = self._load_prompt(entry)
            if prompt_data is None:
                continue

            prompt_text, source = prompt_data
            print(f"Launching prompt: {source}")

            response = api.post_prompt(prompt_text)
            print(f"Response: {response.status_code} {response.text}")

    def _load_prompt(self, entry: str) -> Optional[Tuple[str, str]]:
        """
        Load prompt content from either inline text or a file path.
        Returns a tuple of the prompt text and a human-readable source label.
        """

        is_inline_prompt = getattr(self.args, "type", None) == "prompt"

        if is_inline_prompt:
            if not entry.strip():
                print("Prompt content empty, skipping launch.")
                return None
            return entry, "inline prompt"

        base_dir = Path(__file__).resolve().parent.parent
        prompt_path = Path(entry)
        if not prompt_path.is_absolute():
            prompt_path = base_dir / prompt_path

        if not prompt_path.exists():
            print(f"Prompt file missing: {prompt_path}, skipping launch.")
            return None

        prompt_text = prompt_path.read_text(encoding="utf-8")
        if not prompt_text.strip():
            print(f"Prompt file empty: {prompt_path}, skipping launch.")
            return None

        return prompt_text, str(prompt_path)
