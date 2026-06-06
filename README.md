# AI Commit Reviewer

Automated post-commit agent that analyzes recent git activity and generates LLM-powered review reports for tracked repositories.

## What It Does

- Hooks into the git post-commit lifecycle of tracked repos
- Fetches the last 20 commits and the diff for the most recent one
- Sends the data to an LLM (via Groq) for analysis and recommendations
- Saves the review as a timestamped Markdown file in `logs/`

## Setup

**Prerequisites**
- Python environment: `ai-mentor-env` (`C:\Users\HP\miniconda3\envs\ai-mentor-env`)
- Groq API key in `.env`:
  ```
  GROQ_API_KEY=your_key_here
  ```

**Post-commit hook** — create `.git/hooks/post-commit` in your repo with the following content, then make it executable:

```sh
#!/bin/sh
REVIEWER="/path/to/ai-commit-reviewer-hsa/reviewer-agent.py"

if [ -f "$REVIEWER" ]; then
    /path/to/python "$REVIEWER" <repo-name>
fi
```

- Replace `/path/to/ai-commit-reviewer-hsa/reviewer-agent.py` with the absolute path to `reviewer-agent.py`
- Replace `/path/to/python` with the Python executable from your environment
- Replace `<repo-name>` with the folder name of the repo (must match a key in `REPOS` inside `reviewer-agent.py`)

Make it executable:
```bash
chmod +x .git/hooks/post-commit
```

## Usage

Runs automatically on commit. To trigger manually:

```bash
# Review a specific repo
python reviewer-agent.py <repo-name>

# Review all configured repos
python reviewer-agent.py
```

## Output

Logs are saved to `logs/` as:
```
{repo-name}_{YYYY-MM-DD_HH-MM-SS}.md
```

---

> **Note:** This project is currently in active development.
