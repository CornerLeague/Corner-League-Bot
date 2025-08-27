# Corner League Bot

A production-ready, AI-powered sports media discovery and personalization platform that aggregates, analyzes, and summarizes sports content from across the web.

## 🏆 Overview

Corner League Bot is an enterprise-grade system that provides personalized sports news feeds through intelligent web-scale content discovery, AI-powered summarization, and sophisticated ranking algorithms. 

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
