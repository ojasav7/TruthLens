# TruthLens — On-Premise Deployment Guide

## Quick Start (Docker)

```bash
# Clone and configure
cp .env.example .env
# Edit .env with your settings

# Start everything
docker-compose up --build -d

# Verify
curl http://localhost:8000/health
curl http://localhost:8501
```

## Production Configuration

### Environment Variables

```env
# Security
TL_SECRET_KEY=your-production-secret-key-min-32-chars
TL_ADMIN_API_KEY=your-admin-api-key
ENVIRONMENT=production

# Database (PostgreSQL recommended for production)
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/truthlens

# Models
MODEL_DIR=/opt/truthlens/models

# Retention
TL_RETENTION_MEDIA=1
TL_RETENTION_META=30
TL_RETENTION_REPORTS=30
TL_RETENTION_AUDIT=90

# Limits
TL_MAX_FILE_MB=100
TL_MAX_VIDEO_S=300
TL_MAX_AUDIO_S=300

# WhatsApp (optional)
TL_WHATSAPP_TOKEN=
TL_WHATSAPP_PHONE_ID=

# Telegram (optional)
TL_TELEGRAM_TOKEN=
```

### PostgreSQL Setup

```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Create database
sudo -u postgres createdb truthlens
sudo -u postgres createuser truthlens_user
sudo -u postgres psql -c "ALTER USER truthlens_user WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE truthlens TO truthlens_user;"

# Set DATABASE_URL
export DATABASE_URL="postgresql+asyncpg://truthlens_user:your_password@localhost:5432/truthlens"
```

### SSL/TLS (nginx)

```nginx
server {
    listen 443 ssl http2;
    server_name truthlens.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/truthlens.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/truthlens.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Systemd Service

```ini
[Unit]
Description=TruthLens API
After=network.target postgresql.service

[Service]
Type=simple
User=truthlens
WorkingDirectory=/opt/truthlens
ExecStart=/opt/truthlens/venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
Environment=ENVIRONMENT=production
EnvironmentFile=/opt/truthlens/.env

[Install]
WantedBy=multi-user.target
```

### Backup Strategy

```bash
# Database backup (daily)
pg_dump -U truthlens_user truthlens > /backups/truthlens_$(date +%Y%m%d).sql

# Retention cleanup (run via cron)
0 2 * * * /opt/truthlens/scripts/cleanup_retention.sh
```

### Monitoring

```bash
# Prometheus scrape config
scrape_configs:
  - job_name: 'truthlens'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/platform/metrics'
```

### Kubernetes

```bash
kubectl apply -f deploy/k8s/deployment.yaml
kubectl get pods -l app=truthlens
kubectl logs -l app=truthlens -f
```

### Air-Gapped Deployment

1. Build Docker image on internet-connected machine:
   ```bash
   docker-compose build
   docker save truthlens > truthlens.tar
   ```

2. Transfer `truthlens.tar` to air-gapped machine

3. Load and run:
   ```bash
   docker load < truthlens.tar
   docker-compose up -d
   ```

4. Models must be pre-downloaded in `models/` directory

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Detailed health
curl http://localhost:8000/nextgen/health/detailed

# Metrics
curl http://localhost:8000/platform/metrics

# Deployment info
curl http://localhost:8000/platform/deployment/info
```

### Log Management

```bash
# View logs
docker-compose logs -f backend

# Structured logs are output to stdout in JSON-like format
# Use with: ELK stack, Grafana Loki, or CloudWatch
```
