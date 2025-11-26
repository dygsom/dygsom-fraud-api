# DYGSOM Fraud API - Grafana Dashboard Setup

## Dashboards to Create Manually

After starting Grafana (http://localhost:3001), login with:
- Username: `admin`
- Password: `admin`

### Dashboard 1: API Overview

**Panels:**

1. **Total Requests** (Stat)
   - Query: `sum(api_requests_total)`
   - Title: "Total Requests"

2. **Requests per Second** (Graph)
   - Query: `rate(api_requests_total[5m])`
   - Title: "Requests/sec"

3. **P95 Latency** (Graph)
   - Query: `histogram_quantile(0.95, rate(api_request_duration_seconds_bucket[5m]))`
   - Title: "P95 Latency"
   - Unit: seconds

4. **Error Rate** (Graph)
   - Query: `rate(api_request_errors_total[5m])`
   - Title: "Error Rate"

5. **Status Code Distribution** (Pie Chart)
   - Query: `sum by (status) (api_requests_total)`
   - Title: "Status Codes"

### Dashboard 2: ML Performance

**Panels:**

1. **Fraud Score Distribution** (Heatmap)
   - Query: `rate(fraud_score_distribution_bucket[5m])`
   - Title: "Fraud Score Distribution"

2. **Predictions per Second** (Graph)
   - Query: `rate(ml_predictions_total[5m])`
   - Title: "ML Predictions/sec"

3. **ML Latency** (Graph)
   - Query: `histogram_quantile(0.95, rate(ml_prediction_duration_seconds_bucket[5m]))`
   - Title: "ML Prediction Latency (P95)"
   - Unit: seconds

4. **Risk Levels** (Pie Chart)
   - Query: `sum by (risk_level) (risk_level_distribution_total)`
   - Title: "Risk Level Distribution"

5. **Model Used** (Stat)
   - Query: `ml_model_info`
   - Title: "Active Model"

### Dashboard 3: Business Metrics

**Panels:**

1. **Current Fraud Rate** (Gauge)
   - Query: `fraud_rate_percentage`
   - Title: "Fraud Rate %"
   - Thresholds: 0-5% green, 5-10% yellow, >10% red

2. **Transaction Volume** (Graph)
   - Query: `rate(transaction_volume_total[5m])`
   - Title: "Transaction Volume"

3. **Recommendations** (Pie Chart)
   - Query: `sum by (recommendation) (recommendation_distribution_total)`
   - Title: "Recommendation Distribution"

4. **High Risk Count** (Stat)
   - Query: `sum(risk_level_distribution_total{risk_level="HIGH"})`
   - Title: "High Risk Transactions"

5. **Transaction Amount** (Graph)
   - Query: `histogram_quantile(0.95, rate(transaction_amount_distribution_bucket[5m]))`
   - Title: "P95 Transaction Amount"

### Dashboard 4: Cache & Database

**Panels:**

1. **Cache Hit Rate** (Gauge)
   - Query: `sum(rate(cache_hits_total[5m])) / (sum(rate(cache_hits_total[5m])) + sum(rate(cache_misses_total[5m])))`
   - Title: "Cache Hit Rate"
   - Unit: percentunit

2. **Cache Latency** (Graph)
   - Query: `histogram_quantile(0.95, rate(cache_latency_seconds_bucket[5m]))`
   - Title: "Cache Latency (P95)"

3. **DB Connections** (Graph)
   - Query: `db_connections_active`
   - Title: "Active DB Connections"

4. **DB Query Latency** (Graph)
   - Query: `histogram_quantile(0.95, rate(db_query_duration_seconds_bucket[5m]))`
   - Title: "DB Query Latency (P95)"

## Quick Setup Commands

```bash
# Start all services
docker compose up -d

# Wait for services to be ready
sleep 10

# Check Prometheus
curl http://localhost:9090/-/healthy

# Check Grafana
curl http://localhost:3001/api/health

# Open Grafana
open http://localhost:3001
```

## Notes

- Grafana dashboards are provisioned automatically if JSON files are placed in `monitoring/grafana/dashboards/`
- Prometheus datasource is auto-configured via `monitoring/grafana/datasources/prometheus.yml`
- Alerts are defined in `monitoring/alerts/alert_rules.yml`
