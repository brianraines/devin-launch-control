"""
Rocket fuel handles mixing the prompt payloads before launch.
"""

from pathlib import Path
from typing import Iterable, List, Mapping, Optional


class RocketFuel:
    """
    Prepare prompts for the launch sequence.
    """

    def __init__(self, args, repo: str):
        self.args = args
        self.repo = repo
        self.project_root = Path(__file__).resolve().parent.parent
        self.launch_pad_dir = self.project_root / "prompts" / "launch_pad"
        self.limit = self._parse_limit(getattr(args, "limit", None))
        self._prepare_launch_pad()

    @staticmethod
    def _parse_limit(raw_limit) -> Optional[int]:
        if raw_limit is None:
            return None

        try:
            limit = int(raw_limit)
        except (TypeError, ValueError) as exc:  # pragma: no cover - defensive
            raise ValueError("The limit must be an integer.") from exc

        if limit < 0:
            raise ValueError("The limit must be zero or greater.")

        return limit

    def _prepare_launch_pad(self) -> None:
        """
        Ensure the launch pad directory exists and does not contain stale prompts.
        """

        self.launch_pad_dir.mkdir(parents=True, exist_ok=True)
        for stale_prompt in self.launch_pad_dir.glob("prompt_*.txt"):
            stale_prompt.unlink()

    def build_prompts(self, targets: Iterable[Mapping]) -> List[str]:
        """
        Build prompts from the provided targets and command arguments.
        """

        if self.limit == 0:
            return []

        if self.args.type == "prompt":
            template = (self.project_root / "prompts" / "custom.txt").read_text(
                encoding="utf-8"
            )
            prompt = template.format(
                REPO=self.repo,
                OBJECTIVE=self.args.prompt,
                JIRA_TICKET=self.args.jira,
            )
            return [prompt]

        template = (self.project_root / "prompts" / "playbook.txt").read_text(
            encoding="utf-8"
        )

        base_context = {
            "REPO": self.repo,
            "JIRA_TICKET": self.args.jira,
        }

        prompts: List[str] = []

        def build_injections(parts: Iterable[str]) -> str:
            filtered = [part for part in parts if part != ""]
            lines: List[str] = []

            for index in range(0, len(filtered), 2):
                key = filtered[index]
                value = filtered[index + 1] if index + 1 < len(filtered) else ""
                lines.append(key)
                if value:
                    lines.append(value)
                if index + 2 < len(filtered):
                    lines.append("")

            return "\n".join(lines)

        target_type = getattr(self.args, "target_type", None)

        def should_stop() -> bool:
            return self.limit is not None and len(prompts) >= self.limit

        for target in targets:
            if should_stop():
                break

            module_name = target.get("module")
            if not module_name:
                raise ValueError("Unit targets require a 'module' entry.")

            if target_type == "module":
                context = {
                    **base_context,
                    "PLAYBOOK": "!moduleunittest",
                    "OBJECTIVE": f"Add unit tests for the module {module_name}",
                    "INJECTIONS": build_injections(["Module", module_name]),
                }
                prompts.append(template.format(**context))

            elif target_type == "class":
                for class_name in target.get("classes", []):
                    if should_stop():
                        break
                    context = {
                        **base_context,
                        "PLAYBOOK": "!classunittest",
                        "OBJECTIVE": f"Add unit tests for the class {class_name}",
                        "INJECTIONS": build_injections(
                            ["Module", module_name, "", "Class", class_name]
                        ),
                    }
                    prompts.append(template.format(**context))

            elif target_type == "function":
                class_name = target.get("class")
                if not class_name:
                    raise ValueError("Function targets require a 'class' entry.")

                for function_name in target.get("functions", []):
                    if should_stop():
                        break
                    context = {
                        **base_context,
                        "PLAYBOOK": "!methodunittest",
                        "OBJECTIVE": f"Add unit tests for the function {function_name}",
                        "INJECTIONS": build_injections(
                            [
                                "Module",
                                module_name,
                                "",
                                "Class",
                                class_name,
                                "",
                                "Method",
                                function_name,
                            ]
                        ),
                    }
                    prompts.append(template.format(**context))

            elif target_type == "scenario":
                for scenario in target.get("scenarios", []):
                    if should_stop():
                        break
                    context = {
                        **base_context,
                        "PLAYBOOK": "!integrationtest",
                        "OBJECTIVE": f"Execute integration scenario {scenario}",
                        "INJECTIONS": build_injections(
                            ["Module", module_name, "", "Scenario", str(scenario)]
                        ),
                    }
                    prompts.append(template.format(**context))
            else:
                raise ValueError(f"Unsupported target type: {target_type}")

        if not prompts:
            raise ValueError("No prompts were generated.")

        limited_prompts = prompts
        if self.limit is not None:
            limited_prompts = prompts[: self.limit]

        if not limited_prompts:
            return []

        for index, prompt in enumerate(limited_prompts, start=1):
            destination = self.launch_pad_dir / f"prompt_{index:02d}.txt"
            destination.write_text(prompt, encoding="utf-8")

        return [str(path) for path in sorted(self.launch_pad_dir.glob("prompt_*.txt"))]
