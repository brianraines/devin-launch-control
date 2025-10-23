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
- `-j`, `--jira` *(required)*: Jira ticket identifier, e.g. `P2D-123`.
- `-t`, `--type`: Session type. Defaults to `unit`. Choices: `unit`, `integration`, `prompt`.
- `-tt`, `--target-type`: Target granularity for unit sessions. Defaults to `class`. Choices: `module`, `class`, `function`. For integration sessions this value is ignored and forced to `scenario`.
- `-p`, `--prompt`: Prompt text when launching a prompt session.
- `-l`, `--limit`: Number of sessions to start. Defaults to `5`.
- `-d`, `--debug`: Enable debug output.

When `--type prompt` is used, the `--prompt` flag becomes required.

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
