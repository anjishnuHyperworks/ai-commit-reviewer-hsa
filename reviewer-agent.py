''' AI Commit Reviewer Agent — tracks h-engine-frontend-dev and h-engine-backend-dev '''

import os
import subprocess
import re
import datetime
import pytz

from dotenv import load_dotenv
from groq import Groq

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REPOS = {
    "h-engine-frontend-dev": os.path.join(BASE_DIR, "h-engine-frontend-dev"),
    "h-engine-backend-dev":  os.path.join(BASE_DIR, "h-engine-backend-dev"),
}

LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")


class GitLogs:
    def __init__(self):
        self.commit_hashes = []
        self.date_times = []
        self.messages = []
        self.diff = ""

    def get_all_info(self, directory_path):
        self.directory_path = directory_path

        git_log_command = subprocess.run(
            ['git', 'log', '-20'],
            cwd=self.directory_path, capture_output=True, text=True, shell=True
        )
        git_log_lines = [c for c in git_log_command.stdout.splitlines() if c.split()]

        self.date_times    = [c.split('   ')[1] for c in git_log_lines if re.match(r'\bDate\b', c)]
        self.messages      = [c.strip() for c in git_log_lines if c[0] == ' ']
        self.commit_hashes = [c.split()[1] for c in git_log_lines if re.match(r'\bcommit\b', c)]

        if len(self.commit_hashes) >= 2:
            git_diff_command = subprocess.run(
                ['git', 'diff', self.commit_hashes[1], self.commit_hashes[0]],
                cwd=self.directory_path, capture_output=True, text=True, shell=True
            )
            self.diff = git_diff_command.stdout
        else:
            self.diff = "(only one commit — no diff available)"

        return (
            f"Commit Hashes: {self.commit_hashes}\n"
            f"Date and Times: {self.date_times}\n"
            f"Messages: {self.messages}\n"
            f"Diff for last commit:\n{self.diff}"
        )

    def get_status(self, directory_path):
        self.directory_path = directory_path
        result = subprocess.run(
            ['git', 'status'],
            cwd=self.directory_path, capture_output=True, text=True, shell=True
        )
        return result.stdout


class LLM:
    def __init__(self, name, api_key, model, prompt, role):
        self.name     = name
        self.api_key  = api_key
        self.model    = model
        self.prompt   = prompt
        self.role     = role
        self.response = ""

    def __str__(self):
        return f"LLM Name: {self.name}\nModel: {self.model}\nPrompt: {self.prompt}\nRole: {self.role}"

    def get_response(self):
        client = Groq(api_key=self.api_key)
        chat_completion = client.chat.completions.create(
            model=self.model,
            messages=[{"role": self.role, "content": self.prompt}]
        )
        self.response = chat_completion.choices[0].message.content
        return self.response


SYSTEM_PROMPT = """\
Following is the git log data and the diff for the last commit from the provided repository.
Analyze it and provide your insights and recommendations.
Provide the response in markdown format with appropriate headings and bullet points where necessary.

"""


def review_repo(repo_name: str, repo_path: str, api_key: str) -> str:
    print(f"\n[{repo_name}] Fetching git info...")
    git_logs = GitLogs()
    git_info = git_logs.get_all_info(repo_path)

    print(f"[{repo_name}] Sending to LLM...")
    llm = LLM(
        name="Groq",
        api_key=api_key,
        model="openai/gpt-oss-120b",
        prompt=SYSTEM_PROMPT + git_info,
        role="user",
    )
    return llm.get_response()


def save_log(repo_name: str, content: str, timestamp: str) -> str:
    filename = f"{repo_name}_{timestamp}.md"
    path = os.path.join(LOGS_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# Commit Review — {repo_name}\n\n")
        f.write(content)
    return path


if __name__ == "__main__":
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError("GROQ_API_KEY not found. Add it to the .env file in h2-system-analysis/.")

    ist = pytz.timezone("Asia/Kolkata")
    timestamp = datetime.datetime.now(ist).strftime("%Y-%m-%d_%H-%M-%S")

    for repo_name, repo_path in REPOS.items():
        if not os.path.isdir(repo_path):
            print(f"[{repo_name}] Directory not found, skipping: {repo_path}")
            continue

        response = review_repo(repo_name, repo_path, api_key)
        log_path = save_log(repo_name, response, timestamp)
        print(f"[{repo_name}] Log saved: {log_path}")
