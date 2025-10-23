from pathlib import Path
from types import SimpleNamespace

import pytest

import launch_control.houston as houston
from launch_control.houston import MissionControl

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LAUNCH_PAD_DIR = PROJECT_ROOT / "prompts" / "launch_pad"


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


def _read_prompt(path_str: str) -> str:
    path = Path(path_str)
    return path.read_text(encoding="utf-8")


def test_build_prompts_module_targets():
    args = _make_args(target_type="module")
    mc = MissionControl(args)
    targets = [{"module": "assisted-grading-core"}]

    prompts = mc.build_prompts(targets)

    assert len(prompts) == 1
    prompt_text = _read_prompt(prompts[0])
    assert "!moduleunittest" in prompt_text
    assert "Module\nassisted-grading-core" in prompt_text
    assert "{PLAYBOOK}" not in prompt_text


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
    prompt_text = _read_prompt(prompts[0])
    assert "!classunittest" in prompt_text
    assert "Class\ncom.example.FooService" in prompt_text


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
    prompt_text = _read_prompt(prompts[0])
    assert "!methodunittest" in prompt_text
    assert "Method\nprocess" in prompt_text
    assert "Class\ncom.example.FooService" in prompt_text


def test_build_prompts_integration_targets():
    args = _make_args(stack="cle", type="integration", target_type="scenario")
    mc = MissionControl(args)
    targets = [{"module": "checklist-editor-api", "scenarios": ["54"]}]

    prompts = mc.build_prompts(targets)

    assert len(prompts) == 1
    prompt_text = _read_prompt(prompts[0])
    assert "!integrationtest" in prompt_text
    assert "Scenario\n54" in prompt_text
    assert "Module\nchecklist-editor-api" in prompt_text


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
    prompt_files = sorted(LAUNCH_PAD_DIR.glob("prompt_*.txt"))
    assert len(prompt_files) == 1


def test_build_prompts_zero_limit_clears_launch_pad():
    # Create a stale prompt that should be removed when limit is zero.
    LAUNCH_PAD_DIR.mkdir(parents=True, exist_ok=True)
    stale_prompt = LAUNCH_PAD_DIR / "prompt_42.txt"
    stale_prompt.write_text("stale prompt", encoding="utf-8")

    args = _make_args(limit=0)
    mc = MissionControl(args)
    targets = [{"module": "assisted-grading-core"}]

    prompts = mc.build_prompts(targets)

    assert prompts == []
    assert list(LAUNCH_PAD_DIR.glob("prompt_*.txt")) == []


def test_load_prompt_returns_inline_prompt():
    args = _make_args(type="prompt", target_type=None)
    mc = MissionControl(args)

    prompt_text, source = mc._load_prompt("Investigate outage")

    assert prompt_text.startswith("Investigate outage")
    assert source == "inline prompt"


def test_load_prompt_reads_prompt_file():
    args = _make_args()
    mc = MissionControl(args)

    prompt_path = LAUNCH_PAD_DIR / "prompt_test.txt"
    LAUNCH_PAD_DIR.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text("Test prompt", encoding="utf-8")

    try:
        prompt_text, source = mc._load_prompt("prompts/launch_pad/prompt_test.txt")
        assert prompt_text == "Test prompt"
        assert source.endswith("prompt_test.txt")
    finally:
        prompt_path.unlink(missing_ok=True)


def test_launch_prompts_skips_missing_files(monkeypatch):
    args = _make_args()
    mc = MissionControl(args)

    LAUNCH_PAD_DIR.mkdir(parents=True, exist_ok=True)
    prompt_path = LAUNCH_PAD_DIR / "prompt_launch.txt"
    prompt_path.write_text("Launch me", encoding="utf-8")

    class DummyResponse:
        status_code = 200
        text = "ok"

    class DummyAPI:
        def __init__(self):
            self.prompts = []

        def post_prompt(self, prompt: str):
            self.prompts.append(prompt)
            return DummyResponse()

    dummy_api = DummyAPI()
    monkeypatch.setattr(houston, "DevinAPI", lambda: dummy_api)

    prompts = [
        str(prompt_path),
        str(LAUNCH_PAD_DIR / "missing.txt"),
    ]

    mc.launch_prompts(prompts)

    assert dummy_api.prompts == ["Launch me"]
