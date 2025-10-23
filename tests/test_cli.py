from types import SimpleNamespace

import pytest

from launch_control import cli


def test_build_parser_configures_expected_arguments(monkeypatch):
    created_parser = None

    class DummyParser:
        def __init__(self, *args, **kwargs):
            self.init_args = args
            self.init_kwargs = kwargs
            self.arguments = []

        def add_argument(self, *args, **kwargs):
            self.arguments.append((args, kwargs))

    def parser_factory(*args, **kwargs):
        nonlocal created_parser
        created_parser = DummyParser(*args, **kwargs)
        return created_parser

    monkeypatch.setattr(cli, "ArgumentParser", parser_factory)

    parser = cli._build_parser()

    assert parser is created_parser
    assert created_parser.init_kwargs["description"] == "Generate Devin AI sessions."

    expected_flags = [
        ("-s", "--stack"),
        ("-j", "--jira"),
        ("-t", "--type"),
        ("-tt", "--target-type"),
        ("-p", "--prompt"),
        ("-l", "--limit"),
        ("-d", "--debug"),
    ]

    actual_flags = [entry[0] for entry in created_parser.arguments]
    assert actual_flags == expected_flags

    stack_kwargs = created_parser.arguments[0][1]
    assert stack_kwargs["choices"] == ["asg", "p2d", "cle"]
    assert stack_kwargs["required"] is True

    prompt_kwargs = created_parser.arguments[4][1]
    assert prompt_kwargs["required"] is False

    debug_kwargs = created_parser.arguments[6][1]
    assert debug_kwargs["action"] == "store_true"


def test_validate_args_accepts_valid_configuration():
    args = SimpleNamespace(type="unit", prompt=None, target_type="module")
    cli._validate_args(args)


def test_validate_args_rejects_invalid_type():
    args = SimpleNamespace(type="unsupported", prompt=None, target_type="module")
    with pytest.raises(ValueError) as excinfo:
        cli._validate_args(args)
    assert "Invalid session type" in str(excinfo.value)


def test_validate_args_requires_prompt_for_prompt_type():
    args = SimpleNamespace(type="prompt", prompt=None, target_type=None)
    with pytest.raises(ValueError) as excinfo:
        cli._validate_args(args)
    assert "Prompt is required" in str(excinfo.value)


def test_validate_args_forces_scenario_for_integration():
    args = SimpleNamespace(type="integration", prompt=None, target_type="class")
    cli._validate_args(args)
    assert args.target_type == "scenario"


def test_validate_args_rejects_invalid_unit_target():
    args = SimpleNamespace(type="unit", prompt=None, target_type="scenario")
    with pytest.raises(ValueError) as excinfo:
        cli._validate_args(args)
    assert "Target type must be one of" in str(excinfo.value)


def test_main_parses_and_launches(monkeypatch):
    parsed_args = SimpleNamespace(type="unit", prompt=None, target_type="module")

    class DummyParser:
        def parse_args(self):
            return parsed_args

    monkeypatch.setattr(cli, "_build_parser", lambda: DummyParser())

    validated_args = {}

    def fake_validate(args):
        validated_args["args"] = args

    monkeypatch.setattr(cli, "_validate_args", fake_validate)

    mission_control_calls = {}

    class DummyMissionControl:
        def __init__(self, args):
            mission_control_calls["init_args"] = args

        def launch(self):
            mission_control_calls["launch_called"] = True

    monkeypatch.setattr(cli, "MissionControl", DummyMissionControl)

    cli.main()

    assert validated_args["args"] is parsed_args
    assert mission_control_calls["init_args"] is parsed_args
    assert mission_control_calls["launch_called"] is True
