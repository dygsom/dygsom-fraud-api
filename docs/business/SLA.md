# Service Level Agreement (SLA)

**Effective Date:** 2025-01-25
**Version:** 1.0.0

This Service Level Agreement describes the uptime, performance, and support commitments for the DYGSOM Fraud Detection API.

---

## Uptime SLA

### Commitment

DYGSOM commits to the following monthly uptime percentages:

| Tier | Uptime | Max Downtime/Month |
|------|--------|-------------------|
| Startup | 99.5% | 3.6 hours |
| Growth | 99.9% | 43.2 minutes |
| Enterprise | 99.95% | 21.6 minutes |

**Exclusions:** Scheduled maintenance (2 hours/month max, 7 days notice), client issues, force majeure.

---

## Performance SLA

### Response Time

| Metric | Target |
|--------|--------|
| P50 Latency | <50ms |
| P95 Latency | <100ms |
| P99 Latency | <200ms |
| Error Rate | <0.1% |

### Throughput

| Tier | Guaranteed RPS | Burst |
|------|----------------|-------|
| Startup | 50 RPS | 100 RPS |
| Growth | 200 RPS | 500 RPS |
| Enterprise | Custom | Custom |

---

## Support SLA

### Response Times

| Priority | Response Time | Channels |
|----------|---------------|----------|
| Critical (P0) | <30 minutes | Email, Phone (Enterprise) |
| High (P1) | <2 hours | Email |
| Medium (P2) | <4 hours | Email |
| Low (P3) | <24 hours | Email |

### Support by Tier

- **Startup:** 24/7 email support
- **Growth:** Priority email support
- **Enterprise:** 24/7 phone support + dedicated CSM

---

## SLA Credits

| Uptime Achieved | Credit |
|-----------------|--------|
| 99.0% - 99.9% | 10% of monthly fee |
| 95.0% - 99.0% | 25% of monthly fee |
| <95.0% | 50% of monthly fee |

**Maximum Credit:** 50% of monthly fee.

**To Claim:** Submit request within 30 days with incident details.

---

## Monitoring

- **Status Page:** https://status.dygsom.pe
- **Monthly Reports:** Enterprise tier only

---

## Contact

- **Support:** support@dygsom.pe
- **Emergency:** Include "[URGENT]" in subject (Enterprise)

**Version:** 1.0.0 | **Last Updated:** 2025-01-25
