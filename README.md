# Tracker

## Setup

Install the project dependencies with `pip`, not `pipx`.

`pipx` installs standalone command-line apps; it does not support `-r requirements.txt` for project dependencies.

Recommended setup:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run tracker.py
```

Note: you must run the activate command in every new terminal session before using `streamlit`.
If you do not want to activate, run with the full path instead: `.venv/bin/streamlit run tracker.py`.

If you prefer `pipx`, install the project itself instead of the requirements file:

```bash
pipx install .
tracker
```
