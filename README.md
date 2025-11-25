# DYGSOM Fraud API 🛡️

Fraud detection API for e-commerce and fintech.

## Quick Start

```bash
# Start services
docker compose up -d

# Check health
curl http://localhost:3000/health

# View docs
open http://localhost:3000/docs
```

## Services

- API: http://localhost:3000
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## Development

```bash
# View logs
docker compose logs -f api

# Run migrations
docker compose exec api prisma migrate dev

# Run tests
docker compose exec api pytest
```
