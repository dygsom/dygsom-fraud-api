# 🧪 Guía de Pruebas - DYGSOM Fraud API

> **Nota importante**: Todos los tests usan `docker compose exec` - el ambiente está completamente dockerizado.

## 📋 Requisitos Previos

- ✅ Docker y Docker Compose instalados
- ✅ PowerShell 5.1+ (incluido en Windows)
- ✅ Servicios corriendo: `docker compose up -d`

## 🚀 Uso Rápido

Desde la raíz del proyecto:

```powershell
.\tests\scripts\run_tests.ps1
```

**Resultado esperado**: 15-16 pruebas exitosas

## 📊 Fases de Prueba

El script `run_tests.ps1` ejecuta **7 fases** con **16 pruebas**:

### 1️⃣ **Infraestructura**
- ✅ Docker Compose - Servicios corriendo
- ✅ PostgreSQL - Conexión disponible  
- ✅ Redis - Servicio disponible
- ✅ API Container - Estado healthy

### 2️⃣ **Health Checks**
- ✅ `/health` - Endpoint básico (200)
- ✅ `/health/ready` - Readiness check (200)
- ✅ `/metrics` - Endpoint público (200)

### 3️⃣ **Base de Datos**
- Aplicación de migraciones Prisma
- Creación de API Key de prueba

### 4️⃣ **Autenticación**
- ✅ Sin API Key → 401 Unauthorized
- ✅ Con API Key válida → 200 OK

### 5️⃣ **Fraud Scoring**
- ✅ Transacción LOW RISK (aprobada)
- ✅ Transacción HIGH RISK (rechazada/revisión)

### 6️⃣ **Performance**
- ✅ Latencia promedio < 300ms

### 7️⃣ **Monitoring**
- ✅ Prometheus (puerto 9090)
- ✅ Grafana (puerto 3002)
- ✅ Métricas API requests
- ✅ Métricas fraud score distribution

## 🔑 API Key de Prueba

**Key**: `dygsom_test_api_key_2024`  
**Rate Limit**: 100 requests/minuto  
**Nombre**: `test-key`

La API key se crea automáticamente al ejecutar `run_tests.ps1`.

## 📁 Archivos en `tests/scripts/`

1. **`run_tests.ps1`** - Suite automatizada de pruebas (PowerShell)
2. **`create_test_apikey.sql`** - Script SQL para crear API Key de prueba
3. **`README.md`** - Esta guía

```powershell
Get-Content tests\scripts\create_test_apikey.sql | docker compose exec -T postgres psql -U postgres -d dygsom
```

## Pruebas Manuales

### Verificar Health

```bash
curl http://localhost:3000/health
curl http://localhost:3000/health/ready
```

### Fraud Scoring LOW RISK

```bash
curl -X POST http://localhost:3000/api/v1/fraud/score \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dygsom_test_api_key_2024" \
  -d '{
    "transaction_id": "tx-001",
    "customer_email": "john@gmail.com",
    "customer_ip": "192.168.1.1",
    "amount": 100,
    "currency": "USD",
    "merchant_id": "m001",
    "card_bin": "424242",
    "device_id": "d001",
    "timestamp": "2024-01-01T12:00:00Z"
  }'
```

### Fraud Scoring HIGH RISK

```bash
curl -X POST http://localhost:3000/api/v1/fraud/score \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dygsom_test_api_key_2024" \
  -d '{
    "transaction_id": "tx-002",
    "customer_email": "bad@temp.com",
    "customer_ip": "45.67.89.1",
    "amount": 9000,
    "currency": "USD",
    "merchant_id": "m999",
    "card_bin": "555555",
    "device_id": "d999",
    "timestamp": "2024-01-01T12:00:00Z"
  }'
```

### Ver Métricas

```bash
curl http://localhost:3000/metrics
```

### Verificar Prometheus

```bash
curl http://localhost:9090
```

### Verificar Grafana

```bash
curl http://localhost:3001
```

Login: `admin` / `admin`

## Troubleshooting

### Error: Cannot connect to Docker

```powershell
docker compose ps
```

Si no hay servicios corriendo:

```powershell
docker compose up -d
```

### Error: API no responde

Verificar logs:

```powershell
docker compose logs api
```

### Error: PostgreSQL no acepta conexiones

Reiniciar servicios:

```powershell
docker compose restart postgres
docker compose restart api
```

### Error: API Key no existe

Ejecutar manualmente:

```powershell
Get-Content tests\scripts\create_test_apikey.sql | docker compose exec -T postgres psql -U postgres -d dygsom
```

### Limpiar y reiniciar todo

```powershell
docker compose down -v
docker compose build api
docker compose up -d
Start-Sleep -Seconds 15
.\tests\scripts\run_tests.ps1
```

## Resultados Esperados

✅ **15-17 pruebas exitosas**

- Infraestructura: 4 tests
- Health checks: 3 tests
- Autenticación: 2 tests
- Fraud scoring: 2 tests
- Performance: 1 test
- Monitoring: 4 tests

## URLs del Sistema

| Servicio | URL | Credenciales |
|----------|-----|--------------|
| API | http://localhost:3000 | API Key requerida |
| Docs | http://localhost:3000/docs | Público |
| Metrics | http://localhost:3000/metrics | Público |
| Prometheus | http://localhost:9090 | Público |
| Grafana | http://localhost:3001 | admin/admin |

## Notas

- El script es idempotente (puede ejecutarse múltiples veces)
- Las migraciones Prisma se aplican automáticamente
- La API key se crea solo si no existe
- Los tests de performance miden latencia promedio de 5 requests
- Latencia esperada: < 300ms promedio
