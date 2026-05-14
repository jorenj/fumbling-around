# DocSortBot

A smart, self-recovering CLI tool that monitors a directory, automatically extracts dates from financial documents using deep content inspection, and sorts them into year-based folders.

## How it Works (V2 Features)

### The Sorting Algorithm
When a file is discovered, DocSortBot determines its correct year using a strict, multi-step heuristic designed to eliminate false positives from random numbers (like $2000) or misleading copyright footers:

1. **Filename Check (Highest Priority):** If the file's name already contains exactly one clear 4-digit year (e.g., `w-2 2026.pdf`), it trusts the filename 100% and sorts the file instantly, skipping complex text analysis.
2. **Anchor Keyword Search:** If the filename is ambiguous, the bot reads the document's text and searches for specific financial anchor keywords (like `Statement`, `Tax Return`, `W-2`, `1099`, or `Period`). It collects all years found within 50 characters of these keywords across the entire document. It then selects the most frequently occurring anchored year (resolving ties by picking the most recent year).
3. **Top-Heavy Frequency Analysis:** If no anchor words are found, it analyzes the top 25% of the document (since primary dates usually appear in headers and summaries rather than copyright footers). It extracts all valid 4-digit years found in this section and selects the most frequent one.
4. **Document-Wide Fallback:** If the top 25% yields nothing, it analyzes the entire document and picks the most common year overall.

*(Note: The algorithm is hardcoded to completely ignore 4-digit numbers preceded by a `$` or followed by a decimal `.00` to prevent confusing monetary amounts for years).*

### Additional Features
- **Live Web Dashboard:** Run the bot with the `--dashboard` flag to launch a sleek, live-updating web interface on `localhost:8000`. You can watch files get sorted in real-time and click on them to see exactly which evaluation rule the algorithm used! (Powered by FastAPI and SQLite).
- **Auto-Renaming:** If a year was discovered from the contents rather than the filename, the bot automatically renames the file to explicitly include it (e.g. `[2023]_Bank_Statement.pdf`) before moving it into the correct subfolder.
- **Auto-Discovery & Memory:** If you run the bot without specifying a path, it will use macOS Spotlight to automatically hunt down your `Statements` folder. Once found (or specified manually via `--path`), it saves the configuration permanently so you never have to specify it again.

## Installation
The following command installs the `docsortbot` CLI command into your Python environment. It also installs its dependencies: `watchdog`, `pypdf`, `fastapi`, and `uvicorn`.

```bash
python3 -m pip install -e '.[dev]'
```

## Usage
```bash
# Monitor the default ~/Statements folder
./.venv/bin/docsortbot

# Run the live web dashboard concurrently
./.venv/bin/docsortbot --dashboard

# Run in dry-run mode (no files moved)
./.venv/bin/docsortbot --dry-run
```

## Running as a Background Service (macOS)
To run DocSortBot continuously in the background so it survives computer reboots and doesn't require you to keep a terminal window open, you can set it up as a macOS **Launch Agent** using the included configuration file.

1. **Install the configuration file:**
   Copy the provided `.plist` file to your macOS LaunchAgents directory:
   ```bash
   cp com.jorenjackson.docsortbot.plist ~/Library/LaunchAgents/
   ```

2. **Start the background service:**
   Load the agent into the system so it starts immediately and on every login:
   ```bash
   launchctl load ~/Library/LaunchAgents/com.jorenjackson.docsortbot.plist
   ```

**To stop or uninstall the background service:**
```bash
launchctl unload ~/Library/LaunchAgents/com.jorenjackson.docsortbot.plist
rm ~/Library/LaunchAgents/com.jorenjackson.docsortbot.plist
```
