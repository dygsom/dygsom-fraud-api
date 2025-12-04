# DYGSOM Fraud API - Performance Guide

**Version:** 1.0.0
**Last Updated:** 2025-01-25
**Maintainer:** DYGSOM Engineering Team

---

## Table of Contents

- [Overview](#overview)
- [Performance Targets](#performance-targets)
- [Baseline Metrics](#baseline-metrics)
- [Load Testing](#load-testing)
- [Performance Optimization](#performance-optimization)
- [Horizontal Scaling](#horizontal-scaling)
- [Monitoring & Profiling](#monitoring--profiling)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

---

## Overview

This guide provides comprehensive documentation for performance testing, optimization, and scaling of the DYGSOM Fraud Detection API. It covers:

- **Load Testing**: Using Locust to simulate realistic traffic patterns
- **Performance Optimization**: Database queries, caching, and application tuning
- **Horizontal Scaling**: Multi-instance deployment with nginx load balancing
- **Monitoring**: Profiling, metrics collection, and performance analysis

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Load Balancer (Nginx)                     │
│                     - least_conn algorithm                       │
│                     - Rate limiting: 100 req/min                 │
│                     - Health checks: /health                     │
└────────────┬──────────────┬──────────────┬───────────────────────┘
             │              │              │
      ┌──────▼─────┐ ┌─────▼──────┐ ┌────▼──────┐
      │  API #1    │ │  API #2    │ │  API #3   │
      │  - L1 Cache│ │  - L1 Cache│ │  - L1Cache│
      │  100 rps   │ │  100 rps   │ │  100 rps  │
      └──────┬─────┘ └─────┬──────┘ └────┬──────┘
             │              │              │
             └──────────────┼──────────────┘
                            │
            ┌───────────────┴───────────────┐
            │                               │
      ┌─────▼──────┐                 ┌─────▼─────┐
      │ PostgreSQL │                 │   Redis   │
      │ (Primary)  │                 │ (L2 Cache)│
      │ 200 conns  │                 │  1GB mem  │
      └────────────┘                 └───────────┘
```

---

## Performance Targets

### SLA Targets (Production)

| Metric | Target | Critical Threshold | Monitoring |
|--------|--------|-------------------|------------|
| **Throughput** | 100+ req/sec (single) | <80 req/sec | Prometheus |
| **P50 Latency** | <50ms | >100ms | Prometheus |
| **P95 Latency** | <100ms | >200ms | Prometheus |
| **P99 Latency** | <200ms | >500ms | Prometheus |
| **Error Rate** | <0.1% | >1.0% | Prometheus + Sentry |
| **Availability** | 99.9% | <99.0% | Uptime monitoring |
| **Cache Hit Rate** | >90% | <80% | Redis metrics |
| **DB Query Time (P95)** | <50ms | >100ms | PostgreSQL logs |

### Scaled Deployment Targets (3 Instances)

| Metric | Target | Notes |
|--------|--------|-------|
| **Total Throughput** | 300+ req/sec | 100 rps × 3 instances |
| **P95 Latency** | <100ms | With load balancing |
| **P99 Latency** | <200ms | Consistent across instances |
| **Availability** | 99.9% | Automatic failover |

### Resource Limits

| Resource | Single Instance | 3 Instances (Scaled) |
|----------|----------------|---------------------|
| **CPU** | 2 cores | 12 cores total |
| **Memory** | 2GB | 10GB total |
| **DB Connections** | 50 (20 pool + 30 overflow) | 150 (3 × 50) |
| **Redis Connections** | 100 | 300 (shared pool) |

---

## Baseline Metrics

### Single Instance Performance

Based on measurements with 10 concurrent users over 5 minutes:

```json
{
  "endpoints": {
    "/api/v1/fraud/score": {
      "avg_response_time_ms": 45,
      "median_response_time_ms": 38,
      "p95_response_time_ms": 87,
      "p99_response_time_ms": 150,
      "max_response_time_ms": 250,
      "throughput_rps": 50,
      "error_rate_percent": 0.0
    },
    "/health": {
      "avg_response_time_ms": 3,
      "p95_response_time_ms": 5,
      "throughput_rps": 10
    },
    "/health/ready": {
      "avg_response_time_ms": 12,
      "p95_response_time_ms": 25,
      "throughput_rps": 5
    }
  },
  "system": {
    "cpu_usage_percent": 35,
    "memory_usage_mb": 512,
    "database_connections_active": 8,
    "redis_memory_mb": 45
  },
  "cache": {
    "l1_hit_rate_percent": 75,
    "l2_hit_rate_percent": 85,
    "overall_hit_rate_percent": 85
  }
}
```

**Baseline Summary:**
- ✅ Meets P95 latency target (87ms < 100ms)
- ⚠️  Needs improvement for P99 (150ms, target: <200ms)
- ✅ Zero errors
- ⚠️  Cache hit rate below target (85% vs 90% target)

---

## Load Testing

### Prerequisites

```bash
# Install Locust
cd load_testing
pip install -r requirements.txt

# Verify API is running
curl http://localhost:3000/health

# Verify authentication
curl -H "X-API-Key: dygsom_test_api_key_change_me" \
     http://localhost:3000/health/ready
```

### Test Scenarios

We provide several pre-configured test scenarios:

#### 1. Baseline Test (Warm-up)

**Purpose:** Establish baseline performance metrics
**Load:** 10 users, 5 minutes
**Expected RPS:** ~20

```bash
locust -f load_testing/locustfile.py \
       --host=http://localhost:3000 \
       --users 10 \
       --spawn-rate 2 \
       --run-time 5m \
       --headless
```

#### 2. Normal Load Test

**Purpose:** Simulate typical production traffic
**Load:** 50 users, 10 minutes
**Expected RPS:** ~80

```bash
locust -f load_testing/locustfile.py \
       --host=http://localhost:3000 \
       --users 50 \
       --spawn-rate 5 \
       --run-time 10m \
       --headless
```

#### 3. Stress Test

**Purpose:** Find the breaking point
**Load:** 100 users, 10 minutes
**Expected RPS:** ~100

```bash
locust -f load_testing/locustfile.py \
       --host=http://localhost:3000 \
       --users 100 \
       --spawn-rate 10 \
       --run-time 10m \
       --headless
```

#### 4. Spike Test

**Purpose:** Test response to sudden traffic surge
**Load:** 200 users ramped up quickly, 2 minutes
**Expected RPS:** ~150

```bash
locust -f load_testing/locustfile.py \
       --host=http://localhost:3000 \
       --users 200 \
       --spawn-rate 50 \
       --run-time 2m \
       --headless
```

#### 5. Endurance Test

**Purpose:** Detect memory leaks and performance degradation
**Load:** 50 users, 60 minutes
**Expected RPS:** ~80 (sustained)

```bash
locust -f load_testing/locustfile.py \
       --host=http://localhost:3000 \
       --users 50 \
       --spawn-rate 5 \
       --run-time 60m \
       --headless
```

### Specialized Fraud Scoring Test

For detailed fraud scoring performance:

```bash
locust -f load_testing/scenarios/fraud_scoring.py \
       --host=http://localhost:3000 \
       --users 100 \
       --spawn-rate 10 \
       --run-time 10m \
       --headless
```

This scenario tests:
- Low amount transactions (<$100): 50% weight
- Medium amount ($100-$1000): 30% weight
- High amount (>$1000): 20% weight
- Suspicious patterns: 10% weight

### Interactive Load Testing (Web UI)

For real-time monitoring during tests:

```bash
# Start Locust web UI
locust -f load_testing/locustfile.py --host=http://localhost:3000

# Open browser
open http://localhost:8089
```

### Analyzing Results

After each test, review:

1. **Response Times:**
   - P50, P95, P99 latencies
   - Max response time
   - Distribution graph

2. **Throughput:**
   - Requests per second
   - Total requests
   - Failed requests

3. **Error Rate:**
   - Should be <0.1%
   - Investigate any 500 errors

4. **Resource Usage:**
   ```bash
   # CPU and memory
   docker stats

   # Database connections
   docker exec -it fraud-db psql -U fraud_user -d fraud_db \
     -c "SELECT count(*) FROM pg_stat_activity;"

   # Redis memory
   docker exec -it fraud-redis redis-cli INFO memory
   ```

---

## Performance Optimization

### 1. Database Optimization

#### Query Optimization

Apply the optimized queries from `performance/optimization/query_optimization.sql`:

```bash
# Connect to database
docker exec -it fraud-db psql -U fraud_user -d fraud_db

# Apply optimizations
\i performance/optimization/query_optimization.sql
```

**Key Optimizations:**

1. **Velocity Features Function** (Single Query)
   - **Before:** 3-5 separate queries, ~30ms total
   - **After:** 1 optimized query with CTEs, ~10ms
   - **Impact:** 66% improvement

2. **Materialized Views**
   - Pre-compute expensive aggregations
   - Refresh hourly via cron
   - 90% faster dashboard queries

3. **Optimized Indexes**
   - Partial indexes for recent data
   - Covering indexes for common queries
   - Index-only scans where possible

```sql
-- Example: Create partial index for recent transactions
CREATE INDEX CONCURRENTLY idx_transactions_customer_recent
ON transactions (customer_email, timestamp DESC)
WHERE timestamp > NOW() - INTERVAL '7 days';
```

#### Index Monitoring

Regularly check index health:

```bash
# Run index recommendations
docker exec -it fraud-db psql -U fraud_user -d fraud_db \
  -f performance/optimization/index_recommendations.sql
```

**Monitor:**
- Unused indexes (idx_scan = 0)
- Index bloat (>30%)
- Missing indexes (sequential scans on large tables)
- Duplicate indexes

#### Database Connection Pooling

Configured in `src/core/config.py`:

```python
DATABASE_POOL_SIZE = 20          # Base connections
DATABASE_MAX_OVERFLOW = 30       # Additional under load
DATABASE_POOL_TIMEOUT = 10       # Wait timeout (seconds)
DATABASE_POOL_RECYCLE = 3600     # Recycle after 1 hour
DATABASE_POOL_PRE_PING = True    # Test before use
```

**Tuning Guidelines:**
- **Single instance:** 20 pool + 30 overflow = 50 max
- **3 instances:** 3 × 50 = 150 total connections
- **Database max_connections:** 200 (with buffer)

### 2. Caching Strategy

#### Two-Level Cache Architecture

**L1 Cache (In-Memory):**
- Per-instance LRU cache
- Size: 2000 entries
- Hit rate: 75-85%
- Latency: <1ms

**L2 Cache (Redis):**
- Shared across all instances
- Size: 1GB
- Hit rate: 85-95%
- Latency: 1-2ms

**Combined Hit Rate:** >90%

#### Cache Configuration

```python
# src/core/config.py
CACHE_L1_MAX_SIZE = 2000              # Increased from 1000
CACHE_L2_ENABLED = True               # Enable Redis
CACHE_VELOCITY_TTL = 60               # 1 minute
CACHE_CUSTOMER_HISTORY_TTL = 60       # 1 minute
CACHE_IP_HISTORY_TTL = 300            # 5 minutes
CACHE_ML_PREDICTION_TTL = 300         # 5 minutes
```

#### Cache Key Design

Use consistent prefixes for easy management:

```python
# Velocity features
fraud:velocity:{customer_email}:{timestamp_hour}

# Customer history
fraud:customer:{customer_email}:history

# IP history
fraud:ip:{customer_ip}:history

# ML predictions
fraud:ml:prediction:{feature_hash}
```

#### Cache Monitoring

```bash
# Redis stats
docker exec -it fraud-redis redis-cli INFO stats

# Key distribution
docker exec -it fraud-redis redis-cli --scan --pattern "fraud:*" | wc -l

# Memory usage by prefix
docker exec -it fraud-redis redis-cli --bigkeys
```

### 3. Application-Level Optimizations

#### Async Processing

Enable async I/O for database and cache operations:

```python
# src/core/config.py
ENABLE_ASYNC_PROCESSING = True
ENABLE_CONNECTION_POOLING = True
```

#### Response Compression

Enable gzip compression for API responses:

```python
ENABLE_GZIP_COMPRESSION = True
GZIP_COMPRESSION_LEVEL = 6       # Balanced (1-9)
GZIP_MIN_SIZE = 1024             # Only compress >1KB
```

**Impact:** 60-70% reduction in response size for JSON

#### Worker Configuration

```python
API_WORKER_PROCESSES = 4         # CPU cores × 1-2
API_WORKER_CONNECTIONS = 1000    # Per worker
API_BACKLOG = 2048               # Pending connections
```

**Calculation:**
- 4 workers × 1000 connections = 4000 concurrent connections
- Suitable for 100+ req/sec throughput

---

## Horizontal Scaling

### Scaled Deployment Architecture

Deploy 3 API instances behind nginx load balancer:

```bash
# Start scaled deployment
docker-compose -f scaling/docker-compose-scaled.yml up -d

# Verify all instances are healthy
docker-compose -f scaling/docker-compose-scaled.yml ps

# Check nginx logs
docker-compose -f scaling/docker-compose-scaled.yml logs -f nginx
```

### Load Balancer Configuration

**Algorithm:** `least_conn` (least connections)
- Routes requests to instance with fewest active connections
- Better than round-robin for varying request durations
- Automatic failover on instance failure

**Health Checks:**
- Interval: 10s
- Timeout: 5s
- Retries: 3
- Endpoint: `/health`

**Rate Limiting:**
- Global: 100 req/min per IP
- Burst: 20 requests
- Max connections: 10 per IP

### Testing Scaled Deployment

```bash
# Run load test against load balancer
locust -f load_testing/locustfile.py \
       --host=http://localhost \
       --users 300 \
       --spawn-rate 30 \
       --run-time 10m \
       --headless

# Expected results:
# - Throughput: 300+ req/sec (3× single instance)
# - P95 Latency: <100ms (with load balancing)
# - Error Rate: <0.1%
```

### Monitoring Load Distribution

```bash
# Check which instances are handling requests
docker-compose -f scaling/docker-compose-scaled.yml logs nginx | grep upstream

# Expected distribution (roughly 33% each):
# upstream=api-1:3000
# upstream=api-2:3000
# upstream=api-3:3000

# Check individual instance metrics
curl http://localhost/metrics
```

### Failover Testing

```bash
# Stop one instance
docker stop fraud-api-1

# Verify traffic redistributes to api-2 and api-3
docker-compose -f scaling/docker-compose-scaled.yml logs -f nginx

# Expected behavior:
# - Nginx marks api-1 as down (max_fails=3, fail_timeout=30s)
# - Traffic routes to api-2 and api-3
# - No 503 errors (if 2 instances can handle load)

# Restart instance
docker start fraud-api-1

# Verify instance rejoins pool
docker-compose -f scaling/docker-compose-scaled.yml logs nginx | grep api-1
```

---

## Monitoring & Profiling

### Application Profiling

Use the profiling script to identify bottlenecks:

```bash
# Install profiling tools
cd performance/profiling
pip install -r requirements.txt

# Profile 100 requests
python profile_api.py --requests 100 --detailed

# Results saved to:
# - performance/profiling/results/summary_<timestamp>.txt
# - performance/profiling/results/hotspots_<timestamp>.txt
# - performance/profiling/results/profile_<timestamp>.prof
```

#### Analyzing Profiling Results

1. **Hotspots Report** (Top bottlenecks)
   ```bash
   cat performance/profiling/results/hotspots_<timestamp>.txt
   ```

   Look for:
   - Functions taking >1% of total time
   - High call counts (>1000 calls)
   - Slow functions (>10ms per call)

2. **Visual Analysis with SnakeViz**
   ```bash
   snakeviz performance/profiling/results/profile_<timestamp>.prof
   ```

   Opens interactive flamegraph in browser

3. **Call Graph Generation**
   ```bash
   gprof2dot -f pstats performance/profiling/results/profile_<timestamp>.prof | \
     dot -Tpng -o callgraph.png
   ```

### Prometheus Metrics

Access metrics endpoint:

```bash
curl http://localhost:3000/metrics
```

**Key Metrics:**

```prometheus
# Request duration histogram
fraud_api_request_duration_seconds_bucket{method="POST",path="/api/v1/fraud/score"}

# Request count
fraud_api_requests_total{method="POST",path="/api/v1/fraud/score",status="200"}

# ML inference duration
fraud_api_ml_inference_duration_seconds

# Cache hit rate
fraud_api_cache_hits_total / (fraud_api_cache_hits_total + fraud_api_cache_misses_total)

# Database query duration
fraud_api_db_query_duration_seconds
```

### Grafana Dashboards

If monitoring is enabled:

```bash
# Access Grafana
open http://localhost:3001

# Login: admin / admin

# Import dashboards from:
# monitoring/grafana/dashboards/
```

**Recommended Dashboards:**
1. **API Overview:** Request rate, latency, errors
2. **Cache Performance:** Hit rates, latency, memory
3. **Database Performance:** Query times, connection pool, slow queries
4. **System Resources:** CPU, memory, disk, network

---

## Troubleshooting

### High Latency (P95 > 100ms)

**Symptoms:**
- Slow API responses
- Timeout errors
- User complaints

**Diagnosis:**

```bash
# 1. Check profiling results
python performance/profiling/profile_api.py --requests 100

# 2. Check database query times
docker exec -it fraud-db psql -U fraud_user -d fraud_db
SELECT query, mean_time, calls
FROM pg_stat_statements
WHERE query LIKE '%transactions%'
ORDER BY mean_time DESC LIMIT 10;

# 3. Check cache hit rate
docker exec -it fraud-redis redis-cli INFO stats | grep keyspace
```

**Solutions:**

1. **Slow Database Queries:**
   ```bash
   # Apply query optimizations
   docker exec -it fraud-db psql -U fraud_user -d fraud_db \
     -f performance/optimization/query_optimization.sql

   # Add missing indexes
   docker exec -it fraud-db psql -U fraud_user -d fraud_db \
     -f performance/optimization/index_recommendations.sql
   ```

2. **Low Cache Hit Rate:**
   ```python
   # Increase L1 cache size
   CACHE_L1_MAX_SIZE = 5000  # src/core/config.py

   # Increase TTLs
   CACHE_VELOCITY_TTL = 120
   ```

3. **Connection Pool Exhaustion:**
   ```python
   # Increase pool size
   DATABASE_POOL_SIZE = 30
   DATABASE_MAX_OVERFLOW = 50
   ```

### High Error Rate (>0.1%)

**Symptoms:**
- 500 Internal Server Error
- 503 Service Unavailable
- Exception logs

**Diagnosis:**

```bash
# 1. Check application logs
docker-compose logs -f api

# 2. Check error distribution
docker-compose logs api | grep ERROR | head -20

# 3. Check Sentry (if configured)
# Review error dashboard
```

**Common Causes:**

1. **Database Connection Errors:**
   ```
   sqlalchemy.exc.TimeoutError: QueuePool limit exceeded
   ```
   **Solution:** Increase pool size or reduce connection leak

2. **Redis Connection Errors:**
   ```
   redis.exceptions.ConnectionError: Connection refused
   ```
   **Solution:** Check Redis health, increase connection pool

3. **ML Model Errors:**
   ```
   ValueError: Feature count mismatch
   ```
   **Solution:** Check feature extraction logic, model version

### Low Throughput (<80 req/sec)

**Symptoms:**
- Can't sustain target load
- Request queuing
- Increased latency under load

**Diagnosis:**

```bash
# 1. Check resource usage
docker stats

# 2. Check worker configuration
# Ensure API_WORKER_PROCESSES = 4

# 3. Check database connections
docker exec -it fraud-db psql -U fraud_user -d fraud_db \
  -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';"
```

**Solutions:**

1. **CPU-bound:**
   ```bash
   # Horizontal scaling
   docker-compose -f scaling/docker-compose-scaled.yml up -d
   ```

2. **I/O-bound:**
   ```python
   # Enable async processing
   ENABLE_ASYNC_PROCESSING = True

   # Increase worker connections
   API_WORKER_CONNECTIONS = 2000
   ```

3. **Database-bound:**
   ```sql
   -- Optimize slow queries
   -- Add indexes
   -- Enable query caching
   ```

### Memory Leaks

**Symptoms:**
- Gradual memory increase
- OOM kills
- Performance degradation over time

**Diagnosis:**

```bash
# Run endurance test
locust -f load_testing/locustfile.py \
       --host=http://localhost:3000 \
       --users 50 \
       --spawn-rate 5 \
       --run-time 60m \
       --headless

# Monitor memory
watch -n 5 'docker stats --no-stream'
```

**Solutions:**

1. **Cache Size Limits:**
   ```python
   CACHE_L1_MAX_SIZE = 2000  # Enforce eviction
   ```

2. **Connection Recycling:**
   ```python
   DATABASE_POOL_RECYCLE = 3600  # Recycle after 1 hour
   ```

3. **Graceful Restarts:**
   ```bash
   # Rolling restart (no downtime)
   docker-compose restart api-1
   sleep 30
   docker-compose restart api-2
   sleep 30
   docker-compose restart api-3
   ```

---

## Best Practices

### Development

1. **Always profile before optimizing**
   ```bash
   python performance/profiling/profile_api.py --requests 100
   ```

2. **Test with realistic data**
   - Use production-like transaction volumes
   - Include edge cases (high amounts, suspicious patterns)

3. **Monitor during development**
   - Check metrics after code changes
   - Run baseline tests to detect regressions

### Testing

1. **Run load tests before deployments**
   ```bash
   # Baseline → Normal → Stress
   locust -f load_testing/locustfile.py --host=http://localhost:3000 \
          --users 10 --spawn-rate 2 --run-time 5m --headless
   ```

2. **Validate SLA targets**
   - P95 < 100ms
   - P99 < 200ms
   - Error rate < 0.1%

3. **Test failover scenarios**
   - Stop instances
   - Database connection loss
   - Redis unavailability

### Production

1. **Enable monitoring**
   - Prometheus + Grafana
   - Sentry for errors
   - Custom alerts for SLA violations

2. **Regular maintenance**
   ```bash
   # Weekly: Refresh materialized views
   REFRESH MATERIALIZED VIEW CONCURRENTLY fraud_statistics_hourly;

   # Monthly: Rebuild indexes
   REINDEX TABLE CONCURRENTLY transactions;

   # Quarterly: Vacuum database
   VACUUM ANALYZE transactions;
   ```

3. **Capacity planning**
   - Monitor growth trends
   - Scale before hitting limits
   - Test at 2× expected peak load

4. **Performance regression prevention**
   - Run load tests in CI/CD
   - Compare against baseline
   - Alert on degradation >10%

### Scaling Strategy

1. **Vertical scaling first** (cheaper, simpler)
   - Increase CPU/memory
   - Optimize before scaling out

2. **Horizontal scaling second**
   - Add instances behind load balancer
   - Ensure stateless application design

3. **Database scaling last**
   - Read replicas for read-heavy workloads
   - Connection pooling and caching first
   - Consider managed database services

---

## Appendix

### Quick Reference

**Common Commands:**

```bash
# Start single instance
docker-compose up -d

# Start scaled deployment
docker-compose -f scaling/docker-compose-scaled.yml up -d

# Run baseline test
locust -f load_testing/locustfile.py --host=http://localhost:3000 \
       --users 10 --spawn-rate 2 --run-time 5m --headless

# Run stress test
locust -f load_testing/locustfile.py --host=http://localhost:3000 \
       --users 100 --spawn-rate 10 --run-time 10m --headless

# Profile API
python performance/profiling/profile_api.py --requests 100

# Apply database optimizations
docker exec -it fraud-db psql -U fraud_user -d fraud_db \
  -f performance/optimization/query_optimization.sql

# Check metrics
curl http://localhost:3000/metrics
```

### File Locations

| File | Purpose |
|------|---------|
| `load_testing/locustfile.py` | Main load test |
| `load_testing/scenarios/fraud_scoring.py` | Fraud-specific test |
| `load_testing/config/baseline.json` | Baseline metrics |
| `load_testing/config/targets.json` | Performance targets |
| `performance/optimization/query_optimization.sql` | DB optimizations |
| `performance/optimization/index_recommendations.sql` | Index analysis |
| `performance/profiling/profile_api.py` | Profiling script |
| `scaling/docker-compose-scaled.yml` | Scaled deployment |
| `scaling/nginx/nginx.conf` | Load balancer config |
| `src/core/config.py` | Application config |

### Performance Checklist

Before deploying to production:

- [ ] Run all test scenarios (baseline, normal, stress, spike, endurance)
- [ ] Verify P95 latency <100ms
- [ ] Verify P99 latency <200ms
- [ ] Verify error rate <0.1%
- [ ] Verify cache hit rate >90%
- [ ] Apply database optimizations
- [ ] Enable monitoring (Prometheus + Grafana)
- [ ] Configure alerts for SLA violations
- [ ] Test failover scenarios
- [ ] Document performance characteristics
- [ ] Set up automated load testing in CI/CD

---

**Document Version:** 1.0.0
**Last Updated:** 2025-01-25
**Next Review:** 2025-02-25

For questions or issues, contact: engineering@dygsom.pe
