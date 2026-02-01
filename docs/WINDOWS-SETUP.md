# Windows Setup Guide

This guide covers multiple ways to run ClusterMark on Windows.

---

## Option 1: Docker Desktop (Recommended)

Docker Desktop is the easiest option if it works on your system.

### Installation

1. Download [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
2. Run the installer
3. **Important**: Enable WSL 2 backend when prompted (recommended)
4. Restart your computer

### Verify Installation

Open PowerShell and run:
```powershell
docker --version
docker-compose --version
```

### Run ClusterMark

```powershell
git clone https://github.com/yibeichan/clustermark.git
cd clustermark
docker-compose up --build
```

### Common Docker Desktop Issues

**"WSL 2 installation is incomplete"**
```powershell
# Run as Administrator
wsl --install
# Restart computer, then retry Docker Desktop
```

**"Hyper-V is not enabled"**
- Docker Desktop requires either WSL 2 or Hyper-V
- WSL 2 is recommended (lighter, better performance)
- Enable in: Settings → Apps → Optional Features → More Windows Features → Windows Subsystem for Linux

**"Docker daemon not running"**
- Open Docker Desktop application first
- Wait for it to fully start (whale icon in system tray stops animating)

**Docker Desktop won't install or crashes**
- Try Option 2 (Podman) or Option 3 (WSL2 + Docker) below

---

## Option 2: Podman (Docker Alternative)

Podman is a free, open-source Docker alternative that some find easier to install on Windows.

### Why Podman?

| Aspect | Docker Desktop | Podman |
|--------|---------------|--------|
| License | Paid for large companies | Free and open source |
| Architecture | Requires background daemon | Daemonless (lighter) |
| Admin rights | Required | Supports rootless mode |
| Hyper-V conflicts | Can conflict | Better compatibility |

### Installation

**Option A: Windows Installer**
1. Download from [github.com/containers/podman/releases](https://github.com/containers/podman/releases)
2. Download the `.exe` file (e.g., `podman-5.x.x-setup.exe`)
3. Run installer, follow prompts
4. Restart terminal

**Option B: Winget (Windows Package Manager)**
```powershell
winget install RedHat.Podman
```

**Option C: Chocolatey**
```powershell
choco install podman-desktop
```

### Post-Installation Setup

```powershell
# Initialize the Podman machine (creates a lightweight Linux VM)
podman machine init

# Start the machine
podman machine start

# Verify installation
podman --version
```

### Install Podman Compose

```powershell
pip install podman-compose
```

Or if you don't have Python:
```powershell
winget install Python.Python.3.11
pip install podman-compose
```

### Run ClusterMark with Podman

```powershell
git clone https://github.com/yibeichan/clustermark.git
cd clustermark

# Start all services
podman-compose up --build

# Stop services
podman-compose down

# Run migrations (if needed)
podman exec clustermark_backend_1 alembic upgrade head
```

### Common Podman Issues

**"podman machine is not running"**
```powershell
podman machine start
```

**"permission denied" on volumes**
```powershell
# Option A: Use rootful mode
podman machine stop
podman machine set --rootful
podman machine start

# Option B: Add :Z suffix (SELinux)
# Edit docker-compose.yml volumes to add :Z
```

**Slow first start**
- Normal - Podman downloads a minimal Linux VM on first run
- Subsequent starts are fast (~5-10 seconds)

**"podman-compose not found"**
```powershell
# Ensure Python Scripts are in PATH
python -m pip install podman-compose
python -m podman_compose up --build
```

---

## Option 3: WSL 2 + Docker Engine

Run Docker inside Windows Subsystem for Linux. More technical but very reliable.

### Step 1: Enable WSL 2

Open PowerShell as Administrator:
```powershell
# Enable WSL
wsl --install

# Set WSL 2 as default
wsl --set-default-version 2

# Restart computer
```

### Step 2: Install Ubuntu

```powershell
# Install Ubuntu (or your preferred distro)
wsl --install -d Ubuntu

# Launch Ubuntu and create your user account
wsl -d Ubuntu
```

### Step 3: Install Docker in WSL

Inside your Ubuntu terminal:
```bash
# Update packages
sudo apt update && sudo apt upgrade -y

# Install Docker
sudo apt install -y docker.io docker-compose

# Add your user to docker group (avoids sudo)
sudo usermod -aG docker $USER

# Start Docker service
sudo service docker start

# Exit and re-enter WSL for group changes to take effect
exit
```

### Step 4: Run ClusterMark

Re-enter WSL:
```powershell
wsl -d Ubuntu
```

Then:
```bash
# Clone repository
git clone https://github.com/yibeichan/clustermark.git
cd clustermark

# Start Docker service (needed each time you open WSL)
sudo service docker start

# Run ClusterMark
docker-compose up --build
```

### Access the App

Open your Windows browser and go to: **http://localhost:3000**

WSL 2 automatically forwards ports to Windows.

### Make Docker Auto-Start

Add to your `~/.bashrc`:
```bash
# Auto-start Docker
if service docker status 2>&1 | grep -q "is not running"; then
    sudo service docker start
fi
```

Then allow passwordless sudo for docker:
```bash
sudo visudo
# Add this line at the end:
# yourusername ALL=(ALL) NOPASSWD: /usr/sbin/service docker start
```

---

## Option 4: Run Without Docker (Advanced)

Run each service natively on Windows. Most complex but no virtualization needed.

### Prerequisites

1. **Python 3.11+**: Download from [python.org](https://www.python.org/downloads/)
2. **Node.js 18+**: Download from [nodejs.org](https://nodejs.org/)
3. **PostgreSQL 15+**: Download from [postgresql.org](https://www.postgresql.org/download/windows/)

### Setup PostgreSQL

1. Install PostgreSQL
2. Open pgAdmin or psql
3. Create database:
```sql
CREATE DATABASE clustermark;
CREATE USER clustermark WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE clustermark TO clustermark;
```

### Setup Backend

```powershell
cd backend

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Set environment variable
$env:DATABASE_URL = "postgresql://clustermark:password@localhost:5432/clustermark"

# Run migrations
alembic upgrade head

# Start backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Setup Frontend

Open a new terminal:
```powershell
cd frontend

# Install dependencies
npm install

# Start frontend
npm run dev
```

### Access the App

- Frontend: http://localhost:3000 (or the port Vite shows)
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Troubleshooting

### Line Ending Issues

If you see errors like `bad interpreter` or `/bin/bash^M`:

```powershell
# Fix line endings
git config core.autocrlf input
git add . --renormalize
git checkout -- .
```

Or re-clone the repository (cleanest fix).

### Port Already in Use

```powershell
# Find what's using the port
netstat -ano | findstr :3000
netstat -ano | findstr :8000

# Kill the process (replace PID with actual number)
taskkill /PID <PID> /F
```

Or change ports in `docker-compose.yml`:
```yaml
ports:
  - "3001:3000"  # Frontend on 3001
  - "8001:8000"  # Backend on 8001
```

### Firewall Blocking Connections

If you can't access localhost:
1. Open Windows Defender Firewall
2. Allow Docker Desktop / Podman through firewall
3. Or temporarily disable firewall for testing

### Performance Tips

- **Use WSL 2 file system**: Clone repos inside WSL (`/home/user/`) not Windows (`/mnt/c/`)
- **Allocate more memory**: Docker Desktop → Settings → Resources → Memory
- **Use SSD**: Docker containers run much faster on SSD

---

## Quick Comparison

| Method | Difficulty | Performance | Best For |
|--------|------------|-------------|----------|
| Docker Desktop | Easy | Good | Most users |
| Podman | Easy | Good | Docker licensing concerns |
| WSL 2 + Docker | Medium | Best | Developers, reliable setup |
| Native (no Docker) | Hard | Varies | Full control, no virtualization |

---

## Need Help?

- GitHub Issues: https://github.com/yibeichan/clustermark/issues
- Docker Documentation: https://docs.docker.com/desktop/windows/
- Podman Documentation: https://podman.io/docs
- WSL Documentation: https://docs.microsoft.com/en-us/windows/wsl/
