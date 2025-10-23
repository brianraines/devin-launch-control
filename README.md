# Devin Launch Control

Launch and orchestrate Devin AI sessions from the command line.

## Features
- Consistent CLI for starting new Devin AI sessions.
- Validation for supported stacks, ticket formats, and session types.
- Simple “Houston/Mission Control” abstraction ready to integrate with the Devin API.

## Prerequisites
- Python 3.9 or newer.
- Access to the Devin API, including a valid `DEVIN_API_KEY`.

## Installation
```bash
git clone https://github.com/your-org/devin-launch-control.git
cd devin-launch-control
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -e .[dev]  # installs runtime + dev tools
```

> Skip the `.[dev]` extra if you only need the CLI: `pip install -e .`.

## Configuration
Set the Devin API key so the CLI can authenticate:
```bash
export DEVIN_API_KEY="YOUR_API_KEY"
```

## Usage
Use the provided wrapper script, module entrypoint, or the installed console script.

```bash
devin-launch-control \
  --stack asg \
  --jira P2D-123 \
  --type unit \
  --target-type class \
  --limit 3
```

```bash
python3 launch.py \
  --stack asg \
  --jira P2D-123 \
  --type unit \
  --target-type class \
  --limit 3
```

The same invocation works via the module entrypoint:

```bash
python3 -m launch_control \
  --stack asg \
  --jira P2D-123 \
  --type unit \
  --target-type class \
  --limit 3
```

### Arguments
- `-s`, `--stack` *(required)*: GitHub stack to launch against. Choices: `asg`, `p2d`, `cle`.
- `-j`, `--jira`: Jira ticket identifier. Defaults to the stack-specific ticket (`asg → P2D-18`, `p2d → P2D-1816`, `cle → P2D-1793`) when omitted.
- `-t`, `--type`: Session type. Defaults to `unit`. Choices: `unit`, `integration`, `prompt`.
- `-tt`, `--target-type`: Target granularity for unit sessions. Defaults to `class`. Choices: `module`, `class`, `function`, `scenario`. Integration sessions always force `scenario` regardless of the supplied value.
- `-p`, `--prompt`: Prompt text when launching a prompt session.
- `-l`, `--limit`: Number of sessions to start. Integer, defaults to `5`.
- `-d`, `--debug`: Enable debug output.

When `--type prompt` is used, the `--prompt` flag becomes required.

## Target Configuration
Mission Control reads launch targets from JSON payloads stored in `targets/<target_type>/<stack>.json`. The structure of the payload changes with the target type:

- **Module targets** – `targets/module/asg.json`
  ```json
  [
    { "module": "assisted-grading-core" },
    { "module": "assisted-grading-api" }
  ]
  ```
  Each entry points Devin at an entire module.

- **Class targets** – `targets/class/asg.json`
  ```json
  [
    {
      "module": "assisted-grading-core",
      "classes": [
        "com.turnitin.assistedgrading.core.service.AssistedGradingBaseService",
        "com.turnitin.assistedgrading.core.service.AssistedGradingService"
      ]
    }
  ]
  ```
  Define the module plus one or more fully qualified class names.

- **Function targets** – `targets/function/asg.json`
  ```json
  [
    {
      "module": "assisted-grading-core",
      "class": "com.turnitin.assistedgrading.core.service.AssistedGradingBaseService",
      "functions": [
        "findResponseGroupRecord",
        "updateGroupingConfirmOfResponseRecord"
      ]
    }
  ]
  ```
  Specify the module, owning class, and the functions (methods) to exercise.

- **Scenario targets** – `targets/scenario/cle.json`
  ```json
  [
    {
      "module": "checklist-editor-api",
      "scenarios": ["54", "55", "56"]
    }
  ]
  ```
  Pair the module with the integration scenario identifiers to run.

For `--type prompt`, no JSON file is required. Instead, the CLI formats `prompts/custom.txt` with the provided `--prompt`, Jira ticket, and stack-specific repository before sending the text directly to Devin.

## Development
- CLI entrypoint: `launch_control/cli.py`
- Mission control orchestration: `launch_control/houston.py`
- HTTP/API integration: `launch_control/api.py`

To add new commands or behaviours, extend `MissionControl.launch()` and the Devin API client.

## Testing
```bash
python3 -m pytest
```

## License
See [LICENSE](LICENSE) for details.
