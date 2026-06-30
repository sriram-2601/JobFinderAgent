# Production Deployment Guide (Oracle Cloud Free Tier)

This guide provides step-by-step instructions for deploying the Autonomous Job Search and Application Platform to a cloud host, specifically tailored to the **Oracle Cloud Free Tier (Ubuntu VM.Standard.A1.Flex or VM.Standard.E2.1.Micro)**.

---

## 1. Cloud Infrastructure Setup
1. Log in to your **Oracle Cloud Console**.
2. Spin up a compute instance (Ubuntu 22.04 LTS recommended). Ensure you open port **80** (HTTP) and **22** (SSH) in the Virtual Cloud Network (VCN) Security Lists.
3. SSH into your instance:
   ```bash
   ssh -i your-key.key ubuntu@your-instance-ip
   ```

---

## 2. Server Package Preparations
Run the following commands on the Ubuntu server to update packages, install git, Docker, and Docker Compose:
```bash
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y git curl

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu
newgrp docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

---

## 3. Clone and Configure Platform
1. Create a workspace directory and clone your repository or copy code files to `/home/ubuntu/Jobfinder`.
2. Move into the directory:
   ```bash
   cd /home/ubuntu/Jobfinder
   ```
3. Copy the environment configuration and fill in the active keys:
   ```bash
   cp .env.example .env
   nano .env
   ```
   *Note: Ensure `APP_MODE` is set to `APPROVAL` or `AUTONOMOUS` depending on your automation preference.*

---

## 4. Run Services via Docker Compose
Build and launch containers in detached production mode:
```bash
docker-compose up --build -d
```
Verify container statuses:
```bash
docker-compose ps
```
The dashboard is now live on port 80: `http://your-instance-ip`.

---

## 5. Enable Systemd Daemon Auto-Restart
To ensure the containers automatically launch upon VM reboot, network interruptions, or process crashes:
1. Copy the systemd template:
   ```bash
   sudo cp deployment/jobfinder.service /etc/systemd/system/jobfinder.service
   ```
2. Enable and start the systemd daemon:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable jobfinder.service
   sudo systemctl start jobfinder.service
   ```
3. Check status:
   ```bash
   sudo systemctl status jobfinder.service
   ```

---

## 6. Configure Scheduled Backups
To run the database backup script automatically every day at midnight:
1. Open the system crontab editor:
   ```bash
   crontab -e
   ```
2. Append the following cron task at the bottom:
   ```cron
   0 0 * * * cd /home/ubuntu/Jobfinder && /bin/bash deployment/backup.sh >> data/logs/backup.log 2>&1
   ```
3. Save and close. This backup retains the database copies inside `data/backups` and purges copies older than 14 days automatically.

---

## 7. Monitoring Server Logs
To check the outputs from your job searching agents and Playwright form submissions in real time:
```bash
# View all backend container logs
docker logs -f jobfinder-backend

# View systemd service status
sudo journalctl -u jobfinder.service -f
```
