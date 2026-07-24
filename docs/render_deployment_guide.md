# Deploying JobFinderAgent to Render (via Docker)

This guide provides step-by-step instructions for deploying the **JobFinderAgent** (frontend + backend) to Render as a unified Docker Web Service.

---

## Prerequisites

1. A **GitHub** account with your `JobFinderAgent` repository pushed.
2. A **Render** account (free tier available at [render.com](https://render.com)).
3. Environment variable values for your APIs and integrations (Gemini API Key, Telegram credentials, etc.).

---

## Step 1: Create a Web Service on Render

1. Log in to the [Render Dashboard](https://dashboard.render.com).
2. Click **New +** at the top right and select **Web Service**.
3. Connect your GitHub repository containing the `JobFinderAgent` code.

---

## Step 2: Configure Service Settings

Configure the web service details as follows:

* **Name:** `jobfinder-agent` (or any preferred name)
* **Region:** Select the region closest to you
* **Branch:** `main` (or whichever branch you push deployment changes to)
* **Runtime:** Select **Docker** (Render will automatically detect the [Dockerfile](file:///c:/Users/srira/Desktop/pro/Jobfinder/Dockerfile) in the root)
* **Instance Type:** **Free** (or Starter/Standard)

---

## Step 3: Add Environment Variables

In the **Environment** tab of your Render service, click **Add Environment Variable** and configure the following variables:

| Key | Value | Notes |
| :--- | :--- | :--- |
| `APP_MODE` | `APPROVAL` or `AUTONOMOUS` | Controls if applications submit automatically or queue for review |
| `DATABASE_URL` | `sqlite:///app/data/jobfinder.db` | Path inside the container |
| `JWT_SECRET` | *[Generate a strong secret key]* | Used to encrypt JWT sessions |
| `ENCRYPTION_KEY` | *[Generate a strong Fernet key]* | Run `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `GEMINI_API_KEY` | `your_gemini_api_key` | Required for AI matching and text parsing |
| `TELEGRAM_BOT_TOKEN` | `your_telegram_bot_token` | *(Optional)* For real-time updates |
| `TELEGRAM_CHAT_ID` | `your_telegram_chat_id` | *(Optional)* For real-time updates |
| `SMTP_SERVER` | `smtp.gmail.com` | *(Optional)* |
| `SMTP_PORT` | `587` | *(Optional)* |
| `SMTP_USERNAME` | `your_email@gmail.com` | *(Optional)* |
| `SMTP_PASSWORD` | `your_app_specific_password` | *(Optional)* |

---

## Step 4: Configure Persistent Disk Volume (Optional but Recommended)

Render's free tier has an ephemeral filesystem, meaning your local SQLite database will reset whenever the container restarts or redeploys. To make database files persistent:

1. In your Web Service settings, scroll down to the **Disks** section.
2. Click **Add Disk**.
3. Set the details:
   - **Name:** `jobfinder-data`
   - **Mount Path:** `/app/data` (this maps to `DATA_DIR` in the backend config)
   - **Size:** `1 GB` (sufficient for SQLite database, logs, and screenshots)
4. *Note: Disks require a paid Render instance (starts at $5/month for the instance + $0.25/GB/month for the disk). If you are using the free tier, your database will reset on redeployment.*

---

## Step 5: Deploy the Web Service

1. Click **Create Web Service** at the bottom of the page.
2. Render will trigger a build and:
   - Compile the React frontend using the Node builder stage.
   - Set up the Python FastAPI server.
   - Install system dependencies for Chromium.
   - Download the headless browser binaries.
3. Once the build completes and logs output `Application startup complete`, your app is live! 
4. The dashboard will be accessible via the Render URL: `https://jobfinder-agent.onrender.com`.
