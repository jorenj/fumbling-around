from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import uvicorn
from pathlib import Path

from .db import get_recent_logs

app = FastAPI(title="DocSortBot Dashboard")

# We will inject the base_dir when starting the server
app.state.base_dir = None

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DocSortBot Live Dashboard</title>
    <style>
        :root {
            --bg-color: #0f172a;
            --surface-color: #1e293b;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent: #38bdf8;
            --border: #334155;
            --success: #10b981;
        }
        
        body {
            font-family: 'Inter', -apple-system, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            margin: 0;
            padding: 0;
            line-height: 1.6;
        }

        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
        }

        h1 {
            font-weight: 700;
            letter-spacing: -0.025em;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .pulse {
            width: 10px;
            height: 10px;
            background-color: var(--success);
            border-radius: 50%;
            box-shadow: 0 0 10px var(--success);
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
            70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
        }

        .subtitle {
            color: var(--text-muted);
            margin-bottom: 3rem;
            font-size: 0.95rem;
        }

        .feed {
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }

        .card {
            background: rgba(30, 41, 59, 0.7);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            backdrop-filter: blur(10px);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            cursor: pointer;
            overflow: hidden;
        }

        .card:hover {
            transform: translateY(-2px);
            border-color: var(--accent);
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
        }

        .filename {
            font-weight: 600;
            font-size: 1.1rem;
            color: var(--text-main);
            word-break: break-all;
        }

        .year-badge {
            background-color: rgba(56, 189, 248, 0.1);
            color: var(--accent);
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.85rem;
            border: 1px solid rgba(56, 189, 248, 0.2);
        }

        .card-meta {
            color: var(--text-muted);
            font-size: 0.85rem;
            display: flex;
            gap: 1rem;
        }

        .details {
            max-height: 0;
            opacity: 0;
            overflow: hidden;
            transition: all 0.4s ease;
            margin-top: 0;
            border-top: 1px solid transparent;
            padding-top: 0;
        }

        .card.expanded .details {
            max-height: 200px;
            opacity: 1;
            margin-top: 1rem;
            border-top-color: var(--border);
            padding-top: 1rem;
        }

        .detail-row {
            display: flex;
            margin-bottom: 0.5rem;
            font-size: 0.9rem;
        }

        .detail-label {
            color: var(--text-muted);
            width: 140px;
            flex-shrink: 0;
        }

        .detail-value {
            color: var(--text-main);
            font-family: monospace;
            word-break: break-all;
        }

        .rule-badge {
            display: inline-block;
            background-color: #334155;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.8rem;
            color: #e2e8f0;
        }

        .empty-state {
            text-align: center;
            padding: 3rem;
            color: var(--text-muted);
            background: var(--surface-color);
            border-radius: 12px;
            border: 1px dashed var(--border);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1><div class="pulse"></div> DocSortBot Dashboard</h1>
        <div class="subtitle" id="status-text">Live stream connected. Waiting for files...</div>
        
        <div class="feed" id="feed">
            <!-- Cards will be injected here -->
        </div>
    </div>

    <script>
        let lastKnownId = 0;
        const feedElement = document.getElementById('feed');
        const statusText = document.getElementById('status-text');

        function createCardHTML(log) {
            return `
                <div class="card" onclick="this.classList.toggle('expanded')" id="log-${log.id}">
                    <div class="card-header">
                        <div class="filename">${log.original_filename}</div>
                        <div class="year-badge">${log.year}</div>
                    </div>
                    <div class="card-meta">
                        <span>🕒 ${new Date(log.timestamp + 'Z').toLocaleTimeString()}</span>
                        <span>📂 ${log.destination_folder}</span>
                    </div>
                    <div class="details">
                        <div class="detail-row">
                            <div class="detail-label">Original Name:</div>
                            <div class="detail-value">${log.original_filename}</div>
                        </div>
                        <div class="detail-row">
                            <div class="detail-label">New Name:</div>
                            <div class="detail-value">${log.new_filename}</div>
                        </div>
                        <div class="detail-row">
                            <div class="detail-label">Destination:</div>
                            <div class="detail-value">${log.destination_folder}</div>
                        </div>
                        <div class="detail-row">
                            <div class="detail-label">Sorter Rule:</div>
                            <div class="detail-value"><span class="rule-badge">${log.evaluation_rule || 'Unknown'}</span></div>
                        </div>
                    </div>
                </div>
            `;
        }

        async function fetchLogs() {
            try {
                const response = await fetch('/api/logs');
                if (!response.ok) throw new Error('Network response was not ok');
                const logs = await response.json();
                
                if (logs.length === 0 && feedElement.innerHTML.trim() === '') {
                    feedElement.innerHTML = '<div class="empty-state">No files have been sorted yet.</div>';
                    return;
                }

                // Reverse so newest is at the top conceptually, though we usually prepend new ones
                logs.reverse();

                let hasNew = false;
                logs.forEach(log => {
                    if (log.id > lastKnownId) {
                        hasNew = true;
                        lastKnownId = log.id;
                        
                        // Remove empty state if it exists
                        const emptyState = document.querySelector('.empty-state');
                        if (emptyState) emptyState.remove();

                        // Create temporary element to parse HTML
                        const temp = document.createElement('div');
                        temp.innerHTML = createCardHTML(log);
                        const card = temp.firstElementChild;
                        
                        // Prepend to feed
                        feedElement.insertBefore(card, feedElement.firstChild);
                        
                        // Optional: trigger animation
                        card.style.opacity = '0';
                        card.style.transform = 'translateY(-20px)';
                        setTimeout(() => {
                            card.style.opacity = '1';
                            card.style.transform = 'translateY(0)';
                        }, 50);
                    }
                });
                
                statusText.innerHTML = `Live stream connected. Monitoring directory.`;
                
            } catch (error) {
                console.error("Error fetching logs:", error);
                statusText.innerHTML = `<span style="color: #ef4444;">⚠️ Connection lost. Retrying...</span>`;
            }
        }

        // Initial fetch
        fetchLogs();
        
        // Poll every 2 seconds
        setInterval(fetchLogs, 2000);
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    return HTML_CONTENT

@app.get("/api/logs")
async def api_get_logs(limit: int = 50):
    if not app.state.base_dir:
        raise HTTPException(status_code=500, detail="Base directory not configured.")
    logs = get_recent_logs(app.state.base_dir, limit)
    return logs

def start_server(base_dir: Path, port: int = 8000):
    app.state.base_dir = base_dir
    print(f"Starting web dashboard at http://localhost:{port} ...")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="error")
