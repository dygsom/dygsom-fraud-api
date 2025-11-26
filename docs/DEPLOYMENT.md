# DYGSOM Fraud API - Deployment Guide

Complete deployment guide for the DYGSOM Fraud Detection API.

---

## Table of Contents

1. [Overview](#overview)
2. [Environments](#environments)
3. [Prerequisites](#prerequisites)
4. [Deployment Process](#deployment-process)
   - [Staging Deployment](#staging-deployment)
   - [Production Deployment](#production-deployment)
5. [Rollback Process](#rollback-process)
6. [Pre-Deployment Checklist](#pre-deployment-checklist)
7. [Post-Deployment Checklist](#post-deployment-checklist)
8. [Troubleshooting](#troubleshooting)
9. [Monitoring](#monitoring)
10. [Emergency Contacts](#emergency-contacts)

---

## Overview

The DYGSOM Fraud API uses a modern CI/CD pipeline built with GitHub Actions, featuring:

- **Automated CI**: Linting, testing, building, and security scanning on every push/PR
- **Automated Staging Deployment**: Auto-deploy to staging on `develop` branch pushes
- **Manual Production Deployment**: Controlled deployment with approval gates
- **Blue-Green Deployment**: Zero-downtime deployments in production
- **Automated Rollback**: Health check failures trigger automatic rollback
- **Smoke Tests**: Post-deployment verification
- **Slack Notifications**: Real-time deployment status updates

---

## Environments

### Development
- **Purpose**: Local development and testing
- **Access**: Localhost only
- **Database**: Local PostgreSQL
- **Deployment**: Docker Compose (`docker compose up`)
- **Auto-Deploy**: No

### Staging
- **Purpose**: Pre-production testing and QA
- **Access**: `http://staging.dygsom.com`
- **Database**: Staging PostgreSQL (separate from production)
- **Deployment**: Automated via GitHub Actions
- **Auto-Deploy**: Yes (on push to `develop` branch)
- **Health Checks**: Enabled
- **Monitoring**: Prometheus + Grafana

### Production
- **Purpose**: Live production environment
- **Access**: `https://api.dygsom.com`
- **Database**: Production PostgreSQL (high availability)
- **Deployment**: Manual via GitHub Actions (requires approval)
- **Auto-Deploy**: No (manual trigger only)
- **Health Checks**: Enabled with strict thresholds
- **Monitoring**: Prometheus + Grafana + Sentry

---

## Prerequisites

### For Developers

1. **Git Access**
   - Write access to the GitHub repository
   - SSH key configured for GitHub

2. **Local Environment**
   - Docker and Docker Compose installed
   - Node.js 18+ (for Prisma CLI)
   - Python 3.11+

### For DevOps

1. **Server Access**
   - SSH access to staging and production servers
   - Sudo privileges for Docker commands

2. **GitHub Secrets Configured**
   - `STAGING_HOST`, `STAGING_USER`, `STAGING_SSH_KEY`
   - `PRODUCTION_HOST`, `PRODUCTION_USER`, `PRODUCTION_SSH_KEY`
   - `PRODUCTION_API_KEY` (for smoke tests)
   - `SLACK_WEBHOOK` (for notifications)

3. **GitHub Environments**
   - `staging` environment created (no approval required)
   - `production` environment created (requires approval)

---

## Deployment Process

### Staging Deployment

Staging deploys **automatically** when code is pushed to the `develop` branch.

#### Workflow

```
1. Developer pushes to develop branch
   ↓
2. GitHub Actions runs CI pipeline
   ├─ Linting (Black, isort, Ruff, MyPy)
   ├─ Tests (pytest with coverage)
   ├─ Docker build test
   └─ Security scan (Trivy)
   ↓
3. GitHub Actions builds Docker image
   ↓
4. GitHub Actions deploys to staging server
   ├─ Pull Docker image
   ├─ Run database migrations
   ├─ Deploy with docker compose
   ├─ Health checks
   └─ Smoke tests
   ↓
5. Slack notification (success/failure)
```

#### Manual Staging Deployment

If needed, you can manually deploy to staging:

```bash
# SSH to staging server
ssh user@staging-server

# Navigate to deployment directory
cd /opt/dygsom-fraud-api/deployment/staging

# Pull latest changes
git pull origin develop

# Run deployment script
../scripts/deploy.sh staging staging-latest
```

#### Monitoring Staging Deployment

1. **GitHub Actions**: Check the workflow run at https://github.com/your-org/dygsom-fraud-api/actions
2. **Slack**: Watch for deployment notifications in #deployments channel
3. **Staging URL**: Verify at http://staging.dygsom.com/health/ready
4. **Logs**: `docker logs dygsom-api-staging`

---

### Production Deployment

Production deployments are **manual** and require approval.

#### Prerequisites

1. **Version Tag**: Create a Git tag for the release
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. **Staging Verification**: Ensure the version is tested in staging
3. **Approval**: Have at least one team member ready to approve

#### Workflow

```
1. DevOps triggers workflow
   ├─ Go to GitHub Actions
   ├─ Select "Deploy to Production"
   ├─ Click "Run workflow"
   └─ Input version (e.g., v1.0.0)
   ↓
2. Workflow verifies version exists
   ↓
3. Workflow creates backup
   ├─ Backup current deployment config
   ├─ Backup database
   └─ Store in /opt/dygsom-fraud-api/backups
   ↓
4. GitHub requires approval
   ├─ Reviewer checks staging
   ├─ Reviewer checks change log
   └─ Reviewer approves deployment
   ↓
5. GitHub Actions deploys (Blue-Green)
   ├─ Build and push Docker image
   ├─ Run database migrations
   ├─ Start new container alongside old
   ├─ Health check new container
   ├─ Switch traffic to new container
   └─ Stop old container
   ↓
6. Smoke tests run
   ↓
7. GitHub creates deployment tag
   ↓
8. Slack notification (success/failure)
```

#### Step-by-Step Production Deployment

1. **Create Release Tag**
   ```bash
   git checkout main
   git pull
   git tag v1.2.0
   git push origin v1.2.0
   ```

2. **Trigger Deployment**
   - Go to: https://github.com/your-org/dygsom-fraud-api/actions
   - Select: "Deploy to Production" workflow
   - Click: "Run workflow"
   - Branch: `main`
   - Version: `v1.2.0`
   - Click: "Run workflow"

3. **Monitor Workflow**
   - Watch the workflow execution
   - Verify backup creation succeeds

4. **Approve Deployment**
   - Reviewer receives notification
   - Reviewer checks:
     - Staging is stable
     - Version matches expected
     - Change log reviewed
   - Reviewer clicks "Approve"

5. **Monitor Deployment**
   - Watch Blue-Green deployment logs
   - Verify health checks pass
   - Verify smoke tests pass

6. **Verify Production**
   - Check: https://api.dygsom.com/health/ready
   - Check Grafana dashboards
   - Monitor error rates in Sentry

#### Manual Production Deployment

If GitHub Actions is unavailable:

```bash
# SSH to production server
ssh user@production-server

# Navigate to deployment directory
cd /opt/dygsom-fraud-api/deployment/production

# Run deployment script
../scripts/deploy.sh production v1.2.0
```

---

## Rollback Process

### Automated Rollback

If health checks fail during deployment, the system automatically attempts rollback.

### Manual Rollback

#### Quick Rollback (Latest Backup)

```bash
# SSH to server
ssh user@production-server

# Navigate to deployment scripts
cd /opt/dygsom-fraud-api/deployment/scripts

# Run rollback (uses latest backup)
./rollback.sh production
```

#### Rollback to Specific Backup

```bash
# List available backups
ls -lh /opt/dygsom-fraud-api/backups/

# Rollback to specific backup
./rollback.sh production /opt/dygsom-fraud-api/backups/backup-20250125-143000.tar.gz
```

#### Verify Rollback

```bash
# Check health
curl http://localhost:3000/health/ready

# Check logs
docker logs dygsom-api-production

# Run smoke tests
./smoke-tests.sh production
```

### Rollback Checklist

- [ ] Identify the issue (check logs, metrics, errors)
- [ ] Determine last known good version
- [ ] Notify team in Slack (#incidents)
- [ ] Execute rollback
- [ ] Verify health checks pass
- [ ] Run smoke tests
- [ ] Monitor for 10 minutes
- [ ] Update incident log
- [ ] Schedule post-mortem

---

## Pre-Deployment Checklist

### Staging Deployment

- [ ] Code reviewed and approved
- [ ] All tests passing in CI
- [ ] No security vulnerabilities (Trivy scan clean)
- [ ] Database migrations tested locally
- [ ] `.env.staging` updated if needed

### Production Deployment

- [ ] Tested and verified in staging for at least 24 hours
- [ ] All smoke tests passing in staging
- [ ] Change log reviewed and approved
- [ ] Database migration plan reviewed
- [ ] Rollback plan documented
- [ ] On-call engineer available
- [ ] Backup window confirmed (low traffic period)
- [ ] Stakeholders notified
- [ ] `.env.production` updated if needed
- [ ] Sentry release prepared
- [ ] Monitoring dashboards ready

---

## Post-Deployment Checklist

### Immediate (0-5 minutes)

- [ ] Health checks passing
- [ ] Smoke tests passing
- [ ] No error spikes in logs
- [ ] No alerts firing
- [ ] API response times normal

### Short-term (5-30 minutes)

- [ ] Verify key user flows (fraud scoring, API endpoints)
- [ ] Check Grafana dashboards (request rate, error rate, latency)
- [ ] Check Sentry for new errors
- [ ] Monitor database performance
- [ ] Verify cache hit rates

### Medium-term (30 minutes - 2 hours)

- [ ] Monitor fraud detection accuracy
- [ ] Check business metrics (transaction volume, fraud rate)
- [ ] Verify integrations with external systems
- [ ] Review customer feedback/support tickets
- [ ] Update deployment log

---

## Troubleshooting

### Deployment Fails - Build Error

**Symptoms**: Docker build fails in GitHub Actions

**Solution**:
1. Check build logs in GitHub Actions
2. Verify Dockerfile syntax
3. Check for missing dependencies in requirements.txt
4. Test build locally: `docker build -t test .`

### Deployment Fails - Health Check

**Symptoms**: Health check fails after deployment

**Solution**:
1. Check logs: `docker logs dygsom-api-[staging|production]`
2. Verify database connection
3. Verify Redis connection
4. Check environment variables in `.env`
5. Manual health check: `curl http://localhost:3000/health/ready`

### Database Migration Fails

**Symptoms**: `npx prisma migrate deploy` fails

**Solution**:
1. Check migration files for syntax errors
2. Verify database connectivity
3. Check database user permissions
4. Review migration logs
5. If needed, manually fix database and rerun

### Rollback Fails

**Symptoms**: Rollback script exits with error

**Solution**:
1. Check if backup file exists
2. Manually restore docker-compose.yml and .env
3. Run `docker compose up -d --force-recreate api`
4. If database needs restoration, use pg_restore

### Container Won't Start

**Symptoms**: Container exits immediately after starting

**Solution**:
1. Check logs: `docker logs dygsom-api-[env]`
2. Verify environment variables
3. Check resource limits (CPU, memory)
4. Verify database and Redis are healthy
5. Try starting in interactive mode: `docker run -it [image] /bin/bash`

---

## Monitoring

### Key Metrics to Watch

#### Application Metrics (Prometheus/Grafana)

- **Request Rate**: `rate(api_requests_total[5m])`
- **Error Rate**: `rate(api_request_errors_total[5m])`
- **Latency**: `api_request_duration_seconds`
- **Fraud Detection Rate**: `fraud_score_distribution`
- **Cache Hit Rate**: `cache_hits_total / (cache_hits_total + cache_misses_total)`
- **Database Query Duration**: `db_query_duration_seconds`

#### System Metrics

- **CPU Usage**: Container CPU utilization
- **Memory Usage**: Container memory utilization
- **Disk Usage**: Database volume usage
- **Network I/O**: Container network traffic

#### Business Metrics

- **Transaction Volume**: `transaction_volume_total`
- **Fraud Rate**: `fraud_rate_percentage`
- **Risk Level Distribution**: `risk_level_distribution_total`

### Alerts

#### Critical Alerts (Page Immediately)

- API error rate > 5% for 5 minutes
- API latency p95 > 1s for 5 minutes
- Health check failing
- Database connection errors
- Critical security vulnerability detected

#### Warning Alerts (Notify in Slack)

- API error rate > 1% for 10 minutes
- Cache hit rate < 50% for 15 minutes
- Disk usage > 80%
- Memory usage > 85%

### Dashboards

- **Main Dashboard**: https://monitoring.dygsom.com/d/main
- **API Performance**: https://monitoring.dygsom.com/d/api
- **ML Metrics**: https://monitoring.dygsom.com/d/ml
- **Infrastructure**: https://monitoring.dygsom.com/d/infra

---

## Emergency Contacts

### On-Call Rotation

- **Primary On-Call**: Check PagerDuty schedule
- **Secondary On-Call**: Check PagerDuty schedule

### Team Contacts

- **DevOps Lead**: devops-lead@dygsom.com
- **Backend Lead**: backend-lead@dygsom.com
- **ML Engineer**: ml-engineer@dygsom.com

### Escalation

- **Level 1**: On-call engineer (via PagerDuty)
- **Level 2**: Team lead (via phone)
- **Level 3**: CTO (via phone)

### External Vendors

- **Cloud Provider Support**: [Support Portal URL]
- **Database Support**: [Support Portal URL]
- **Monitoring Support**: [Support Portal URL]

### Communication Channels

- **#incidents**: Incident coordination
- **#deployments**: Deployment notifications
- **#alerts**: Automated alerts
- **#on-call**: On-call engineer chat

---

## Appendix

### Useful Commands

```bash
# Check deployment status
docker compose ps

# View logs (last 100 lines)
docker compose logs --tail=100 api

# Follow logs in real-time
docker compose logs -f api

# Check resource usage
docker stats

# Execute command in container
docker compose exec api bash

# Database access
docker compose exec postgres psql -U postgres -d dygsom_production

# Redis access
docker compose exec redis redis-cli

# Run database migration
docker compose run --rm api npx prisma migrate deploy

# Generate Prisma client
docker compose run --rm api npx prisma generate
```

### Version Numbering

We use Semantic Versioning (SemVer): `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking API changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

Examples:
- `v1.0.0`: Initial release
- `v1.1.0`: New feature added
- `v1.1.1`: Bug fix
- `v2.0.0`: Breaking changes

### Release Process

1. Create release branch: `git checkout -b release/v1.2.0`
2. Update version in files
3. Update CHANGELOG.md
4. Create PR to main
5. After merge, tag release
6. Deploy to staging
7. Test in staging
8. Deploy to production
9. Monitor for issues

---

**Last Updated**: 2025-11-25
**Document Version**: 1.0.0
**Owner**: DevOps Team
