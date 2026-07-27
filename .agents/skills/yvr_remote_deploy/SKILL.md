---
name: yvr-remote-deploy
description: Context and instructions for developing and deploying the YVR Rideshare Radar project directly to the remote Google Cloud VM using `ssh yvrr`.
---

# YVR Rideshare Radar - Remote Development & Deployment Skill

This skill provides the architectural context and strict execution rules for the "YVR Rideshare Radar" project. 
The core idea is to collect events across Vancouver (e.g., parsing from Luma) and display them on Google Maps via a web interface to help rideshare drivers find high-demand areas.
The user does NOT work locally on their Mac; all code generation, execution, and deployment must happen on the remote Google Cloud VM.

## 1. Remote Execution Rules (CRITICAL)
- **Do not run project code or containers locally.** 
- You MUST interact with the remote machine using the `ssh yvrr` command.
- To execute commands on the remote machine, use your command execution tool, for example: `ssh yvrr 'ls -la'`.
- To create or modify files on the remote machine, use SSH with heredocs, for example: 
  ```bash
  ssh yvrr "cat << 'EOF' > ~/yvr-radar/docker-compose.yml
  ...content...
  EOF"
  ```
- The project directory on the remote machine should be `~/yvr-radar`. Create it if it doesn't exist: `ssh yvrr 'mkdir -p ~/yvr-radar'`.
- When starting containers, use: `ssh yvrr 'cd ~/yvr-radar && docker compose up -d --build'`.

## 2. Environment & Architecture Context
- **Remote Target**: Google Cloud Compute Engine VM (Ubuntu/Debian) with a PUBLIC IP.
- **Domain**: `yvrr.kravchuk.net.ua` (DNS A-record points to the VM's public IP).
- **Containerization**: Docker Compose.

## 3. Security & Tech Stack Requirements (STRICT)
- **Database**: PostgreSQL + PostGIS.
  - **CRITICAL SECURITY**: Do NOT expose the database port (5432) to the host. It must only be accessible via Docker's internal network.
- **Environment Variables**: ALL secrets (DB passwords, Admin login/password, API keys, CAPTCHA secrets) must be loaded exclusively from a `.env` file. Ensure `.gitignore` explicitly ignores `.env`.
- **Backend/Web Server**: Python 3.11 (e.g., FastAPI).
  - **Custom Authentication**: Implement a custom HTML login page.
  - **Anti-Bruteforce**: Implement IP-based rate limiting for the login endpoint. If an IP address fails to authenticate 12 times, block that IP (return 403) for at least 1 hour.
  - **Bot Protection**: Integrate Cloudflare Turnstile (or Google reCAPTCHA) on the login form. Validate the CAPTCHA token on the backend before checking credentials. Provide placeholders for the keys in `.env`.
- **Scraper**: Python script to parse event data. Must securely connect to the internal DB.
- **Frontend**: HTML/JS, Tailwind CSS, Google Maps API. Mobile-First, dark mode, deferred script loading. Protected by the custom Python authentication session.
- **Reverse Proxy & SSL**: Use Traefik to route traffic to the Python backend and automatically issue/renew Let's Encrypt SSL certificates via HTTP-01 challenge for `yvrr.kravchuk.net.ua`.

## 4. Development Workflow
Whenever the user asks to build a feature, create a file, or deploy:
1. Plan the necessary files (e.g., `docker-compose.yml`, `main.py`, `Dockerfile`, `.env.example`).
2. Use `ssh yvrr` to create/edit these files on the remote server in the project directory (`~/yvr-radar`), OR push changes via Git and pull them on the server.
3. Deploy or restart services using `ssh yvrr 'cd ~/yvr-radar && docker compose up -d --build'`.
4. Check logs if needed using `ssh yvrr 'cd ~/yvr-radar && docker compose logs'`.
5. **ALWAYS update the `CHANGELOG.md` file** to reflect any new features, fixes, or significant changes made during the session.
6. **Follow Cyber Security Best Practices** at all times (e.g., input validation, avoiding SQL injection, securing endpoints, using environment variables for secrets, enforcing rate limiting).
7. Commit and push changes to the GitHub repository.
