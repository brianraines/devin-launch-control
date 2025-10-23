"""
Rocket fuel handles mixing the prompt payloads before launch.
"""

from pathlib import Path
from typing import Iterable, List, Mapping
import shutil
import random


class RocketFuel:
    """
    Prepare prompts for the launch sequence.
    """

    def __init__(self, args, repo: str):
        self.args = args
        self.repo = repo
        self.limit = int(args.limit)
        self.clear_launch_pad()

    def clear_launch_pad(self):
        """
        Clear the launch pad directory.
        """
        launch_pad_dir = Path("prompts/launch_pad")
        if launch_pad_dir.exists():
            shutil.rmtree(launch_pad_dir)
        launch_pad_dir.mkdir(parents=True, exist_ok=True)
        for file in launch_pad_dir.glob("*.txt"):
            file.unlink()

    def build_prompts(self, targets: Iterable[Mapping]) -> List[str]:
        """
        Build prompts from the provided targets and command arguments.
        """

        if self.args.type == "prompt":
            with open("prompts/custom.txt", "r", encoding="utf-8") as handle:
                template = handle.read()
            prompt = template.format(
                REPO=self.repo,
                OBJECTIVE=self.args.prompt,
                JIRA_TICKET=self.args.jira,
            )
            return [prompt]

        with open("prompts/playbook.txt", "r", encoding="utf-8") as handle:
            template = handle.read()

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

        for target in targets:
            if self.limit is not None and len(prompts) >= self.limit:
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
                    if len(prompts) >= self.limit:
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
                    if len(prompts) >= self.limit:
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
                    if len(prompts) >= self.limit:
                        break

                    context = {
                        **base_context,
                        "PLAYBOOK": "!java_module_int_test",
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

        launch_pad_dir = Path("prompts/launch_pad")
        launch_pad_dir.mkdir(parents=True, exist_ok=True)

        for index, prompt in enumerate(prompts, start=1):
            destination = launch_pad_dir / f"prompt_{index:02d}.txt"
            with destination.open("w", encoding="utf-8") as handle:
                handle.write(prompt)

        return [str(destination) for destination in launch_pad_dir.glob("*.txt")]
