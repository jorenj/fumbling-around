# Fumbling Around

This is a general monorepo for small hobby projects.

## Projects

### DocSortBot
A smart CLI tool for automating the management of financial documents. Features content-aware year extraction and a live web dashboard.

### CribbageBots
A Cribbage tournament engine that pits different bots (and humans!) against each other. It includes an optimized Python backend (FastAPI) and a modern web frontend (Vite/React). Features include a real-time Human vs Bot UI via WebSockets and high-performance Bulk Tournament simulation modes.

---

## Getting Started

To run the **Cribbage Tournament Engine** locally:

### 🚀 The Easy Way (One Script)
Run the master development script in the root directory:
```bash
./dev.sh
```
This script sets up the virtual environment, installs all dependencies, and starts both the backend and frontend concurrently.

---

### 🛠️ The Manual Way

#### 1. Backend (FastAPI)
```bash
cd CribbageBots/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cribbage api
```

#### 2. Frontend (React/Vite)
```bash
cd CribbageBots/frontend
npm install
npm run dev
```
Visit `http://localhost:5173` to view the dashboard.

For more details on the implementation and performance fixes, see the [walkthrough](file:///Users/jorenjackson/.gemini/antigravity/brain/4ee8df90-79fc-472d-931e-4e644f76418e/walkthrough.md).
