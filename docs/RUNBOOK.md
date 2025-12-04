# DYGSOM Fraud API - Operations Runbook

Operational procedures and troubleshooting guide for on-call engineers.

---

## Table of Contents

1. [Common Operations](#common-operations)
2. [Incident Response](#incident-response)
3. [Maintenance Tasks](#maintenance-tasks)
4. [Emergency Procedures](#emergency-procedures)
5. [Useful Commands](#useful-commands)

---

## Common Operations

### Restart Services

#### Restart API Container

```bash
# Staging
ssh user@staging-server
cd /opt/dygsom-fraud-api/deployment/staging
docker compose restart api

# Production
ssh user@production-server
cd /opt/dygsom-fraud-api/deployment/production
docker compose restart api

# Verify
curl http://localhost:3000/health/ready
```

#### Restart All Services

```bash
docker compose restart

# Or with downtime
docker compose down
docker compose up -d
```

#### Restart Database

```bash
# WARNING: This causes downtime!
docker compose restart postgres

# Wait for database to be ready
docker compose exec postgres pg_isready -U postgres
```

### View Logs

#### Real-time Logs

```bash
# Follow API logs
docker compose logs -f api

# Follow all logs
docker compose logs -f

# Last 100 lines
docker compose logs --tail=100 api

# Since specific time
docker compose logs --since="2025-01-25T14:00:00" api
```

#### Search Logs

```bash
# Search for errors
docker compose logs api | grep -i error

# Search for specific transaction
docker compose logs api | grep "transaction_id:12345"

# Export logs to file
docker compose logs api > api-logs-$(date +%Y%m%d).log
```

### Database Operations

#### Access Database

```bash
# Connect to database
docker compose exec postgres psql -U postgres -d dygsom_production

# Run query
docker compose exec postgres psql -U postgres -d dygsom_production -c "SELECT COUNT(*) FROM Transaction;"
```

#### Database Backup

```bash
# Create backup
docker compose exec postgres pg_dump -U postgres dygsom_production > backup-$(date +%Y%m%d-%H%M%S).sql

# Compress backup
gzip backup-$(date +%Y%m%d-%H%M%S).sql

# Copy to backup server
scp backup-*.sql.gz backup-server:/backups/
```

#### Database Restore

```bash
# From SQL file
docker compose exec -T postgres psql -U postgres -d dygsom_production < backup.sql

# From compressed file
gunzip -c backup.sql.gz | docker compose exec -T postgres psql -U postgres -d dygsom_production
```

#### Run Migrations

```bash
# Deploy pending migrations
docker compose exec api npx prisma migrate deploy

# Check migration status
docker compose exec api npx prisma migrate status

# Generate Prisma client
docker compose exec api npx prisma generate
```

### Check System Health

#### Container Health

```bash
# Check all containers
docker compose ps

# Check container health status
docker inspect dygsom-api-production | grep -A 10 Health

# Check resource usage
docker stats --no-stream
```

#### Application Health

```bash
# Health endpoint
curl http://localhost:3000/health

# Readiness endpoint
curl http://localhost:3000/health/ready

# Metrics endpoint
curl http://localhost:3000/metrics
```

#### Database Health

```bash
# Check connections
docker compose exec postgres psql -U postgres -d dygsom_production -c "SELECT count(*) FROM pg_stat_activity;"

# Check database size
docker compose exec postgres psql -U postgres -d dygsom_production -c "SELECT pg_size_pretty(pg_database_size('dygsom_production'));"

# Check table sizes
docker compose exec postgres psql -U postgres -d dygsom_production -c "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size FROM pg_tables ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC LIMIT 10;"
```

### Cache Operations

#### Redis Commands

```bash
# Connect to Redis
docker compose exec redis redis-cli

# Check memory usage
docker compose exec redis redis-cli INFO memory

# Get cache hit rate
docker compose exec redis redis-cli INFO stats | grep keyspace

# Clear specific key
docker compose exec redis redis-cli DEL "cache:customer:email@example.com"

# Clear all cache (WARNING: Performance impact!)
docker compose exec redis redis-cli FLUSHALL
```

---

## Incident Response

### High Error Rate

**Symptoms**: Error rate > 5% for 5+ minutes

**Steps**:

1. **Acknowledge Alert**
   ```bash
   # Check error rate
   curl http://localhost:9090/api/v1/query?query=rate(api_request_errors_total[5m])
   ```

2. **Check Logs**
   ```bash
   docker compose logs --tail=200 api | grep ERROR
   ```

3. **Identify Error Type**
   - Database connection errors → Check database
   - Redis connection errors → Check Redis
   - 500 errors → Check application logs
   - 401/403 errors → Check authentication service

4. **Mitigate**
   - If database issue: Restart database or scale up
   - If application issue: Restart API container
   - If persistent: Rollback to previous version

5. **Document**
   - Update incident log in Slack #incidents
   - Create incident report

### High Latency

**Symptoms**: p95 latency > 1s for 5+ minutes

**Steps**:

1. **Check Metrics**
   ```bash
   # Check current latency
   curl 'http://localhost:9090/api/v1/query?query=api_request_duration_seconds{quantile="0.95"}'
   ```

2. **Identify Bottleneck**
   - Check database query times
   - Check cache hit rate
   - Check ML model inference time
   - Check external API calls

3. **Quick Fixes**
   ```bash
   # Clear cache if hit rate is low
   docker compose exec redis redis-cli FLUSHALL

   # Restart API if memory leak suspected
   docker compose restart api

   # Scale up database if needed
   # (requires infrastructure changes)
   ```

4. **Long-term**
   - Optimize slow queries
   - Add caching
   - Scale horizontally

### Database Connection Pool Exhausted

**Symptoms**: "Too many connections" errors

**Steps**:

1. **Check Active Connections**
   ```bash
   docker compose exec postgres psql -U postgres -d dygsom_production -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';"
   ```

2. **Kill Idle Connections**
   ```bash
   docker compose exec postgres psql -U postgres -d dygsom_production -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND state_change < NOW() - INTERVAL '5 minutes';"
   ```

3. **Increase Pool Size** (if needed)
   - Update `DATABASE_POOL_SIZE` in .env
   - Restart API

### Out of Memory

**Symptoms**: Container restarts, OOMKilled events

**Steps**:

1. **Check Memory Usage**
   ```bash
   docker stats --no-stream dygsom-api-production
   ```

2. **Check for Memory Leaks**
   ```bash
   # Check container logs for memory warnings
   docker compose logs api | grep -i memory
   ```

3. **Immediate Fix**
   ```bash
   # Restart container
   docker compose restart api
   ```

4. **Long-term**
   - Increase memory limits in docker-compose.yml
   - Fix memory leaks in code
   - Optimize data structures

### Fraud Detection Not Working

**Symptoms**: All fraud scores returning 0 or errors

**Steps**:

1. **Check ML Model**
   ```bash
   docker compose exec api ls -lh ml/models/
   ```

2. **Check Model Loading**
   ```bash
   docker compose logs api | grep -i "model"
   ```

3. **Test Fraud Endpoint**
   ```bash
   curl -X POST http://localhost:3000/api/v1/fraud/score \
     -H "Content-Type: application/json" \
     -H "X-API-Key: your-api-key" \
     -d '{
       "transaction_id": "test-123",
       "customer_email": "test@example.com",
       "customer_ip": "192.168.1.1",
       "amount": 100.00,
       "currency": "USD",
       "merchant_id": "test-merchant",
       "card_bin": "424242"
     }'
   ```

4. **Reload Model** (if needed)
   ```bash
   docker compose restart api
   ```

---

## Maintenance Tasks

### Weekly Tasks

#### Review Alerts

```bash
# Check Grafana dashboards
# Review recent alerts in Slack #alerts
# Update alert thresholds if needed
```

#### Database Maintenance

```bash
# Vacuum database
docker compose exec postgres vacuumdb -U postgres -d dygsom_production --analyze

# Reindex
docker compose exec postgres reindexdb -U postgres -d dygsom_production
```

#### Log Rotation

```bash
# Check log sizes
docker compose exec api du -sh /var/log/

# Rotate logs if needed
docker compose exec api logrotate /etc/logrotate.conf
```

#### Backup Verification

```bash
# Verify latest backups exist
ls -lh /opt/dygsom-fraud-api/backups/

# Test restore on staging
scp latest-backup.sql staging-server:/tmp/
ssh staging-server
# Restore to test database
```

### Monthly Tasks

#### Security Updates

```bash
# Update base images
docker compose pull

# Rebuild containers
docker compose up -d --force-recreate

# Run security scan
docker scan dygsom-fraud-api:production-latest
```

#### Performance Review

```bash
# Review Grafana dashboards
# Identify slow queries
# Optimize database indexes
# Review cache hit rates
```

#### Capacity Planning

```bash
# Check disk usage
df -h

# Check database growth
docker compose exec postgres psql -U postgres -d dygsom_production -c "SELECT pg_size_pretty(pg_database_size('dygsom_production'));"

# Review traffic trends in Grafana
# Plan for scaling if needed
```

---

## Emergency Procedures

### Complete Service Outage

**Priority**: P0 - All hands on deck

**Steps**:

1. **Alert Team**
   ```
   Post in Slack #incidents: "P0: Complete service outage"
   Page all on-call engineers
   ```

2. **Quick Health Check**
   ```bash
   # Check if containers are running
   docker compose ps

   # Check if server is reachable
   ping production-server

   # Check if ports are open
   nc -zv production-server 3000
   ```

3. **Restart All Services**
   ```bash
   docker compose down
   docker compose up -d
   ```

4. **If Restart Fails**
   ```bash
   # Rollback to last known good version
   cd /opt/dygsom-fraud-api/deployment/scripts
   ./rollback.sh production
   ```

5. **If Rollback Fails**
   - Check server resources (CPU, memory, disk)
   - Check Docker daemon: `systemctl status docker`
   - Reboot server if necessary
   - Restore from backup

### Data Loss Event

**Priority**: P0 - Critical

**Steps**:

1. **Stop All Writes**
   ```bash
   docker compose stop api
   ```

2. **Assess Damage**
   ```bash
   # Check what data is affected
   docker compose exec postgres psql -U postgres -d dygsom_production -c "SELECT COUNT(*) FROM Transaction;"
   ```

3. **Restore from Backup**
   ```bash
   # Find latest backup
   ls -lht /opt/dygsom-fraud-api/backups/

   # Restore database
   docker compose exec -T postgres psql -U postgres -d dygsom_production < latest-backup.sql
   ```

4. **Verify Data Integrity**
   ```bash
   # Run data integrity checks
   docker compose exec postgres psql -U postgres -d dygsom_production -c "SELECT * FROM Transaction ORDER BY created_at DESC LIMIT 10;"
   ```

5. **Restart Services**
   ```bash
   docker compose up -d api
   ```

### Security Breach

**Priority**: P0 - Critical

**Steps**:

1. **Isolate**
   ```bash
   # Stop all services immediately
   docker compose down

   # Block all network access
   iptables -A INPUT -j DROP
   ```

2. **Alert**
   - Notify security team immediately
   - Notify management
   - Prepare for customer communication

3. **Investigate**
   - Review access logs
   - Check for unauthorized access
   - Identify attack vector
   - Document findings

4. **Remediate**
   - Rotate all secrets and API keys
   - Patch vulnerabilities
   - Update security rules
   - Deploy fixes

5. **Recovery**
   - Restore from known good backup
   - Run security scan
   - Monitor for continued attack
   - Update incident response procedures

---

## Useful Commands

### Docker

```bash
# View running containers
docker ps

# View all containers (including stopped)
docker ps -a

# View container resource usage
docker stats

# Inspect container
docker inspect <container-name>

# Execute command in running container
docker exec -it <container-name> bash

# View container logs
docker logs <container-name>

# Stop container
docker stop <container-name>

# Remove container
docker rm <container-name>

# Prune unused resources
docker system prune -a
```

### Docker Compose

```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# Restart service
docker compose restart <service-name>

# View logs
docker compose logs <service-name>

# Scale service
docker compose up -d --scale api=3

# Rebuild and start
docker compose up -d --build

# View service status
docker compose ps
```

### Database

```bash
# Connect to database
docker compose exec postgres psql -U postgres -d dygsom_production

# Run query
docker compose exec postgres psql -U postgres -d dygsom_production -c "SELECT * FROM Transaction LIMIT 5;"

# Backup database
docker compose exec postgres pg_dump -U postgres dygsom_production > backup.sql

# Restore database
docker compose exec -T postgres psql -U postgres -d dygsom_production < backup.sql

# Check database size
docker compose exec postgres psql -U postgres -d dygsom_production -c "SELECT pg_size_pretty(pg_database_size('dygsom_production'));"

# Check active connections
docker compose exec postgres psql -U postgres -d dygsom_production -c "SELECT count(*) FROM pg_stat_activity;"
```

### Redis

```bash
# Connect to Redis
docker compose exec redis redis-cli

# Check memory
docker compose exec redis redis-cli INFO memory

# Get all keys (use with caution in production)
docker compose exec redis redis-cli KEYS '*'

# Delete key
docker compose exec redis redis-cli DEL key-name

# Clear all data (WARNING!)
docker compose exec redis redis-cli FLUSHALL

# Monitor commands in real-time
docker compose exec redis redis-cli MONITOR
```

### Monitoring

```bash
# Query Prometheus
curl 'http://localhost:9090/api/v1/query?query=up'

# Check metrics endpoint
curl http://localhost:3000/metrics

# View Grafana dashboards
# Open browser: http://monitoring.dygsom.pe
```

### Networking

```bash
# Test connectivity
ping production-server

# Test port
nc -zv production-server 3000

# Check listening ports
netstat -tlnp

# View network connections
docker network ls

# Inspect network
docker network inspect dygsom-production-network
```

---

**Last Updated**: 2025-11-25
**Document Version**: 1.0.0
**Owner**: DevOps Team
