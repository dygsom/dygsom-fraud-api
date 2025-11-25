# Instrucciones para GitHub Copilot - DYGSOM Fraud API - DÍA 3

## 🎯 Fase Actual: DÍA 3 - Core Endpoint + Integración ML

### Objetivos del Día 3

**CRÍTICO: Implementar endpoint POST /api/v1/fraud/score funcionando end-to-end**

---

## 📍 Estado Actual del Proyecto

### ✅ Ya Completado (Día 1-2)
- FastAPI básico funcionando
- Docker Compose con PostgreSQL + Redis
- Prisma schema completo
- Repository layer implementado
- Service layer básico
- DTOs básicos

### 🎯 A Implementar HOY (Día 3)
1. DTOs completos para fraud scoring
2. Endpoint `/api/v1/fraud/score` con validación
3. Integración de ML model en FraudService
4. Tests E2E del flujo completo
5. Verificar latencia <200ms

---

## 🚫 GUARDRAILS (Recordatorio)

### ❌ Prohibido
- `any` type
- Magic numbers/strings
- `print()` (usar logger)
- Hardcoded secrets
- Passwords sin hashear
- Operaciones blocking

### ✅ Obligatorio
- Type hints siempre
- Async/await
- Pydantic validation
- Logging estructurado
- Exception handling
- Docstrings

---

## 📐 Estructura de Archivos para Hoy

```
src/
├── api/
│   └── v1/
│       ├── endpoints/
│       │   └── fraud.py          ← CREAR HOY
│       └── router.py             ← ACTUALIZAR
├── schemas/
│   └── fraud_schemas.py          ← CREAR HOY
├── services/
│   └── fraud_service.py          ← EXPANDIR
├── dependencies.py               ← CREAR HOY
└── ml/
    ├── ml_service.py             ← CREAR HOY
    └── feature_extractor.py      ← CREAR HOY

tests/
└── test_fraud_endpoint.py        ← CREAR HOY
```

---

## 📊 Schema del Request/Response

### Request: POST /api/v1/fraud/score

```json
{
  "transaction_id": "txn_abc123",
  "amount": 150.00,
  "currency": "PEN",
  "timestamp": "2024-11-27T10:30:00Z",
  "customer": {
    "id": "cust_123",
    "email": "user@example.com",
    "phone": "+51987654321",
    "ip_address": "181.65.123.45",
    "device_fingerprint": "fp_xyz789"
  },
  "payment_method": {
    "type": "credit_card",
    "bin": "411111",
    "last4": "1111",
    "brand": "Visa"
  }
}
```

### Response: 200 OK

```json
{
  "transaction_id": "txn_abc123",
  "fraud_score": 0.23,
  "risk_level": "LOW",
  "recommendation": "APPROVE",
  "reasons": ["Normal spending pattern", "Known device"],
  "flags": [],
  "processing_time_ms": 87,
  "model_version": "v1.0.0",
  "timestamp": "2024-11-27T10:30:00.087Z"
}
```
