# Corner League Bot

A production-ready, AI-powered sports media discovery and personalization platform that aggregates, analyzes, and summarizes sports content from across the web.

## 🏆 Overview

Corner League Bot is an enterprise-grade system that provides personalized sports news feeds through intelligent web-scale content discovery, AI-powered summarization, and sophisticated ranking algorithms. Built for scalability and reliability, it can handle 10,000+ concurrent users with sub-100ms search response times.

### Key Features

- **🌐 Web-Scale Content Discovery**: Comprehensive crawling across RSS feeds, sitemaps, and search APIs
- **🤖 AI-Powered Summarization**: DeepSeek AI integration with sports-specific content analysis
- **🔍 Advanced Search & Ranking**: Multi-signal BM25-based ranking with personalization
- **📊 Real-Time Trending Detection**: Burst detection with automatic query generation
- **🛡️ Enterprise Security**: JWT/RBAC authentication, API keys, and comprehensive security headers
- **📈 Production Monitoring**: Comprehensive metrics, health checks, and chaos engineering
- **⚡ High Performance**: Sub-100ms search, intelligent caching, and horizontal scaling

## 🏗️ Architecture

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Gateway   │    │   Background    │
│   (React/TS)    │◄──►│   (FastAPI)     │◄──►│   Workers       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └──────────────►│   Load Balancer │◄─────────────┘
                        └─────────────────┘
                                 │
                    ┌─────────────────────────────┐
                    │        Core Services        │
                    ├─────────────────────────────┤
                    │  • Content Discovery        │
                    │  • Extraction & Processing  │
                    │  • Quality Assessment       │
                    │  • Search & Ranking         │
                    │  • AI Summarization         │
                    │  • Trending Detection       │
                    └─────────────────────────────┘
                                 │
                    ┌─────────────────────────────┐
                    │      Data Layer             │
                    ├─────────────────────────────┤
                    │  • PostgreSQL (Primary)     │
                    │  • Redis (Cache/Queue)      │
                    │  • OpenSearch (Search)      │
                    └─────────────────────────────┘
```

### Technology Stack

**Backend:**
- **FastAPI**: High-performance async API framework
- **PostgreSQL**: Primary database with full-text search
- **Redis**: Caching, queuing, and session management
- **OpenSearch**: Advanced search and analytics (optional)

**Frontend:**
- **React 18**: Modern UI framework with concurrent features
- **TypeScript**: Type-safe development
- **TanStack Query**: Intelligent data fetching and caching
- **Tailwind CSS**: Utility-first styling

**AI & ML:**
- **DeepSeek AI**: Advanced language model for summarization
- **BM25**: Information retrieval and ranking
- **MinHash**: Near-duplicate detection
- **Statistical Analysis**: Trending detection and burst analysis

**Infrastructure:**
- **Docker**: Containerization and deployment
- **Kubernetes**: Orchestration and scaling (optional)
- **Evomi**: Proxy services for web crawling
- **Prometheus/Grafana**: Monitoring and alerting

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis 6+
- Docker & Docker Compose

### Local Development Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd sports-media-platform
   ```

2. **Start infrastructure services:**
   ```bash
   docker-compose up -d postgres redis
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -e .
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize the database:**
   ```bash
   python -m alembic upgrade head
   python scripts/seed_database.py
   ```

6. **Start the API server:**
   ```bash
   cd apps/api
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

7. **Start the frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

8. **Start background workers:**
   ```bash
   python -m apps.workers.crawler_worker
   ```

### Access the Application

- **Frontend**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 📁 Project Structure

```
sports-media-platform/
├── apps/                          # Application services
│   ├── api/                       # FastAPI application
│   │   ├── main.py               # API entry point
│   │   ├── routes/               # API route handlers
│   │   └── middleware/           # Custom middleware
│   └── workers/                  # Background workers
│       └── crawler_worker.py     # Content discovery worker
├── libs/                         # Shared libraries
│   ├── common/                   # Common utilities
│   │   ├── database.py          # Database models and connections
│   │   └── config.py            # Configuration management
│   ├── ingestion/               # Content ingestion
│   │   ├── crawler.py           # Web crawler with guardrails
│   │   └── extractor.py         # Content extraction and deduplication
│   ├── quality/                 # Quality assessment
│   │   └── scorer.py            # Multi-signal quality scoring
│   ├── search/                  # Search and ranking
│   │   ├── engine.py            # Search engine with dual backends
│   │   └── trending.py          # Trending detection and discovery
│   └── ai/                      # AI services
│       └── summarizer.py        # DeepSeek AI integration
├── frontend/                    # React frontend application
│   ├── client/src/              # Source code
│   │   ├── components/          # Reusable UI components
│   │   ├── pages/               # Page components
│   │   ├── hooks/               # Custom React hooks
│   │   └── lib/                 # Utilities and API client
│   └── package.json             # Frontend dependencies
├── tests/                       # Test suite
│   ├── test_golden_corpus.py    # 100-URL extraction testing
│   ├── test_chaos_engineering.py # Resilience testing
│   └── integration/             # Integration tests
├── infra/                       # Infrastructure configuration
│   ├── docker/                  # Docker configurations
│   ├── k8s/                     # Kubernetes manifests
│   └── terraform/               # Infrastructure as code
├── docs/                        # Documentation
│   ├── api/                     # API documentation
│   ├── deployment/              # Deployment guides
│   └── architecture/            # Architecture documentation
├── scripts/                     # Utility scripts
│   ├── seed_database.py         # Database seeding
│   └── backup_restore.py        # Backup and restore utilities
├── docker-compose.yml           # Local development environment
├── pyproject.toml              # Python project configuration
└── README.md                   # This file
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/sports_media
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_POOL_SIZE=10

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# AI Configuration
DEEPSEEK_API_KEY=your-deepseek-api-key
DEEPSEEK_API_BASE=https://api.deepseek.com/v1
AI_REQUEST_TIMEOUT=30
AI_MAX_RETRIES=3

# Crawler Configuration
EVOMI_API_KEY=your-evomi-api-key
EVOMI_ENDPOINT=https://api.evomi.com
CRAWLER_USER_AGENT=SportsMediaPlatform/1.0
CRAWLER_DELAY_SECONDS=1
CRAWLER_MAX_CONCURRENT=10
CRAWLER_RESPECT_ROBOTS_TXT=true

# Search Configuration
SEARCH_BACKEND=postgresql  # or opensearch
OPENSEARCH_URL=https://localhost:9200
OPENSEARCH_USERNAME=admin
OPENSEARCH_PASSWORD=admin

# Feature Flags
ENABLE_AI_SUMMARIZATION=true
ENABLE_TRENDING_DETECTION=true
ENABLE_QUALITY_GATE=true
QUALITY_GATE_SHADOW_MODE=false

# Monitoring
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
LOG_LEVEL=INFO
SENTRY_DSN=your-sentry-dsn
```

### Database Schema

The platform uses PostgreSQL with the following key tables:

- **content_items**: Extracted articles and content
- **sources**: Content source metadata and reputation
- **users**: User accounts and preferences
- **user_preferences**: Personalization settings
- **search_queries**: Query logs and analytics
- **trending_terms**: Real-time trending detection
- **quality_scores**: Content quality assessments

Run migrations to set up the schema:

```bash
python -m alembic upgrade head
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test suites
pytest tests/test_golden_corpus.py -v
pytest tests/test_chaos_engineering.py -v

# Run with coverage
pytest --cov=libs --cov=apps --cov-report=html
```

### Golden Corpus Testing

Test content extraction accuracy across 100 carefully selected URLs:

```bash
python tests/test_golden_corpus.py
```

Expected results:
- **Success Rate**: ≥85%
- **Average Quality Score**: ≥0.6
- **Average Extraction Time**: ≤5000ms

### Chaos Engineering

Test system resilience under failure conditions:

```bash
python tests/test_chaos_engineering.py
```

Scenarios tested:
- Database connection failures
- Redis cluster outages
- Network connectivity issues
- API service degradation
- Resource exhaustion

## 📊 Monitoring & Operations

### Health Checks

The platform provides comprehensive health endpoints:

- **GET /health**: Overall system health
- **GET /health/database**: Database connectivity
- **GET /health/redis**: Redis connectivity
- **GET /health/workers**: Background worker status

### Metrics

Key metrics tracked:

- **Content Discovery**: URLs crawled, extraction success rate, quality scores
- **Search Performance**: Query latency, result relevance, cache hit rates
- **AI Summarization**: Generation time, confidence scores, error rates
- **System Resources**: CPU, memory, database connections, Redis usage

### Logging

Structured logging with correlation IDs:

```python
import logging
logger = logging.getLogger(__name__)

# All logs include correlation ID for request tracing
logger.info("Content extracted", extra={
    "correlation_id": "req_123",
    "url": "https://example.com/article",
    "extraction_time_ms": 1250,
    "quality_score": 0.85
})
```

### Alerting

Configure alerts for:

- **High Error Rates**: >5% API errors, >10% extraction failures
- **Performance Degradation**: >100ms search latency, >5s extraction time
- **Resource Exhaustion**: >80% CPU, >90% memory, >100 DB connections
- **Service Outages**: Health check failures, worker downtime

## 🚀 Deployment

### Production Deployment

1. **Build Docker images:**
   ```bash
   docker build -t sports-media-api -f infra/docker/Dockerfile.api .
   docker build -t sports-media-worker -f infra/docker/Dockerfile.worker .
   docker build -t sports-media-frontend -f infra/docker/Dockerfile.frontend ./frontend
   ```

2. **Deploy with Docker Compose:**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Or deploy to Kubernetes:**
   ```bash
   kubectl apply -f infra/k8s/
   ```

### Scaling Guidelines

**Horizontal Scaling:**
- **API Servers**: Scale based on CPU usage (target: 70%)
- **Workers**: Scale based on queue depth (target: <100 pending jobs)
- **Database**: Use read replicas for search queries
- **Redis**: Use Redis Cluster for high availability

**Performance Targets:**
- **API Response Time**: <100ms (95th percentile)
- **Search Latency**: <50ms (PostgreSQL), <25ms (OpenSearch)
- **Content Processing**: 1000+ articles/hour per worker
- **Concurrent Users**: 10,000+ with proper scaling

### Security Considerations

- **Authentication**: JWT tokens with 24-hour expiration
- **Authorization**: Role-based access control (Admin, Editor, User)
- **API Security**: Rate limiting, input validation, security headers
- **Data Protection**: Encryption at rest and in transit
- **Network Security**: VPC isolation, security groups, WAF

## 🤝 Contributing

### Development Workflow

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make changes and add tests**
4. **Run the test suite**: `pytest`
5. **Run code quality checks**: `pre-commit run --all-files`
6. **Commit changes**: `git commit -m 'Add amazing feature'`
7. **Push to branch**: `git push origin feature/amazing-feature`
8. **Open a Pull Request**

### Code Quality

The project uses automated code quality tools:

- **Black**: Code formatting
- **isort**: Import sorting
- **Ruff**: Fast Python linting
- **mypy**: Static type checking
- **Bandit**: Security vulnerability scanning

Run quality checks:

```bash
pre-commit run --all-files
```

### Adding New Features

When adding new features:

1. **Update the database schema** if needed (create Alembic migration)
2. **Add comprehensive tests** (unit, integration, golden corpus if applicable)
3. **Update API documentation** (OpenAPI/Swagger)
4. **Add monitoring and logging**
5. **Update configuration** and environment variables
6. **Document the feature** in relevant docs

## 📚 Documentation

- **[API Documentation](docs/api/)**: Complete API reference
- **[Architecture Guide](docs/architecture/)**: System design and components
- **[Deployment Guide](docs/deployment/)**: Production deployment instructions
- **[Operations Manual](docs/operations/)**: Monitoring, troubleshooting, and maintenance

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check the [docs/](docs/) directory
- **Issues**: Open an issue on GitHub
- **Discussions**: Use GitHub Discussions for questions
- **Security**: Report security issues privately to security@example.com

## 🎯 Roadmap

### Phase 1: Core Platform (Current)
- ✅ Web-scale content discovery
- ✅ AI-powered summarization
- ✅ Advanced search and ranking
- ✅ Production deployment

### Phase 2: Enhanced Personalization
- 🔄 Machine learning recommendation engine
- 🔄 User behavior analytics
- 🔄 A/B testing framework
- 🔄 Advanced content filtering

### Phase 3: Mobile & Integrations
- 📱 Mobile applications (iOS/Android)
- 🔗 Third-party integrations (Slack, Discord)
- 📧 Email newsletters and notifications
- 🎙️ Podcast and video content support

### Phase 4: Enterprise Features
- 🏢 Multi-tenant architecture
- 📊 Advanced analytics dashboard
- 🔐 SSO and enterprise authentication
- 📈 Custom reporting and insights

---

**Built with ❤️ for sports fans everywhere**

