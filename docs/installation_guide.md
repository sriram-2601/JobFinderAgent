# Local Installation Guide

Follow these steps to run the Autonomous Job Search and Application Platform on your local machine for development or sandbox testing.

---

## 1. Prerequisites
Ensure you have the following installed on your machine:
- **Python**: Version 3.10 or higher (Python 3.12+ recommended).
- **Node.js**: Version 18 or higher (Node 20+ recommended).
- **npm**: Node Package Manager (comes with Node.js).
- **Git**: (Optional) for version control.

---

## 2. Directory Structure Setup
Ensure your workspace matches the following layout:
```
Jobfinder/
├── data/                  # SQLite storage & screenshots
├── src/                   # Backend API and agents
│   ├── agents/            # Crawler & AI engines
│   ├── services/          # Gemini, Email, Telegram, Playwright connectors
│   └── api/               # FastAPI endpoints
├── frontend/              # Vite React app
├── deployment/            # Docker compose and Systemd templates
└── docs/                  # Instruction manuals
```

---

## 3. Environment Configurations
1. Copy the environment variables template:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and fill in the target variables:
   - `GEMINI_API_KEY`: Generative model analysis key (required for resume optimizations).
   - `SMTP_USERNAME` / `SMTP_PASSWORD`: For email alerts.
   - `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID`: For mobile alerts.

---

## 4. Run Backend Locally (Without Docker)
1. Initialize a Python virtual environment:
   ```bash
   python -m venv .venv
   source .venv/Scripts/activate     # Windows
   # source .venv/bin/activate       # macOS/Linux
   ```
2. Install Python packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Install Playwright browser dependencies:
   ```bash
   playwright install chromium
   ```
4. Run the FastAPI development server:
   ```bash
   python -m uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000
   ```
   The backend API will be live at `http://127.0.0.1:8000`.

---

## 5. Run Frontend Locally (Without Docker)
1. Open a new terminal and navigate to the frontend folder:
   ```bash
   cd frontend
   ```
2. Install Node.js dependencies:
   ```bash
   npm install
   ```
3. Start the Vite React development server:
   ```bash
   npm run dev
   ```
   The interactive dashboard will be live at `http://localhost:5173`. Open this URL in your web browser.

---

## 6. Run Entire Stack Using Docker Compose
1. Ensure Docker and Docker Compose are installed and running.
2. Build and launch all services in the background:
   ```bash
   docker-compose up --build -d
   ```
3. Check container statuses:
   ```bash
   docker-compose ps
   ```
4. The dashboard will be accessible on port 80: `http://localhost`. The FastAPI server will be exposed on port 8000: `http://localhost:8000`.
