# 🚀 Deployment Guide

Complete guide for deploying the CSV Verification Dashboard to various platforms.

---

## 📦 GitHub Setup

### Initial Setup

1. **Create GitHub Repository**
```bash
# On GitHub.com:
# - Click "New Repository"
# - Name: csv-verification-dashboard
# - Description: CSV verification tool for Day Archive
# - Public or Private (your choice)
# - Don't initialize with README (we have one)
```

2. **Initialize Local Git**
```bash
cd csv-verification-dashboard
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/csv-verification-dashboard.git
git push -u origin main
```

3. **Set Up Secrets (Important!)**
- Go to repository Settings → Secrets and variables → Actions
- Add secret: `ANTHROPIC_API_KEY` (for CI/CD if needed)
- **Never commit API keys to the repository!**

---

## 🌐 Streamlit Cloud Deployment

### Prerequisites
- GitHub repository created
- Streamlit Cloud account (free at [streamlit.io/cloud](https://streamlit.io/cloud))

### Steps

1. **Log into Streamlit Cloud**
- Go to [share.streamlit.io](https://share.streamlit.io)
- Sign in with GitHub

2. **Deploy New App**
- Click "New app"
- Repository: `YOUR_USERNAME/csv-verification-dashboard`
- Branch: `main`
- Main file path: `csv_verification_dashboard.py`

3. **Configure Secrets**
- Click "Advanced settings"
- Add secrets (optional - users will enter API keys themselves):
```toml
# .streamlit/secrets.toml format (if needed)
# Note: Not recommended for this app since users enter their own keys
```

4. **Deploy**
- Click "Deploy!"
- Wait 2-3 minutes
- Your app will be live at `https://YOUR_USERNAME-csv-verification.streamlit.app`

### Custom Domain (Optional)
- Streamlit Cloud doesn't support custom domains on free tier
- Use Streamlit for Teams ($250/month) for custom domains

---

## 🐳 Docker Deployment

### Create Dockerfile

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "csv_verification_dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Create docker-compose.yml

```yaml
version: '3.8'

services:
  csv-verification:
    build: .
    ports:
      - "8501:8501"
    environment:
      - STREAMLIT_SERVER_HEADLESS=true
      - STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
    restart: unless-stopped
```

### Build and Run

```bash
# Build image
docker build -t csv-verification-dashboard .

# Run container
docker run -p 8501:8501 csv-verification-dashboard

# Or use docker-compose
docker-compose up -d
```

### Deploy to Production

```bash
# Tag for production
docker tag csv-verification-dashboard:latest YOUR_REGISTRY/csv-verification:v1.0.0

# Push to registry
docker push YOUR_REGISTRY/csv-verification:v1.0.0

# Pull and run on production server
docker pull YOUR_REGISTRY/csv-verification:v1.0.0
docker run -d -p 8501:8501 YOUR_REGISTRY/csv-verification:v1.0.0
```

---

## ☁️ AWS Deployment

### Option 1: AWS EC2

1. **Launch EC2 Instance**
- Ubuntu 22.04 LTS
- t2.micro (free tier) or t2.small
- Security group: Allow port 8501

2. **SSH into Instance**
```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
```

3. **Install Dependencies**
```bash
sudo apt update
sudo apt install python3-pip git -y
```

4. **Clone Repository**
```bash
git clone https://github.com/YOUR_USERNAME/csv-verification-dashboard.git
cd csv-verification-dashboard
```

5. **Install Python Packages**
```bash
pip3 install -r requirements.txt
```

6. **Run with Screen (keeps running after logout)**
```bash
screen -S streamlit
streamlit run csv_verification_dashboard.py --server.port=8501 --server.address=0.0.0.0
# Press Ctrl+A then D to detach
```

7. **Access Dashboard**
- Open browser: `http://your-ec2-ip:8501`

### Option 2: AWS Elastic Beanstalk

1. **Install EB CLI**
```bash
pip install awsebcli
```

2. **Initialize EB**
```bash
eb init -p python-3.11 csv-verification-dashboard
```

3. **Create Application**
```bash
eb create csv-verification-env
```

4. **Deploy Updates**
```bash
eb deploy
```

5. **Open Application**
```bash
eb open
```

---

## 🔷 Azure Deployment

### Azure App Service

1. **Install Azure CLI**
```bash
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

2. **Login to Azure**
```bash
az login
```

3. **Create Resource Group**
```bash
az group create --name csv-verification-rg --location eastus
```

4. **Create App Service Plan**
```bash
az appservice plan create --name csv-verification-plan --resource-group csv-verification-rg --sku B1 --is-linux
```

5. **Create Web App**
```bash
az webapp create --resource-group csv-verification-rg --plan csv-verification-plan --name csv-verification-app --runtime "PYTHON:3.11"
```

6. **Deploy from GitHub**
```bash
az webapp deployment source config --name csv-verification-app --resource-group csv-verification-rg --repo-url https://github.com/YOUR_USERNAME/csv-verification-dashboard --branch main --manual-integration
```

7. **Configure Startup Command**
```bash
az webapp config set --resource-group csv-verification-rg --name csv-verification-app --startup-file "streamlit run csv_verification_dashboard.py --server.port=8000"
```

---

## 🌊 Digital Ocean Deployment

### App Platform

1. **Create New App**
- Go to [DigitalOcean App Platform](https://cloud.digitalocean.com/apps)
- Click "Create App"
- Select GitHub repository

2. **Configure Build**
- Build Command: `pip install -r requirements.txt`
- Run Command: `streamlit run csv_verification_dashboard.py --server.port=8080`

3. **Set Environment Variables**
```
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
```

4. **Deploy**
- Click "Next" → "Create Resources"
- Wait 5-10 minutes
- App live at: `https://your-app.ondigitalocean.app`

---

## 🖥️ Local Network Deployment

### For Internal Company Use

1. **Find Your Local IP**
```bash
# Linux/Mac
ifconfig | grep "inet "

# Windows
ipconfig
```

2. **Run Streamlit on Network**
```bash
streamlit run csv_verification_dashboard.py --server.address=0.0.0.0 --server.port=8501
```

3. **Access from Other Computers**
- Open browser on any computer on same network
- Navigate to: `http://YOUR_LOCAL_IP:8501`

### Make it Auto-Start (Linux)

Create systemd service file `/etc/systemd/system/csv-verification.service`:
```ini
[Unit]
Description=CSV Verification Dashboard
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/csv-verification-dashboard
ExecStart=/usr/bin/streamlit run csv_verification_dashboard.py --server.port=8501 --server.address=0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable csv-verification
sudo systemctl start csv-verification
```

---

## 🔐 Production Security Checklist

Before deploying to production:

- [ ] API keys stored securely (not in code)
- [ ] HTTPS enabled (use reverse proxy like Nginx)
- [ ] Firewall configured
- [ ] Regular backups enabled
- [ ] Monitoring set up
- [ ] Error tracking configured
- [ ] Rate limiting implemented
- [ ] Access logs enabled
- [ ] Security headers configured
- [ ] Dependencies up to date

---

## 📊 Monitoring

### Basic Health Check

Add to your deployment:
```python
# Health check endpoint
@st.cache_data
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
```

### Recommended Tools

- **Uptime Monitoring:** UptimeRobot, Pingdom
- **Error Tracking:** Sentry
- **Analytics:** Google Analytics, Plausible
- **Logs:** CloudWatch (AWS), Stackdriver (GCP), Azure Monitor

---

## 🔄 CI/CD Setup

### GitHub Actions

Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run tests (if you have any)
        run: |
          # pytest tests/
          echo "No tests yet"
      
      - name: Deploy to Streamlit Cloud
        run: |
          # Streamlit Cloud auto-deploys from GitHub
          echo "Deployment triggered"
```

---

## 💰 Cost Estimates

### Streamlit Cloud
- **Free:** 1 app, community support
- **Team:** $250/month, 3 apps, custom domains

### AWS EC2
- **t2.micro:** $0-8/month (free tier)
- **t2.small:** ~$17/month

### Digital Ocean
- **Basic App:** $5/month
- **Professional:** $12/month

### Azure
- **B1 Plan:** ~$13/month

### Self-Hosted
- **VPS:** $5-10/month (Linode, Vultr, etc.)

---

## 🆘 Troubleshooting Deployment

### App won't start
- Check Python version (needs 3.8+)
- Verify requirements.txt has correct versions
- Check port is not in use

### Can't access externally
- Check firewall rules
- Verify port is open
- Confirm server address is 0.0.0.0

### Slow performance
- Increase instance size
- Enable caching in Streamlit
- Optimize verification logic

### Out of memory
- Reduce max_tokens in API calls
- Process smaller batches
- Increase server RAM

---

**Choose the deployment method that fits your needs and budget!**
