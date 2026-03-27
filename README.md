# timetracker

Linux time-tracker (GUI) — MVP.

## Requirements
- Python 3.12+

## Install (venv)
```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"
````

## Run

```bash
python -m app
```

## Run tests

```bash
pytest
```
## Close behavior

- Если таймер не активен, окно закрывается сразу.
- Если таймер в состоянии `RUNNING` или `PAUSED`, приложение показывает подтверждение.
- При подтверждении текущая сессия завершается через обычный `stop()` и сохраняется.

