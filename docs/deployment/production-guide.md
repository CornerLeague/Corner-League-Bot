# Production Deployment Guide

This guide covers deploying the Sports Media Platform to production environments with enterprise-grade reliability, security, and performance.

## 🎯 Deployment Overview

The Sports Media Platform is designed for cloud-native deployment with support for:

- **Container Orchestration**: Docker Compose, Kubernetes, Docker Swarm
- **Cloud Providers**: AWS, Google Cloud, Azure, DigitalOcean
- **Database**: PostgreSQL with read replicas and connection pooling
- **Caching**: Redis Cluster for high availability
- **Search**: OpenSearch for advanced search capabilities
- **Monitoring**: Prometheus, Grafana, and comprehensive logging

## 🏗️ Infrastructure Requirements

### Minimum Production Requirements

**API Servers (2+ instances):**
- **CPU**: 4 vCPUs per instance
- **Memory**: 8GB RAM per instance
- **Storage**: 50GB SSD
- **Network**: 1Gbps bandwidth

**Background Workers (2+ instances):**
- **CPU**: 2 vCPUs per instance
- **Memory**: 4GB RAM per instance
- **Storage**: 20GB SSD
- **Network**: 500Mbps bandwidth

**Database (PostgreSQL):**
- **CPU**: 8 vCPUs (primary), 4 vCPUs (replicas)
- **Memory**: 32GB RAM (primary), 16GB RAM (replicas)
- **Storage**: 500GB SSD with 3000+ IOPS
- **Network**: 10Gbps bandwidth

**Cache (Redis Cluster):**
- **CPU**: 2 vCPUs per node
- **Memory**: 8GB RAM per node
- **Storage**: 50GB SSD per node
- **Nodes**: 3 master + 3 replica minimum

**Search (OpenSearch - Optional):**
- **CPU**: 4 vCPUs per node
- **Memory**: 16GB RAM per node
- **Storage**: 200GB SSD per node
- **Nodes**: 3 node cluster minimum

### Recommended Production Setup

For 10,000+ concurrent users:

**Load Balancer:**
- Application Load Balancer (ALB) or NGINX
- SSL termination and HTTP/2 support
- Health checks and automatic failover

**API Tier:**
- 4+ API server instances
- Auto-scaling based on CPU (target: 70%)
- Container orchestration (Kubernetes recommended)

**Worker Tier:**
- 6+ background worker instances
- Queue-based auto-scaling
- Separate worker types for different tasks

**Data Tier:**
- PostgreSQL primary with 2+ read replicas
- Redis Cluster with 6+ nodes (3 master, 3 replica)
- OpenSearch cluster with 3+ nodes
- Automated backups and point-in-time recovery

## 🐳 Docker Deployment

### Docker Compose Production Setup

1. **Create production Docker Compose file:**

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  # Load Balancer
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./infra/nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./infra/nginx/ssl:/etc/nginx/ssl
    depends_on:
      - api-1
      - api-2
    restart: unless-stopped

  # API Servers
  api-1:
    image: sports-media-api:latest
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres-primary:5432/sports_media
      - REDIS_URL=redis://redis-cluster:6379/0
      - API_WORKERS=4
    depends_on:
      - postgres-primary
      - redis-cluster
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  api-2:
    image: sports-media-api:latest
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres-primary:5432/sports_media
      - REDIS_URL=redis://redis-cluster:6379/0
      - API_WORKERS=4
    depends_on:
      - postgres-primary
      - redis-cluster
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Background Workers
  crawler-worker-1:
    image: sports-media-worker:latest
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres-primary:5432/sports_media
      - REDIS_URL=redis://redis-cluster:6379/0
      - WORKER_ID=crawler-1
      - WORKER_TYPE=crawler
    depends_on:
      - postgres-primary
      - redis-cluster
    restart: unless-stopped

  crawler-worker-2:
    image: sports-media-worker:latest
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres-primary:5432/sports_media
      - REDIS_URL=redis://redis-cluster:6379/0
      - WORKER_ID=crawler-2
      - WORKER_TYPE=crawler
    depends_on:
      - postgres-primary
      - redis-cluster
    restart: unless-stopped

  # Database
  postgres-primary:
    image: postgres:15
    environment:
      - POSTGRES_DB=sports_media
      - POSTGRES_USER=sports_user
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_INITDB_ARGS=--auth-host=scram-sha-256
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./infra/postgres/postgresql.conf:/etc/postgresql/postgresql.conf
    command: postgres -c config_file=/etc/postgresql/postgresql.conf
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U sports_user -d sports_media"]
      interval: 10s
      timeout: 5s
      retries: 5

  postgres-replica:
    image: postgres:15
    environment:
      - POSTGRES_DB=sports_media
      - POSTGRES_USER=sports_user
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - PGUSER=sports_user
    volumes:
      - postgres_replica_data:/var/lib/postgresql/data
    command: |
      bash -c "
      until pg_basebackup --pgdata=/var/lib/postgresql/data -R --slot=replica1 --host=postgres-primary --port=5432
      do
        echo 'Waiting for primary to connect...'
        sleep 1s
      done
      echo 'Backup done, starting replica...'
      chmod 0700 /var/lib/postgresql/data
      postgres
      "
    depends_on:
      - postgres-primary
    restart: unless-stopped

  # Redis Cluster
  redis-cluster:
    image: redis:7-alpine
    command: redis-server --cluster-enabled yes --cluster-config-file nodes.conf --cluster-node-timeout 5000 --appendonly yes
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  # OpenSearch
  opensearch:
    image: opensearchproject/opensearch:2.11.0
    environment:
      - cluster.name=sports-media-cluster
      - node.name=opensearch-node1
      - discovery.seed_hosts=opensearch-node1
      - cluster.initial_cluster_manager_nodes=opensearch-node1
      - bootstrap.memory_lock=true
      - "OPENSEARCH_JAVA_OPTS=-Xms2g -Xmx2g"
      - "DISABLE_INSTALL_DEMO_CONFIG=true"
      - "DISABLE_SECURITY_PLUGIN=true"
    ulimits:
      memlock:
        soft: -1
        hard: -1
      nofile:
        soft: 65536
        hard: 65536
    volumes:
      - opensearch_data:/usr/share/opensearch/data
    restart: unless-stopped

  # Frontend
  frontend:
    image: sports-media-frontend:latest
    environment:
      - REACT_APP_API_URL=https://api.yourdomain.com
    restart: unless-stopped

  # Monitoring
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./infra/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./infra/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./infra/grafana/datasources:/etc/grafana/provisioning/datasources
    restart: unless-stopped

volumes:
  postgres_data:
  postgres_replica_data:
  redis_data:
  opensearch_data:
  prometheus_data:
  grafana_data:

networks:
  default:
    driver: bridge
```

2. **Deploy the stack:**

```bash
# Set environment variables
export POSTGRES_PASSWORD=your-secure-password
export GRAFANA_PASSWORD=your-grafana-password

# Deploy
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps
```

### Building Production Images

```bash
# Build API image
docker build -t sports-media-api:latest -f infra/docker/Dockerfile.api .

# Build worker image
docker build -t sports-media-worker:latest -f infra/docker/Dockerfile.worker .

# Build frontend image
docker build -t sports-media-frontend:latest -f infra/docker/Dockerfile.frontend ./frontend

# Tag for registry
docker tag sports-media-api:latest your-registry.com/sports-media-api:v1.0.0
docker tag sports-media-worker:latest your-registry.com/sports-media-worker:v1.0.0
docker tag sports-media-frontend:latest your-registry.com/sports-media-frontend:v1.0.0

# Push to registry
docker push your-registry.com/sports-media-api:v1.0.0
docker push your-registry.com/sports-media-worker:v1.0.0
docker push your-registry.com/sports-media-frontend:v1.0.0
```

## ☸️ Kubernetes Deployment

### Kubernetes Manifests

1. **Namespace and ConfigMap:**

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: sports-media

---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: sports-media-config
  namespace: sports-media
data:
  DATABASE_POOL_SIZE: "20"
  REDIS_POOL_SIZE: "10"
  API_WORKERS: "4"
  LOG_LEVEL: "INFO"
  ENABLE_AI_SUMMARIZATION: "true"
  ENABLE_TRENDING_DETECTION: "true"
```

2. **Secrets:**

```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: sports-media-secrets
  namespace: sports-media
type: Opaque
data:
  DATABASE_URL: <base64-encoded-database-url>
  REDIS_URL: <base64-encoded-redis-url>
  SECRET_KEY: <base64-encoded-secret-key>
  DEEPSEEK_API_KEY: <base64-encoded-deepseek-key>
  EVOMI_API_KEY: <base64-encoded-evomi-key>
```

3. **API Deployment:**

```yaml
# k8s/api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sports-media-api
  namespace: sports-media
spec:
  replicas: 4
  selector:
    matchLabels:
      app: sports-media-api
  template:
    metadata:
      labels:
        app: sports-media-api
    spec:
      containers:
      - name: api
        image: your-registry.com/sports-media-api:v1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: sports-media-secrets
              key: DATABASE_URL
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: sports-media-secrets
              key: REDIS_URL
        envFrom:
        - configMapRef:
            name: sports-media-config
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: sports-media-api-service
  namespace: sports-media
spec:
  selector:
    app: sports-media-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
```

4. **Worker Deployment:**

```yaml
# k8s/worker-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sports-media-worker
  namespace: sports-media
spec:
  replicas: 6
  selector:
    matchLabels:
      app: sports-media-worker
  template:
    metadata:
      labels:
        app: sports-media-worker
    spec:
      containers:
      - name: worker
        image: your-registry.com/sports-media-worker:v1.0.0
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: sports-media-secrets
              key: DATABASE_URL
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: sports-media-secrets
              key: REDIS_URL
        - name: WORKER_ID
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        envFrom:
        - configMapRef:
            name: sports-media-config
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
```

5. **Ingress Controller:**

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: sports-media-ingress
  namespace: sports-media
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
spec:
  tls:
  - hosts:
    - api.yourdomain.com
    - app.yourdomain.com
    secretName: sports-media-tls
  rules:
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: sports-media-api-service
            port:
              number: 80
  - host: app.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: sports-media-frontend-service
            port:
              number: 80
```

### Deploy to Kubernetes

```bash
# Apply all manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n sports-media
kubectl get services -n sports-media
kubectl get ingress -n sports-media

# View logs
kubectl logs -f deployment/sports-media-api -n sports-media
kubectl logs -f deployment/sports-media-worker -n sports-media

# Scale deployments
kubectl scale deployment sports-media-api --replicas=8 -n sports-media
kubectl scale deployment sports-media-worker --replicas=12 -n sports-media
```

## 🌐 Cloud Provider Deployment

### AWS Deployment

**Using AWS EKS:**

1. **Create EKS cluster:**

```bash
# Install eksctl
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin

# Create cluster
eksctl create cluster \
  --name sports-media-cluster \
  --version 1.28 \
  --region us-west-2 \
  --nodegroup-name standard-workers \
  --node-type m5.xlarge \
  --nodes 3 \
  --nodes-min 1 \
  --nodes-max 10 \
  --managed
```

2. **Set up RDS PostgreSQL:**

```bash
# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier sports-media-db \
  --db-instance-class db.r5.2xlarge \
  --engine postgres \
  --engine-version 15.4 \
  --master-username sports_user \
  --master-user-password YourSecurePassword \
  --allocated-storage 500 \
  --storage-type gp3 \
  --storage-encrypted \
  --vpc-security-group-ids sg-xxxxxxxxx \
  --db-subnet-group-name sports-media-subnet-group \
  --backup-retention-period 7 \
  --multi-az \
  --deletion-protection
```

3. **Set up ElastiCache Redis:**

```bash
# Create Redis cluster
aws elasticache create-replication-group \
  --replication-group-id sports-media-redis \
  --description "Sports Media Redis Cluster" \
  --num-cache-clusters 3 \
  --cache-node-type cache.r6g.xlarge \
  --engine redis \
  --engine-version 7.0 \
  --port 6379 \
  --security-group-ids sg-xxxxxxxxx \
  --subnet-group-name sports-media-cache-subnet-group \
  --at-rest-encryption-enabled \
  --transit-encryption-enabled
```

4. **Set up OpenSearch:**

```bash
# Create OpenSearch domain
aws opensearch create-domain \
  --domain-name sports-media-search \
  --elasticsearch-version OpenSearch_2.3 \
  --elasticsearch-cluster-config InstanceType=r6g.large.search,InstanceCount=3,DedicatedMasterEnabled=true,MasterInstanceType=r6g.medium.search,MasterInstanceCount=3 \
  --ebs-options EBSEnabled=true,VolumeType=gp3,VolumeSize=100 \
  --vpc-options SecurityGroupIds=sg-xxxxxxxxx,SubnetIds=subnet-xxxxxxxxx,subnet-yyyyyyyyy \
  --encryption-at-rest-options Enabled=true \
  --node-to-node-encryption-options Enabled=true \
  --domain-endpoint-options EnforceHTTPS=true
```

### Google Cloud Deployment

**Using GKE:**

1. **Create GKE cluster:**

```bash
# Create cluster
gcloud container clusters create sports-media-cluster \
  --zone us-central1-a \
  --machine-type n1-standard-4 \
  --num-nodes 3 \
  --enable-autoscaling \
  --min-nodes 1 \
  --max-nodes 10 \
  --enable-autorepair \
  --enable-autoupgrade
```

2. **Set up Cloud SQL:**

```bash
# Create PostgreSQL instance
gcloud sql instances create sports-media-db \
  --database-version POSTGRES_15 \
  --tier db-custom-8-32768 \
  --region us-central1 \
  --storage-size 500GB \
  --storage-type SSD \
  --backup-start-time 03:00 \
  --enable-bin-log \
  --maintenance-window-day SUN \
  --maintenance-window-hour 04
```

3. **Set up Memorystore Redis:**

```bash
# Create Redis instance
gcloud redis instances create sports-media-redis \
  --size 16 \
  --region us-central1 \
  --redis-version redis_7_0 \
  --tier standard
```

## 🔒 Security Configuration

### SSL/TLS Setup

1. **Generate SSL certificates:**

```bash
# Using Let's Encrypt with Certbot
sudo apt install certbot python3-certbot-nginx

# Generate certificates
sudo certbot --nginx -d api.yourdomain.com -d app.yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

2. **Configure NGINX SSL:**

```nginx
# /etc/nginx/sites-available/sports-media
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    location / {
        proxy_pass http://api-backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

upstream api-backend {
    least_conn;
    server api-1:8000 max_fails=3 fail_timeout=30s;
    server api-2:8000 max_fails=3 fail_timeout=30s;
    server api-3:8000 max_fails=3 fail_timeout=30s;
    server api-4:8000 max_fails=3 fail_timeout=30s;
}
```

### Firewall Configuration

```bash
# UFW firewall rules
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Application-specific rules
sudo ufw allow from 10.0.0.0/8 to any port 5432  # PostgreSQL
sudo ufw allow from 10.0.0.0/8 to any port 6379  # Redis
sudo ufw allow from 10.0.0.0/8 to any port 9200  # OpenSearch
```

### Database Security

```sql
-- Create application user with limited privileges
CREATE USER sports_app WITH PASSWORD 'secure_password';

-- Grant necessary permissions
GRANT CONNECT ON DATABASE sports_media TO sports_app;
GRANT USAGE ON SCHEMA public TO sports_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO sports_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO sports_app;

-- Create read-only user for analytics
CREATE USER sports_readonly WITH PASSWORD 'readonly_password';
GRANT CONNECT ON DATABASE sports_media TO sports_readonly;
GRANT USAGE ON SCHEMA public TO sports_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO sports_readonly;
```

## 📊 Monitoring Setup

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "sports_media_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'sports-media-api'
    static_configs:
      - targets: ['api-1:8000', 'api-2:8000', 'api-3:8000', 'api-4:8000']
    metrics_path: /metrics
    scrape_interval: 10s

  - job_name: 'sports-media-workers'
    static_configs:
      - targets: ['worker-1:9090', 'worker-2:9090', 'worker-3:9090']
    metrics_path: /metrics
    scrape_interval: 30s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']
```

### Alerting Rules

```yaml
# sports_media_rules.yml
groups:
  - name: sports_media_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ $value }}s"

      - alert: DatabaseConnectionsHigh
        expr: pg_stat_database_numbackends > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High database connection count"
          description: "Database has {{ $value }} active connections"

      - alert: WorkerDown
        expr: up{job="sports-media-workers"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Worker instance down"
          description: "Worker {{ $labels.instance }} is down"

      - alert: RedisMemoryHigh
        expr: redis_memory_used_bytes / redis_memory_max_bytes > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Redis memory usage high"
          description: "Redis memory usage is {{ $value | humanizePercentage }}"
```

### Grafana Dashboards

Import the provided dashboard JSON files:

- **API Performance Dashboard**: Request rates, response times, error rates
- **Database Dashboard**: Connection pools, query performance, replication lag
- **Worker Dashboard**: Job processing rates, queue depths, error rates
- **Infrastructure Dashboard**: CPU, memory, disk, network metrics

## 🔄 Backup and Recovery

### Database Backups

```bash
#!/bin/bash
# backup_database.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/postgres"
DB_NAME="sports_media"
DB_USER="sports_user"
DB_HOST="postgres-primary"

# Create backup directory
mkdir -p $BACKUP_DIR

# Full database backup
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME -F c -b -v -f "$BACKUP_DIR/sports_media_$DATE.backup"

# Compress backup
gzip "$BACKUP_DIR/sports_media_$DATE.backup"

# Upload to S3 (optional)
aws s3 cp "$BACKUP_DIR/sports_media_$DATE.backup.gz" s3://your-backup-bucket/postgres/

# Clean up old backups (keep 7 days)
find $BACKUP_DIR -name "*.backup.gz" -mtime +7 -delete

echo "Backup completed: sports_media_$DATE.backup.gz"
```

### Redis Backups

```bash
#!/bin/bash
# backup_redis.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/redis"
REDIS_HOST="redis-cluster"
REDIS_PORT="6379"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create Redis backup
redis-cli -h $REDIS_HOST -p $REDIS_PORT --rdb "$BACKUP_DIR/redis_$DATE.rdb"

# Compress backup
gzip "$BACKUP_DIR/redis_$DATE.rdb"

# Upload to S3 (optional)
aws s3 cp "$BACKUP_DIR/redis_$DATE.rdb.gz" s3://your-backup-bucket/redis/

# Clean up old backups (keep 3 days)
find $BACKUP_DIR -name "*.rdb.gz" -mtime +3 -delete

echo "Redis backup completed: redis_$DATE.rdb.gz"
```

### Automated Backup Schedule

```bash
# Add to crontab
crontab -e

# Database backup every 6 hours
0 */6 * * * /scripts/backup_database.sh >> /var/log/backup_db.log 2>&1

# Redis backup every 2 hours
0 */2 * * * /scripts/backup_redis.sh >> /var/log/backup_redis.log 2>&1

# Weekly full system backup
0 2 * * 0 /scripts/backup_full_system.sh >> /var/log/backup_full.log 2>&1
```

## 🚀 Performance Optimization

### Database Optimization

```sql
-- PostgreSQL configuration optimizations
-- Add to postgresql.conf

# Memory settings
shared_buffers = 8GB                    # 25% of total RAM
effective_cache_size = 24GB             # 75% of total RAM
work_mem = 256MB                        # For complex queries
maintenance_work_mem = 2GB              # For maintenance operations

# Connection settings
max_connections = 200                   # Adjust based on load
max_prepared_transactions = 200

# Checkpoint settings
checkpoint_completion_target = 0.9
wal_buffers = 64MB
checkpoint_timeout = 15min

# Query planner settings
random_page_cost = 1.1                  # For SSD storage
effective_io_concurrency = 200          # For SSD storage

# Logging settings
log_min_duration_statement = 1000       # Log slow queries
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on

# Replication settings (for primary)
wal_level = replica
max_wal_senders = 3
wal_keep_size = 1GB
```

### Redis Optimization

```bash
# Redis configuration optimizations
# Add to redis.conf

# Memory settings
maxmemory 6gb
maxmemory-policy allkeys-lru

# Persistence settings
save 900 1
save 300 10
save 60 10000

# Network settings
tcp-keepalive 300
timeout 0

# Performance settings
tcp-backlog 511
databases 16

# Cluster settings (if using Redis Cluster)
cluster-enabled yes
cluster-config-file nodes.conf
cluster-node-timeout 5000
cluster-announce-ip 10.0.0.1
cluster-announce-port 6379
cluster-announce-bus-port 16379
```

### Application Optimization

```python
# API server optimization settings
# In your FastAPI app configuration

from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Sports Media API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Connection pool settings
DATABASE_POOL_SIZE = 20
DATABASE_MAX_OVERFLOW = 30
DATABASE_POOL_TIMEOUT = 30
DATABASE_POOL_RECYCLE = 3600

# Redis connection pool
REDIS_POOL_SIZE = 10
REDIS_POOL_TIMEOUT = 5

# Worker settings
WORKER_CONCURRENCY = 4
WORKER_MAX_TASKS_PER_CHILD = 1000
WORKER_PREFETCH_MULTIPLIER = 4
```

## 📈 Scaling Guidelines

### Horizontal Scaling

**API Servers:**
```bash
# Scale based on CPU usage (target: 70%)
kubectl autoscale deployment sports-media-api --cpu-percent=70 --min=4 --max=20

# Scale based on custom metrics (requests per second)
kubectl apply -f - <<EOF
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: sports-media-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: sports-media-api
  minReplicas: 4
  maxReplicas: 20
  metrics:
  - type: Pods
    pods:
      metric:
        name: requests_per_second
      target:
        type: AverageValue
        averageValue: "100"
EOF
```

**Background Workers:**
```bash
# Scale workers based on queue depth
kubectl autoscale deployment sports-media-worker --cpu-percent=80 --min=6 --max=50

# Custom scaling based on Redis queue length
kubectl apply -f - <<EOF
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: sports-media-worker-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: sports-media-worker
  minReplicas: 6
  maxReplicas: 50
  metrics:
  - type: External
    external:
      metric:
        name: redis_queue_length
      target:
        type: AverageValue
        averageValue: "100"
EOF
```

### Vertical Scaling

**Database Scaling:**
```bash
# AWS RDS scaling
aws rds modify-db-instance \
  --db-instance-identifier sports-media-db \
  --db-instance-class db.r5.4xlarge \
  --apply-immediately

# Add read replicas
aws rds create-db-instance-read-replica \
  --db-instance-identifier sports-media-db-replica-2 \
  --source-db-instance-identifier sports-media-db \
  --db-instance-class db.r5.2xlarge
```

**Redis Scaling:**
```bash
# ElastiCache scaling
aws elasticache modify-replication-group \
  --replication-group-id sports-media-redis \
  --cache-node-type cache.r6g.2xlarge \
  --apply-immediately

# Add more nodes
aws elasticache increase-replica-count \
  --replication-group-id sports-media-redis \
  --new-replica-count 5 \
  --apply-immediately
```

## 🔧 Troubleshooting

### Common Issues

**High Database Connection Count:**
```sql
-- Check active connections
SELECT count(*) FROM pg_stat_activity WHERE state = 'active';

-- Kill long-running queries
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'active' 
AND query_start < NOW() - INTERVAL '5 minutes';

-- Optimize connection pooling
-- Increase pool size or add connection pooler (PgBouncer)
```

**Redis Memory Issues:**
```bash
# Check Redis memory usage
redis-cli info memory

# Clear expired keys
redis-cli --scan --pattern "expired:*" | xargs redis-cli del

# Analyze memory usage by key pattern
redis-cli --bigkeys

# Configure memory policy
redis-cli config set maxmemory-policy allkeys-lru
```

**Worker Performance Issues:**
```bash
# Check worker status
kubectl logs -f deployment/sports-media-worker

# Monitor queue depths
redis-cli llen crawler_queue
redis-cli llen extraction_queue
redis-cli llen summarization_queue

# Scale workers if needed
kubectl scale deployment sports-media-worker --replicas=12
```

### Performance Debugging

**API Response Time Issues:**
```bash
# Check API metrics
curl -s http://api.yourdomain.com/metrics | grep http_request_duration

# Profile slow endpoints
curl -w "@curl-format.txt" -o /dev/null -s "http://api.yourdomain.com/api/v1/search?q=test"

# Check database query performance
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
```

**Database Performance Issues:**
```sql
-- Check slow queries
SELECT query, mean_time, calls, total_time
FROM pg_stat_statements 
WHERE mean_time > 1000 
ORDER BY mean_time DESC;

-- Check index usage
SELECT schemaname, tablename, attname, n_distinct, correlation 
FROM pg_stats 
WHERE tablename = 'content_items';

-- Analyze table statistics
ANALYZE content_items;
```

### Log Analysis

**Centralized Logging with ELK Stack:**
```yaml
# filebeat.yml
filebeat.inputs:
- type: container
  paths:
    - '/var/lib/docker/containers/*/*.log'
  processors:
  - add_kubernetes_metadata:
      host: ${NODE_NAME}
      matchers:
      - logs_path:
          logs_path: "/var/lib/docker/containers/"

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  index: "sports-media-logs-%{+yyyy.MM.dd}"

setup.template.name: "sports-media"
setup.template.pattern: "sports-media-*"
```

**Log Queries:**
```bash
# Search for errors in the last hour
curl -X GET "elasticsearch:9200/sports-media-logs-*/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        {"match": {"level": "ERROR"}},
        {"range": {"@timestamp": {"gte": "now-1h"}}}
      ]
    }
  }
}'

# Search for slow API requests
curl -X GET "elasticsearch:9200/sports-media-logs-*/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        {"match": {"logger": "api"}},
        {"range": {"response_time_ms": {"gte": 1000}}}
      ]
    }
  }
}'
```

## 📋 Deployment Checklist

### Pre-Deployment

- [ ] **Infrastructure provisioned** (servers, databases, load balancers)
- [ ] **SSL certificates** generated and configured
- [ ] **DNS records** configured (A, CNAME, MX if needed)
- [ ] **Firewall rules** configured and tested
- [ ] **Monitoring** and alerting set up
- [ ] **Backup systems** configured and tested
- [ ] **CI/CD pipeline** configured
- [ ] **Environment variables** and secrets configured
- [ ] **Database migrations** tested
- [ ] **Load testing** completed
- [ ] **Security scanning** completed

### Deployment

- [ ] **Database migrations** applied
- [ ] **Static assets** deployed to CDN
- [ ] **Application containers** deployed
- [ ] **Health checks** passing
- [ ] **Load balancer** configured and tested
- [ ] **SSL/TLS** working correctly
- [ ] **Monitoring** collecting metrics
- [ ] **Logs** being collected and indexed
- [ ] **Backup jobs** scheduled and tested

### Post-Deployment

- [ ] **Smoke tests** passed
- [ ] **Performance tests** passed
- [ ] **Security tests** passed
- [ ] **Monitoring alerts** configured
- [ ] **Documentation** updated
- [ ] **Team notifications** sent
- [ ] **Rollback plan** documented and tested
- [ ] **Post-mortem** scheduled (if issues occurred)

---

This production deployment guide provides comprehensive instructions for deploying the Sports Media Platform with enterprise-grade reliability, security, and performance. Follow the guidelines appropriate for your infrastructure and scale requirements.

