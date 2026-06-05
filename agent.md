# AI Agent Instructions

Welcome! If you are an AI agent reading this, you are working in a hybrid Windows/WSL development environment. This repository is checked out as a **Git Worktree** on a Windows filesystem, which introduces a few critical idiosyncrasies you must be aware of to successfully write code, test, and commit here.

## 1. The Environment Split

*   **Git Operations ➔ Native Windows**
*   **Code Execution & Testing ➔ WSL (Ubuntu Linux)**

## 2. Git Operations (Native Windows ONLY)

Because this directory is a Git Worktree created on Windows, the internal `.git` file contains a hardcoded Windows path (e.g., `C:/Users/...`). 
If you try to run `git` or `gh` commands inside WSL, the Linux subsystem will see the `C:/` path, fail to parse it, and crash with `fatal: not a git repository`.

**Rule:** You MUST run all Git commands (add, commit, push, checkout) using your native Windows shell access. Do not use WSL for version control.

*Example:*
```powershell
git add .
git commit -m "feat: updated bot logic"
git push origin your-branch-name
```

## 3. Code Execution (WSL ONLY)

The development scripts (`dev.sh`) and the Python virtual environment are built for Linux. You must run all servers, scripts, and tournaments inside WSL.

**Rule:** Use `wsl bash -c "..."` to execute commands, or instruct the user to run them in their WSL terminal.

### Setting up the Environment
If the virtual environment does not exist, it must be created in WSL:
```bash
# In WSL
cd CribbageBots/backend
sudo apt update && sudo apt install python3.10-venv -y
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Running a Tournament
To test bot performance, run the `cribbage` CLI from within the WSL virtual environment.
```bash
# In WSL
cd CribbageBots/backend
./.venv/bin/cribbage run --p1 leifv4 --p2 leifv3 --games 1000
```
*(Note: As of a recent update, the tournament engine will print a live 1-line summary per game if `--verbose` is omitted).*

## 4. File Management

*   **Scratch Files:** If you need to create temporary scripts (e.g., probability simulators, benchmark tools), place them in the `CribbageBots/backend/scratch/` directory. Do not commit your temporary scripts unless the user explicitly asks you to.
*   **Tool Usage:** Do not use `echo >> file` or `cat` in bash to edit files. Use your agentic file editing tools to safely replace content.

Follow these rules, and you'll avoid the pathing headaches between Windows and WSL!
