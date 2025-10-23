from pathlib import Path
from types import SimpleNamespace

import pytest

from launch_control.houston import MissionControl


def _make_args(**overrides):
    defaults = {
        "stack": "asg",
        "type": "unit",
        "target_type": "module",
        "prompt": None,
        "jira": "P2D-123",
        "limit": 5,
        "debug": False,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_build_prompts_module_targets():
    args = _make_args(target_type="module")
    mc = MissionControl(args)
    targets = [{"module": "assisted-grading-core"}]

    prompts = mc.build_prompts(targets)

    assert len(prompts) == 1
    prompt = prompts[0]
    assert "!moduleunittest" in prompt
    assert "Module\nassisted-grading-core" in prompt
    assert "{PLAYBOOK}" not in prompt


def test_build_prompts_class_targets():
    args = _make_args(target_type="class")
    mc = MissionControl(args)
    targets = [
        {
            "module": "assisted-grading-core",
            "classes": ["com.example.FooService"],
        }
    ]

    prompts = mc.build_prompts(targets)

    assert len(prompts) == 1
    prompt = prompts[0]
    assert "!classunittest" in prompt
    assert "Class\ncom.example.FooService" in prompt


def test_build_prompts_function_targets():
    args = _make_args(target_type="function")
    mc = MissionControl(args)
    targets = [
        {
            "module": "assisted-grading-core",
            "class": "com.example.FooService",
            "functions": ["process"],
        }
    ]

    prompts = mc.build_prompts(targets)

    assert len(prompts) == 1
    prompt = prompts[0]
    assert "!methodunittest" in prompt
    assert "Method\nprocess" in prompt
    assert "Class\ncom.example.FooService" in prompt


def test_build_prompts_integration_targets():
    args = _make_args(stack="cle", type="integration", target_type="scenario")
    mc = MissionControl(args)
    targets = [{"module": "checklist-editor-api", "scenarios": ["54"]}]

    prompts = mc.build_prompts(targets)

    assert len(prompts) == 1
    prompt = prompts[0]
    assert "!integrationtest" in prompt
    assert "Scenario\n54" in prompt
    assert "Module\nchecklist-editor-api" in prompt


def test_build_prompts_prompt_type():
    args = _make_args(type="prompt", target_type=None, prompt="Investigate issue")
    mc = MissionControl(args)

    prompts = mc.build_prompts([])

    assert len(prompts) == 1
    prompt = prompts[0]
    assert "Investigate issue" in prompt
    assert "!moduleunittest" not in prompt


def test_build_prompts_requires_class_for_function_targets():
    args = _make_args(target_type="function")
    mc = MissionControl(args)
    targets = [{"module": "assisted-grading-core", "functions": ["foo"]}]

    with pytest.raises(ValueError):
        mc.build_prompts(targets)


def test_build_prompts_respects_limit():
    args = _make_args(target_type="class", limit=1)
    mc = MissionControl(args)
    targets = [
        {
            "module": "assisted-grading-core",
            "classes": [
                "com.example.FooService",
                "com.example.BarService",
            ],
        }
    ]

    prompts = mc.build_prompts(targets)

    assert len(prompts) == 1
    launch_pad_dir = Path("prompts/launch_pad")
    prompt_files = list(launch_pad_dir.glob("prompt_*.txt"))
    assert len(prompt_files) == 1


def test_build_prompts_zero_limit_removes_existing_prompts():
    launch_pad_dir = Path("prompts/launch_pad")
    launch_pad_dir.mkdir(parents=True, exist_ok=True)
    existing = launch_pad_dir / "prompt_42.txt"
    existing.write_text("stale prompt", encoding="utf-8")

    args = _make_args(limit=0)
    mc = MissionControl(args)
    targets = [{"module": "assisted-grading-core"}]

    prompts = mc.build_prompts(targets)

    assert prompts == []
    assert list(launch_pad_dir.glob("prompt_*.txt")) == []
