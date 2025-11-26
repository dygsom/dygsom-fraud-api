# DYGSOM Fraud API

**Version:** 1.0.0
**Status:** Production Ready
**License:** Proprietary

Real-time fraud detection API powered by machine learning, designed for e-commerce and fintech platforms.

[![CI Pipeline](https://github.com/your-org/dygsom-fraud-api/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/dygsom-fraud-api/actions/workflows/ci.yml)
[![Deploy Staging](https://github.com/your-org/dygsom-fraud-api/actions/workflows/deploy-staging.yml/badge.svg)](https://github.com/your-org/dygsom-fraud-api/actions/workflows/deploy-staging.yml)
[![Deploy Production](https://github.com/your-org/dygsom-fraud-api/actions/workflows/deploy-production.yml/badge.svg)](https://github.com/your-org/dygsom-fraud-api/actions/workflows/deploy-production.yml)

---

## Features

- **ML-Powered Detection**: XGBoost model with 70+ features achieving 87%+ accuracy
- **Real-time Scoring**: Sub-100ms fraud assessment (P95 latency: 87ms)
- **High Throughput**: 100+ requests/second per instance, horizontally scalable
- **Secure Authentication**: API key-based authentication with rate limiting
- **Comprehensive Monitoring**: Prometheus metrics + Grafana dashboards
- **Multi-layer Caching**: L1 (in-memory) + L2 (Redis) for 90%+ hit rates
- **Production-Ready**: CI/CD pipeline, automated testing, blue-green deployments

---

## Quick Start

### For API Consumers

If you want to integrate the DYGSOM Fraud API into your application:

1. **Get Started in 15 Minutes**: [docs/customer/QUICK_START.md](docs/customer/QUICK_START.md)
2. **API Reference**: [docs/api/API_REFERENCE.md](docs/api/API_REFERENCE.md)
3. **Integration Guide**: [docs/api/INTEGRATION_GUIDE.md](docs/api/INTEGRATION_GUIDE.md)
4. **Code Examples**: [docs/api/examples/](docs/api/examples/)

**Example Request:**
```bash
curl -X POST https://api.dygsom.com/api/v1/fraud/score \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key_here" \
  -d '{
    "transaction_id": "tx-123456",
    "customer_email": "user@example.com",
    "customer_ip": "203.0.113.45",
    "amount": 299.99,
    "currency": "USD",
    "merchant_id": "merchant-001",
    "card_bin": "424242",
    "device_id": "device-xyz789",
    "timestamp": "2025-01-25T10:30:00Z"
  }'
```

---

### For Developers

If you want to run or contribute to the API itself:

**Prerequisites:**
- Docker & Docker Compose
- Python 3.11+
- PostgreSQL 15+ (via Docker)
- Redis 7+ (via Docker)

**Setup:**
```bash
# Clone repository
git clone https://github.com/your-org/dygsom-fraud-api.git
cd dygsom-fraud-api

# Copy environment file
cp .env.example .env

# Start all services
docker-compose up -d

# Check health
curl http://localhost:3000/health

# View API documentation
open http://localhost:3000/docs

# View Grafana dashboards
open http://localhost:3001  # Login: admin/admin
```

**Run Tests:**
```bash
# Unit and integration tests
pytest tests/ -v --cov=src

# Load testing
locust -f load_testing/locustfile.py --host=http://localhost:3000

# API profiling
python performance/profiling/profile_api.py --requests 100
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Load Balancer (Nginx)                     │
│                   least_conn | rate limiting                 │
└────────────┬──────────────┬──────────────┬──────────────────┘
             │              │              │
      ┌──────▼─────┐ ┌─────▼──────┐ ┌────▼──────┐
      │  API #1    │ │  API #2    │ │  API #3   │
      │  FastAPI   │ │  FastAPI   │ │  FastAPI  │
      │  + XGBoost │ │  + XGBoost │ │  + XGBoost│
      └──────┬─────┘ └─────┬──────┘ └────┬──────┘
             │              │              │
             └──────────────┼──────────────┘
                            │
            ┌───────────────┴───────────────┐
            │                               │
      ┌─────▼──────┐                 ┌─────▼─────┐
      │ PostgreSQL │                 │   Redis   │
      │ (Primary)  │                 │ (L2 Cache)│
      └────────────┘                 └───────────┘
```

**Technology Stack:**
- **API Framework**: FastAPI (Python 3.11)
- **ML Model**: XGBoost 2.0
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Monitoring**: Prometheus + Grafana
- **CI/CD**: GitHub Actions
- **Deployment**: Docker + Docker Compose

---

## Documentation

### API Documentation
- [API Reference](docs/api/API_REFERENCE.md) - Complete API specification
- [Integration Guide](docs/api/INTEGRATION_GUIDE.md) - Step-by-step integration
- [Error Codes](docs/api/ERROR_CODES.md) - Error handling reference
- [Code Examples](docs/api/examples/) - Python, Node.js, PHP, cURL

### Customer Guides
- [Quick Start](docs/customer/QUICK_START.md) - 15-minute getting started guide
- [Integration Checklist](docs/customer/INTEGRATION_CHECKLIST.md) - Pre-launch checklist
- [Testing Guide](docs/customer/TESTING_GUIDE.md) - How to test your integration
- [Best Practices](docs/customer/BEST_PRACTICES.md) - Security and performance tips

### Business Documentation
- [SLA](docs/business/SLA.md) - Service Level Agreement
- [Pricing](docs/business/PRICING.md) - Pricing tiers and plans
- [Support Policy](docs/business/SUPPORT_POLICY.md) - Support channels and SLAs
- [Terms of Service](docs/business/TERMS_OF_SERVICE.md) - Legal terms
- [Privacy Policy](docs/business/PRIVACY_POLICY.md) - Data privacy policy

### Operational Documentation
- [Deployment Guide](docs/DEPLOYMENT.md) - How to deploy to staging/production
- [Runbook](docs/RUNBOOK.md) - Operations and troubleshooting
- [Performance Guide](docs/PERFORMANCE.md) - Load testing and optimization
- [Monitoring Guide](docs/operations/MONITORING_GUIDE.md) - Metrics and alerts
- [Incident Response](docs/operations/INCIDENT_RESPONSE.md) - Incident procedures

### Launch Materials
- [MVP Launch Checklist](docs/launch/MVP_LAUNCH_CHECKLIST.md) - Pre-launch verification
- [Customer Success Kit](docs/launch/CUSTOMER_SUCCESS_KIT.md) - Onboarding resources

---

## Performance

### Benchmarks (Single Instance)

| Metric | Target | Measured | Status |
|--------|--------|----------|--------|
| **P50 Latency** | <50ms | 38ms | PASS |
| **P95 Latency** | <100ms | 87ms | PASS |
| **P99 Latency** | <200ms | 150ms | PASS |
| **Throughput** | 100 RPS | 100+ RPS | PASS |
| **Error Rate** | <0.1% | 0.0% | PASS |
| **ML Accuracy** | ≥87% | 87%+ | PASS |

### Scaled Deployment (3 Instances)

- **Throughput**: 300+ requests/second
- **Availability**: 99.9% (automatic failover)
- **Latency**: Consistent <100ms P95

See [PERFORMANCE.md](docs/PERFORMANCE.md) for detailed benchmarks and optimization guide.

---

## Security

- **Authentication**: API key in `X-API-Key` header
- **Encryption**: All traffic over HTTPS/TLS 1.2+
- **Rate Limiting**: 1000 requests/minute per API key
- **Input Validation**: Comprehensive request validation
- **SQL Injection**: Protected via SQLAlchemy ORM
- **Secret Management**: Environment variables, never committed

See [Security Audit](docs/operations/SECURITY_AUDIT.md) for full security checklist.

---

## Monitoring

**Dashboards:**
- API Overview (request rate, latency, errors)
- ML Performance (fraud score distribution, accuracy)
- Infrastructure (CPU, memory, disk, network)

**Key Metrics:**
- `fraud_api_requests_total` - Total API requests
- `fraud_api_request_duration_seconds` - Request latency histogram
- `fraud_api_fraud_score` - Fraud score distribution
- `fraud_api_cache_hit_rate` - Cache efficiency

**Alerts:**
- Error rate > 1%
- P95 latency > 150ms
- API uptime < 99.9%
- Cache hit rate < 80%

---

## Deployment

### Staging
```bash
# Automatic deployment on push to `develop` branch
git push origin develop

# Manual deployment
./deployment/scripts/deploy.sh staging
```

### Production
```bash
# Manual deployment with approval
gh workflow run deploy-production.yml -f version=v1.0.0

# Using deployment script
./deployment/scripts/deploy.sh production
```

### Rollback
```bash
# Automatic rollback on health check failure
# Manual rollback
./deployment/scripts/rollback.sh production
```

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed deployment guide.

---

## Support

- **Technical Support**: support@dygsom.com
- **Documentation**: https://docs.dygsom.com
- **Status Page**: https://status.dygsom.com
- **Community**: https://slack.dygsom.com

**For urgent production issues**, include "[URGENT]" in email subject line.

---

## Contributing

Internal contributors should follow:
1. Create feature branch from `develop`
2. Write tests for new features
3. Ensure CI pipeline passes
4. Submit pull request for review
5. Deploy to staging for validation
6. Merge to `main` for production

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and release notes.

---

## License

Proprietary - DYGSOM. All rights reserved.

This software is the property of DYGSOM and is protected by copyright law. Unauthorized copying, distribution, or use is strictly prohibited.

For licensing inquiries: sales@dygsom.com

---

**Version:** 1.0.0
**Last Updated:** 2025-01-25
**Maintained by:** DYGSOM Engineering Team
