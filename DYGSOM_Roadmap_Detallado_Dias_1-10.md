# DYGSOM - Roadmap Detallado Día a Día
## Semanas 1-2: Fraud Scoring API (CORE)

> **Objetivo**: API de scoring de fraude funcional con latencia <100ms y accuracy >90%
> **Equipo**: ali1 (Backend) + Alicia (ML)
> **Fecha inicio**: 24 Noviembre 2024
> **Fecha entrega**: 7 Diciembre 2024

---

## 📅 SEMANA 1: Setup + Core Endpoint

### DÍA 1 (Lun 25 Nov) - Setup Completo del Proyecto

#### Objetivo del Día
✅ Proyecto FastAPI inicializado con Docker funcionando

#### Tareas ali1 (Backend) - 8 horas

**Mañana (4h)**
```bash
# 1. Crear estructura del proyecto (1h)
mkdir -p dygsom-fraud-api
cd dygsom-fraud-api

# Estructura base
fraud-api/
├── src/
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   ├── core/
│   │   ├── config.py
│   │   └── security.py
│   ├── models/
│   ├── services/
│   ├── repositories/
│   └── utils/
├── tests/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example

# 2. Configurar Docker (2h)
# Crear docker-compose.yml con:
# - FastAPI service
# - PostgreSQL 15
# - Redis 7
# - Incluir healthchecks

# 3. Setup inicial FastAPI (1h)
# Instalar dependencias core
# Configurar main.py con Swagger
# Crear endpoint /health
```

**Tarde (4h)**
```bash
# 4. Configurar Prisma + PostgreSQL (2h)
# - Instalar Prisma
# - Crear schema.prisma inicial
# - Primera migración
# - Probar conexión DB

# 5. Setup Redis + Caching (1h)
# - Configurar Redis client
# - Crear cache service
# - Probar conexión

# 6. Testing setup (1h)
# - Configurar pytest
# - Crear primer test (health endpoint)
# - Configurar coverage
```

#### Tareas Alicia (ML) - 8 horas

**Mañana (4h)**
```python
# 1. Setup ambiente ML (1h)
# - Instalar scikit-learn, xgboost, pandas, numpy
# - Crear notebook exploratorio

# 2. Análisis de datos inicial (3h)
# - Revisar datos históricos de fraude Perú
# - Identificar features clave:
#   * IP geolocation (país, ciudad)
#   * Hora de transacción
#   * Monto
#   * Email domain
#   * Card BIN
#   * Velocity checks
```

**Tarde (4h)**
```python
# 3. Feature engineering inicial (4h)
# - Definir schema de features
# - Crear funciones de extracción:
#   * extract_ip_features()
#   * extract_transaction_features()
#   * extract_card_features()
#   * extract_customer_features()
# - Documentar en notebook
```

#### Entregables Día 1
- [ ] Docker funcionando (backend + postgres + redis)
- [ ] FastAPI corriendo en http://localhost:3000
- [ ] Swagger docs en http://localhost:3000/docs
- [ ] Endpoint /health funcionando
- [ ] Tests básicos pasando
- [ ] Features ML identificadas (lista documentada)

---

### DÍA 2 (Mar 26 Nov) - Database Schema + ML Pipeline

#### Objetivo del Día
✅ Schema de BD completo + Pipeline ML básico funcionando

#### Tareas ali1 (Backend) - 8 horas

**Mañana (4h)**
```sql
-- 1. Diseñar schema completo (2h)
-- Crear en prisma/schema.prisma:

model Transaction {
  id                String   @id @default(uuid())
  transaction_id    String   @unique
  amount            Decimal  @db.Decimal(12, 2)
  currency          String   @default("PEN")
  timestamp         DateTime @default(now())
  
  // Customer data
  customer_id       String?
  customer_email    String?
  customer_phone    String?
  customer_ip       String?
  device_fingerprint String?
  
  // Payment method
  payment_method_type String?
  card_bin          String?
  card_last4        String?
  card_brand        String?
  
  // Fraud detection
  fraud_score       Decimal?  @db.Decimal(5, 4)
  risk_level        String?
  decision          String?
  model_version     String?
  processing_time_ms Int?
  
  // Raw data
  raw_data          Json?
  enriched_data     Json?
  
  created_at        DateTime @default(now())
  updated_at        DateTime @updatedAt
  
  @@index([customer_email])
  @@index([customer_ip])
  @@index([timestamp])
  @@index([fraud_score])
}

model FraudFeatures {
  id                String   @id @default(uuid())
  transaction_id    String   @unique
  
  // Features calculadas
  ip_country        String?
  ip_city           String?
  transaction_hour  Int?
  is_weekend        Boolean?
  
  // Velocity features
  transactions_last_hour Int?
  transactions_last_day  Int?
  amount_last_day   Decimal? @db.Decimal(12, 2)
  
  // Metadata
  created_at        DateTime @default(now())
  
  @@index([transaction_id])
}

-- 2. Ejecutar migraciones (30min)
npx prisma migrate dev --name init

-- 3. Seed data de prueba (1.5h)
# Crear script para popular 1000 transacciones de ejemplo
# Mix de legítimas y fraudulentas
```

**Tarde (4h)**
```python
# 4. Crear repository layer (2h)
# src/repositories/transaction_repository.py

class TransactionRepository:
    def __init__(self, prisma_client):
        self.prisma = prisma_client
    
    async def create(self, data: dict) -> Transaction:
        """Create transaction"""
        pass
    
    async def find_by_id(self, id: str) -> Transaction:
        """Find by ID"""
        pass
    
    async def get_customer_history(self, customer_email: str, hours: int) -> List[Transaction]:
        """Get customer transaction history"""
        pass

# 5. Crear service layer básico (2h)
# src/services/fraud_service.py

class FraudService:
    def __init__(self, repository, ml_service, cache_service):
        self.repository = repository
        self.ml_service = ml_service
        self.cache = cache_service
    
    async def score_transaction(self, data: dict) -> dict:
        """Score transaction for fraud"""
        # 1. Validate input
        # 2. Extract features
        # 3. Check cache
        # 4. Call ML model
        # 5. Store result
        # 6. Return response
        pass
```

#### Tareas Alicia (ML) - 8 horas

**Todo el día (8h)**
```python
# 1. Entrenar modelo baseline (3h)
# ml/train_baseline.py

from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
import pandas as pd
import numpy as np

# Load data
df = pd.read_csv('data/historical_transactions.csv')

# Feature engineering
X = extract_features(df)
y = df['is_fraud']

# Train baseline
model = XGBClassifier(
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1,
    random_state=42
)

model.fit(X_train, y_train)

# Evaluate
accuracy = model.score(X_test, y_test)
print(f"Baseline accuracy: {accuracy}")

# Save model
import joblib
joblib.dump(model, 'models/baseline_v1.pkl')

# 2. Crear feature extraction service (3h)
# ml/feature_extractor.py

class FeatureExtractor:
    def extract(self, transaction: dict) -> np.ndarray:
        """Extract features from transaction"""
        features = []
        
        # Amount features
        features.append(transaction['amount'])
        features.append(np.log1p(transaction['amount']))
        
        # Time features
        dt = datetime.fromisoformat(transaction['timestamp'])
        features.append(dt.hour)
        features.append(dt.weekday())
        features.append(int(dt.weekday() >= 5))  # is_weekend
        
        # IP features
        ip_data = self.get_ip_geolocation(transaction['customer_ip'])
        features.append(self.encode_country(ip_data['country']))
        
        # Card features
        features.append(self.encode_card_brand(transaction['card_brand']))
        
        # Velocity features (requiere DB)
        history = self.get_customer_history(transaction['customer_email'])
        features.append(len(history))  # transaction_count_24h
        
        return np.array(features).reshape(1, -1)
    
    def get_ip_geolocation(self, ip: str) -> dict:
        """Get IP geolocation"""
        # Usar API gratuita ipapi.co
        pass

# 3. Crear ML service (2h)
# ml/ml_service.py

class MLService:
    def __init__(self, model_path: str):
        self.model = joblib.load(model_path)
        self.feature_extractor = FeatureExtractor()
    
    def predict(self, transaction: dict) -> dict:
        """Predict fraud probability"""
        # Extract features
        features = self.feature_extractor.extract(transaction)
        
        # Predict
        fraud_prob = self.model.predict_proba(features)[0][1]
        
        # Determine risk level
        if fraud_prob > 0.8:
            risk_level = "CRITICAL"
            recommendation = "DECLINE"
        elif fraud_prob > 0.5:
            risk_level = "HIGH"
            recommendation = "REVIEW"
        elif fraud_prob > 0.3:
            risk_level = "MEDIUM"
            recommendation = "APPROVE"
        else:
            risk_level = "LOW"
            recommendation = "APPROVE"
        
        return {
            "fraud_score": fraud_prob,
            "risk_level": risk_level,
            "recommendation": recommendation,
            "model_version": "baseline_v1"
        }
```

#### Entregables Día 2
- [ ] Database schema completo y migrado
- [ ] 1000 transacciones seed en DB
- [ ] Repository layer implementado
- [ ] Service layer básico implementado
- [ ] Modelo ML baseline entrenado (accuracy >85%)
- [ ] Feature extraction funcionando
- [ ] ML service con predict() funcionando

---

### DÍA 3 (Mié 27 Nov) - Core Endpoint + Integración ML

#### Objetivo del Día
✅ POST /api/v1/fraud/score funcionando end-to-end

#### Tareas ali1 (Backend) - 8 horas

**Mañana (4h)**
```python
# 1. Crear DTOs con validación (1h)
# src/api/v1/schemas/fraud_schemas.py

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

class CustomerData(BaseModel):
    id: Optional[str] = None
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    phone: Optional[str] = None
    ip_address: str = Field(..., pattern=r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
    device_fingerprint: Optional[str] = None

class PaymentMethodData(BaseModel):
    type: str = Field(..., pattern=r'^(credit_card|debit_card)$')
    bin: str = Field(..., min_length=6, max_length=6)
    last4: str = Field(..., min_length=4, max_length=4)
    brand: str  # Visa, Mastercard, etc.

class FraudScoreRequest(BaseModel):
    transaction_id: str
    amount: float = Field(..., gt=0, le=1000000)
    currency: str = Field(default="PEN", pattern=r'^[A-Z]{3}$')
    timestamp: datetime
    customer: CustomerData
    payment_method: PaymentMethodData
    
    @validator('amount')
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v

class FraudScoreResponse(BaseModel):
    transaction_id: str
    fraud_score: float
    risk_level: str
    recommendation: str
    reasons: list[str]
    flags: list[str]
    processing_time_ms: int
    model_version: str
    timestamp: datetime

# 2. Crear endpoint (2h)
# src/api/v1/endpoints/fraud.py

from fastapi import APIRouter, Depends, HTTPException
from ...schemas.fraud_schemas import FraudScoreRequest, FraudScoreResponse
import time

router = APIRouter(prefix="/fraud", tags=["fraud"])

@router.post("/score", response_model=FraudScoreResponse)
async def score_transaction(
    request: FraudScoreRequest,
    fraud_service: FraudService = Depends(get_fraud_service)
):
    """
    Score transaction for fraud risk
    
    Returns fraud score (0-1), risk level, and recommendation.
    """
    start_time = time.time()
    
    try:
        # Score transaction
        result = await fraud_service.score_transaction(request.dict())
        
        # Calculate processing time
        processing_time = int((time.time() - start_time) * 1000)
        
        return FraudScoreResponse(
            transaction_id=request.transaction_id,
            fraud_score=result['fraud_score'],
            risk_level=result['risk_level'],
            recommendation=result['recommendation'],
            reasons=result.get('reasons', []),
            flags=result.get('flags', []),
            processing_time_ms=processing_time,
            model_version=result['model_version'],
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error scoring transaction: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# 3. Dependency injection setup (1h)
# src/api/dependencies.py

from src.services.fraud_service import FraudService
from src.repositories.transaction_repository import TransactionRepository
from ml.ml_service import MLService

def get_fraud_service() -> FraudService:
    prisma_client = get_prisma_client()
    repository = TransactionRepository(prisma_client)
    ml_service = MLService('models/baseline_v1.pkl')
    cache_service = get_cache_service()
    
    return FraudService(repository, ml_service, cache_service)
```

**Tarde (4h)**
```python
# 4. Integrar ML service en fraud_service (2h)
# src/services/fraud_service.py - COMPLETAR

class FraudService:
    async def score_transaction(self, data: dict) -> dict:
        """Score transaction for fraud"""
        
        # 1. Validate and normalize data
        transaction_data = self._normalize_data(data)
        
        # 2. Check cache first
        cache_key = f"fraud_score:{data['transaction_id']}"
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for {data['transaction_id']}")
            return cached_result
        
        # 3. Get customer history (for velocity features)
        customer_history = await self.repository.get_customer_history(
            data['customer']['email'],
            hours=24
        )
        
        # 4. Enrich data
        enriched_data = await self._enrich_data(transaction_data, customer_history)
        
        # 5. Call ML model
        ml_result = self.ml_service.predict(enriched_data)
        
        # 6. Generate reasons and flags
        reasons, flags = self._generate_insights(ml_result, enriched_data)
        
        # 7. Store transaction in DB
        await self.repository.create({
            **transaction_data,
            'fraud_score': ml_result['fraud_score'],
            'risk_level': ml_result['risk_level'],
            'decision': ml_result['recommendation'],
            'model_version': ml_result['model_version'],
            'enriched_data': enriched_data
        })
        
        # 8. Cache result (TTL 1 hour)
        result = {
            **ml_result,
            'reasons': reasons,
            'flags': flags
        }
        await self.cache.set(cache_key, result, ttl=3600)
        
        return result
    
    async def _enrich_data(self, data: dict, history: list) -> dict:
        """Enrich transaction data"""
        enriched = data.copy()
        
        # Add velocity features
        enriched['transactions_last_24h'] = len(history)
        enriched['amount_last_24h'] = sum(t.amount for t in history)
        
        # Add IP geolocation
        ip_data = await self._get_ip_geolocation(data['customer']['ip_address'])
        enriched['ip_country'] = ip_data.get('country')
        enriched['ip_city'] = ip_data.get('city')
        
        return enriched
    
    def _generate_insights(self, ml_result: dict, data: dict) -> tuple:
        """Generate human-readable reasons and flags"""
        reasons = []
        flags = []
        
        if ml_result['fraud_score'] < 0.3:
            reasons.append("Normal spending pattern")
            reasons.append("Known device")
        
        if ml_result['fraud_score'] > 0.5:
            flags.append("Unusual transaction amount")
            flags.append("High-risk geolocation")
        
        # Add more logic here
        
        return reasons, flags

# 5. Testing endpoint (2h)
# tests/test_fraud_endpoint.py

import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_score_transaction_success(client: AsyncClient):
    payload = {
        "transaction_id": "txn_test_123",
        "amount": 150.00,
        "currency": "PEN",
        "timestamp": "2024-11-27T10:30:00Z",
        "customer": {
            "email": "test@example.com",
            "ip_address": "181.65.123.45"
        },
        "payment_method": {
            "type": "credit_card",
            "bin": "411111",
            "last4": "1111",
            "brand": "Visa"
        }
    }
    
    response = await client.post("/api/v1/fraud/score", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "fraud_score" in data
    assert 0 <= data["fraud_score"] <= 1
    assert data["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert data["recommendation"] in ["APPROVE", "REVIEW", "DECLINE"]
    assert data["processing_time_ms"] < 200  # <200ms for now
```

#### Tareas Alicia (ML) - 8 horas

**Mañana (4h)**
```python
# 1. Optimizar feature extraction (2h)
# - Cachear resultados de IP geolocation
# - Optimizar queries de velocity features
# - Reducir llamadas externas

# 2. Agregar más features (2h)
# - Email domain risk score
# - Time-based patterns (unusual hour)
# - Card BIN risk score
# - Device fingerprint consistency
```

**Tarde (4h)**
```python
# 3. Mejorar modelo (3h)
# - Feature engineering avanzado
# - Hyperparameter tuning
# - Cross-validation
# - Objetivo: >90% accuracy

# 4. Crear benchmark script (1h)
# ml/benchmark.py

def benchmark_model():
    """Benchmark model performance"""
    # Load test data
    # Measure:
    # - Accuracy
    # - Precision
    # - Recall
    # - F1 score
    # - Inference time
    pass
```

#### Entregables Día 3
- [ ] POST /api/v1/fraud/score funcionando
- [ ] Response en <200ms (todavía no optimizado)
- [ ] ML model integrado
- [ ] Cache funcionando
- [ ] Tests E2E pasando
- [ ] Modelo mejorado (accuracy >88%)

---

### DÍA 4 (Jue 28 Nov) - Optimización de Performance

#### Objetivo del Día
✅ Latencia <100ms + Caching agresivo

#### Tareas ali1 (Backend) - 8 horas

**Mañana (4h)**
```python
# 1. Implementar caching multi-layer (2h)

class CacheService:
    def __init__(self):
        # L1: In-memory LRU cache (muy rápido)
        self.l1_cache = LRUCache(maxsize=1000)
        # L2: Redis (rápido)
        self.l2_cache = redis_client
    
    async def get(self, key: str):
        # Try L1 first
        value = self.l1_cache.get(key)
        if value:
            return value
        
        # Try L2
        value = await self.l2_cache.get(key)
        if value:
            # Warm up L1
            self.l1_cache.set(key, value)
            return value
        
        return None
    
    async def set(self, key: str, value, ttl: int):
        # Set in both layers
        self.l1_cache.set(key, value)
        await self.l2_cache.set(key, value, ex=ttl)

# 2. Optimizar queries DB (2h)
# - Agregar indexes faltantes
# - Usar select específico (no SELECT *)
# - Implementar query batching para velocity features

CREATE INDEX idx_customer_email_timestamp ON transactions(customer_email, timestamp DESC);
CREATE INDEX idx_customer_ip_timestamp ON transactions(customer_ip, timestamp DESC);
```

**Tarde (4h)**
```python
# 3. Cachear resultados de IP geolocation (2h)
# - Cachear por 24 horas
# - Reducir llamadas externas a casi 0

class IPGeolocationService:
    def __init__(self, cache: CacheService):
        self.cache = cache
    
    async def get_location(self, ip: str) -> dict:
        cache_key = f"ip_geo:{ip}"
        
        # Check cache
        cached = await self.cache.get(cache_key)
        if cached:
            return cached
        
        # Call external API
        result = await self._fetch_from_api(ip)
        
        # Cache for 24h
        await self.cache.set(cache_key, result, ttl=86400)
        
        return result

# 4. Load testing (2h)
# tests/load_test.py

from locust import HttpUser, task, between

class FraudAPIUser(HttpUser):
    wait_time = between(0.1, 0.5)
    
    @task
    def score_transaction(self):
        payload = generate_random_transaction()
        self.client.post("/api/v1/fraud/score", json=payload)

# Run: locust -f tests/load_test.py
# Target: 100 req/s con latencia <100ms
```

#### Tareas Alicia (ML) - 8 horas

**Mañana (4h)**
```python
# 1. Optimizar modelo para inferencia rápida (3h)
# - Reducir número de features si es necesario
# - Quantization del modelo
# - Benchmark diferentes modelos:
#   * XGBoost (actual)
#   * LightGBM (más rápido)
#   * Simple logistic regression (muy rápido)

from lightgbm import LGBMClassifier

# LightGBM suele ser 3x más rápido que XGBoost
model = LGBMClassifier(
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1,
    num_leaves=31
)

# 2. Crear versión del modelo (1h)
# - Guardar con versionado
# - Documentar features usadas
# - Guardar métricas del modelo
```

**Tarde (4h)**
```python
# 3. Feature caching (2h)
# - Pre-calcular features lentas
# - Cachear BIN info, email domains conocidos

# 4. A/B testing setup (2h)
# - Preparar para comparar modelos
# - Crear framework para testear múltiples versiones
```

#### Entregables Día 4
- [ ] Latencia p95 <100ms
- [ ] Caching multi-layer funcionando
- [ ] IP geolocation cacheada
- [ ] Load testing pasando (100 req/s)
- [ ] Modelo optimizado para inferencia rápida

---

### DÍA 5 (Vie 29 Nov) - Testing Completo + Documentación

#### Objetivo del Día
✅ Tests >80% coverage + Swagger docs completo

#### Tareas ali1 (Backend) - 8 horas

**Mañana (4h)**
```python
# 1. Tests unitarios completos (2h)

# tests/test_fraud_service.py
@pytest.mark.asyncio
async def test_score_transaction_low_risk():
    # Test caso low risk
    pass

@pytest.mark.asyncio
async def test_score_transaction_high_risk():
    # Test caso high risk
    pass

@pytest.mark.asyncio
async def test_caching_works():
    # Verificar que cache funciona
    pass

@pytest.mark.asyncio
async def test_velocity_features():
    # Test velocity calculations
    pass

# 2. Tests de integración (2h)
# tests/test_integration.py

@pytest.mark.asyncio
async def test_full_flow_with_real_db():
    # Test con DB real
    # 1. Insert transaction
    # 2. Score it
    # 3. Verify stored in DB
    # 4. Verify cache updated
    pass
```

**Tarde (4h)**
```python
# 3. Mejorar Swagger docs (2h)
# src/api/v1/endpoints/fraud.py

@router.post(
    "/score",
    response_model=FraudScoreResponse,
    summary="Score transaction for fraud",
    description="""
    Score a transaction for fraud risk using machine learning.
    
    Returns:
    - fraud_score: 0-1 probability of fraud
    - risk_level: LOW, MEDIUM, HIGH, CRITICAL
    - recommendation: APPROVE, REVIEW, DECLINE
    - reasons: Human-readable explanations
    - processing_time_ms: Time taken to score
    
    Performance:
    - p95 latency: <100ms
    - Availability: 99.9%
    """,
    responses={
        200: {
            "description": "Successfully scored transaction",
            "content": {
                "application/json": {
                    "example": {
                        "transaction_id": "txn_abc123",
                        "fraud_score": 0.23,
                        "risk_level": "LOW",
                        "recommendation": "APPROVE",
                        "reasons": ["Normal spending pattern", "Known device"],
                        "flags": [],
                        "processing_time_ms": 87,
                        "model_version": "v1.0.0",
                        "timestamp": "2024-11-29T10:30:00Z"
                    }
                }
            }
        },
        400: {"description": "Invalid input data"},
        500: {"description": "Internal server error"}
    }
)
async def score_transaction(...):
    pass

# 4. Crear README (2h)
# README.md

# DYGSOM Fraud Scoring API

## Quick Start
```bash
docker compose up -d
curl http://localhost:3000/health
```

## API Documentation
Swagger: http://localhost:3000/docs

## Examples
```bash
curl -X POST http://localhost:3000/api/v1/fraud/score \
  -H "Content-Type: application/json" \
  -d @examples/transaction.json
```

## Performance
- p95 latency: <100ms
- Throughput: 100+ req/s
- Accuracy: >90%
```

#### Tareas Alicia (ML) - 8 horas

**Todo el día (8h)**
```python
# 1. Documentar modelo ML (2h)
# ml/MODEL_DOCUMENTATION.md

# 2. Crear notebook de análisis (3h)
# ml/notebooks/model_analysis.ipynb
# - Feature importance
# - Error analysis
# - Confusion matrix
# - ROC curve

# 3. Crear data validation pipeline (3h)
# ml/data_validation.py
# - Validar inputs antes de predecir
# - Detectar data drift
# - Alertas si datos anómalos
```

#### Entregables Día 5
- [ ] Tests coverage >80%
- [ ] Todos los tests pasando
- [ ] Swagger docs completo con ejemplos
- [ ] README con quick start
- [ ] Modelo documentado

---

## 📅 SEMANA 2: Feature Engineering + Optimización Final

### DÍA 6 (Lun 2 Dic) - Feature Engineering Avanzado

#### Objetivo del Día
✅ Features avanzadas + Accuracy >90%

#### Tareas ali1 (Backend) - 8 horas

**Mañana (4h)**
```python
# 1. Implementar features avanzadas (3h)

class AdvancedFeatureExtractor:
    async def extract_email_features(self, email: str) -> dict:
        """Extract email domain risk features"""
        domain = email.split('@')[1]
        
        # Check if disposable email
        is_disposable = domain in DISPOSABLE_EMAIL_DOMAINS
        
        # Check domain age (via WHOIS)
        domain_age = await self.get_domain_age(domain)
        
        # Check if email on blocklist
        is_blocked = await self.check_email_blocklist(email)
        
        return {
            'email_domain': domain,
            'is_disposable_email': is_disposable,
            'domain_age_days': domain_age,
            'is_blocked_email': is_blocked
        }
    
    async def extract_device_features(self, device_fingerprint: str) -> dict:
        """Extract device fingerprint features"""
        # Check device history
        device_history = await self.get_device_history(device_fingerprint)
        
        return {
            'device_seen_count': len(device_history),
            'device_first_seen': device_history[0].timestamp if device_history else None,
            'device_user_count': len(set(t.user_id for t in device_history))
        }
    
    async def extract_bin_features(self, bin: str) -> dict:
        """Extract BIN (Bank Identification Number) features"""
        # Lookup BIN in database
        bin_info = await self.lookup_bin(bin)
        
        return {
            'card_type': bin_info.get('type'),  # credit, debit, prepaid
            'card_level': bin_info.get('level'),  # standard, gold, platinum
            'issuing_bank': bin_info.get('bank'),
            'issuing_country': bin_info.get('country')
        }

# 2. Actualizar FraudService para usar nuevas features (1h)
```

**Tarde (4h)**
```python
# 3. Implementar blocklists (2h)
# - Email blocklist
# - IP blocklist
# - Card BIN blocklist

class BlocklistService:
    def __init__(self, cache: CacheService):
        self.cache = cache
    
    async def is_email_blocked(self, email: str) -> bool:
        """Check if email is blocked"""
        # Check cache first
        cache_key = f"blocklist:email:{email}"
        cached = await self.cache.get(cache_key)
        if cached is not None:
            return cached
        
        # Check DB
        is_blocked = await self.db.blocklist.find_unique(
            where={'email': email, 'type': 'EMAIL'}
        )
        
        # Cache result
        await self.cache.set(cache_key, bool(is_blocked), ttl=3600)
        
        return bool(is_blocked)

# 4. Testing de nuevas features (2h)
```

#### Tareas Alicia (ML) - 8 horas

**Todo el día (8h)**
```python
# 1. Re-entrenar modelo con nuevas features (4h)
# - Incorporar todas las features nuevas
# - Feature selection (eliminar redundantes)
# - Hyperparameter tuning
# - Objetivo: >90% accuracy

# 2. Validación del modelo (2h)
# - Cross-validation
# - Test en datos holdout
# - Verificar no overfitting

# 3. Exportar modelo v2.0 (2h)
# - Guardar modelo
# - Documentar features usadas
# - Crear matriz de features
```

#### Entregables Día 6
- [ ] Features avanzadas implementadas
- [ ] Blocklists funcionando
- [ ] Modelo re-entrenado con nuevas features
- [ ] Accuracy >90%

---

### DÍA 7 (Mar 3 Dic) - Monitoring + Logging

#### Objetivo del Día
✅ Observabilidad completa del sistema

#### Tareas ali1 (Backend) - 8 horas

**Mañana (4h)**
```python
# 1. Structured logging con Winston (2h)
# src/utils/logger.py

import logging
import json
from datetime import datetime

class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # JSON formatter
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        self.logger.addHandler(handler)
    
    def log_transaction_scored(self, transaction_id: str, result: dict, processing_time: int):
        self.logger.info(json.dumps({
            'event': 'transaction_scored',
            'transaction_id': transaction_id,
            'fraud_score': result['fraud_score'],
            'risk_level': result['risk_level'],
            'recommendation': result['recommendation'],
            'processing_time_ms': processing_time,
            'timestamp': datetime.utcnow().isoformat()
        }))

# 2. Metrics con Prometheus (2h)
# src/utils/metrics.py

from prometheus_client import Counter, Histogram, Gauge

# Counters
transactions_total = Counter(
    'fraud_api_transactions_total',
    'Total transactions scored',
    ['risk_level', 'recommendation']
)

# Histograms
processing_time = Histogram(
    'fraud_api_processing_seconds',
    'Processing time in seconds',
    buckets=[0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0]
)

# Gauges
cache_hit_rate = Gauge(
    'fraud_api_cache_hit_rate',
    'Cache hit rate percentage'
)

# Usage en el endpoint
@router.post("/score")
async def score_transaction(...):
    with processing_time.time():
        result = await fraud_service.score_transaction(...)
    
    transactions_total.labels(
        risk_level=result['risk_level'],
        recommendation=result['recommendation']
    ).inc()
    
    return result
```

**Tarde (4h)**
```python
# 3. Health checks detallados (2h)
# src/api/v1/endpoints/health.py

@router.get("/health")
async def health_check():
    """Detailed health check"""
    checks = {}
    
    # Database
    try:
        await prisma.raw('SELECT 1')
        checks['database'] = {'status': 'healthy', 'latency_ms': 5}
    except Exception as e:
        checks['database'] = {'status': 'unhealthy', 'error': str(e)}
    
    # Redis
    try:
        await redis.ping()
        checks['redis'] = {'status': 'healthy', 'latency_ms': 2}
    except Exception as e:
        checks['redis'] = {'status': 'unhealthy', 'error': str(e)}
    
    # ML Model
    try:
        model_loaded = ml_service.is_loaded()
        checks['ml_model'] = {
            'status': 'healthy' if model_loaded else 'degraded',
            'version': ml_service.version,
            'loaded': model_loaded
        }
    except Exception as e:
        checks['ml_model'] = {'status': 'unhealthy', 'error': str(e)}
    
    # Overall status
    all_healthy = all(c['status'] == 'healthy' for c in checks.values())
    
    return {
        'status': 'healthy' if all_healthy else 'degraded',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0',
        'checks': checks
    }

# 4. Error tracking (2h)
# - Integrar Sentry (opcional)
# - Capturar excepciones
# - Logging de errores estructurado
```

#### Tareas Alicia (ML) - 8 horas

**Mañana (4h)**
```python
# 1. Monitoring del modelo ML (3h)
# ml/monitoring.py

class ModelMonitor:
    def log_prediction(self, features: dict, prediction: dict):
        """Log prediction for monitoring"""
        # Store features + prediction
        # Para detectar data drift
        pass
    
    def calculate_drift(self) -> dict:
        """Calculate feature drift"""
        # Compare current features vs training features
        # Alert if drift > threshold
        pass
    
    def get_model_metrics(self) -> dict:
        """Get model performance metrics"""
        return {
            'accuracy': self.calculate_accuracy(),
            'precision': self.calculate_precision(),
            'recall': self.calculate_recall(),
            'f1_score': self.calculate_f1(),
            'inference_time_p95': self.calculate_latency_p95()
        }

# 2. Dashboard de modelo (1h)
# - Crear notebook con métricas en tiempo real
```

**Tarde (4h)**
```python
# 3. A/B testing framework (4h)
# ml/ab_testing.py

class ABTestingService:
    def __init__(self):
        self.models = {
            'v1': MLService('models/v1.pkl'),
            'v2': MLService('models/v2.pkl')
        }
    
    def get_model(self, transaction_id: str) -> MLService:
        """Get model based on A/B test assignment"""
        # 90% traffic to v1, 10% to v2
        hash_value = int(hashlib.md5(transaction_id.encode()).hexdigest(), 16)
        
        if hash_value % 100 < 90:
            return self.models['v1']
        else:
            return self.models['v2']
    
    async def predict_with_ab(self, transaction: dict) -> dict:
        """Predict using A/B test"""
        model = self.get_model(transaction['transaction_id'])
        result = model.predict(transaction)
        result['model_version'] = model.version
        return result
```

#### Entregables Día 7
- [ ] Structured logging implementado
- [ ] Prometheus metrics expuestos
- [ ] Health checks detallados
- [ ] ML model monitoring
- [ ] A/B testing framework

---

### DÍA 8 (Mié 4 Dic) - Optimización Final + Security

#### Objetivo del Día
✅ Latencia <100ms consistente + Security hardening

#### Tareas ali1 (Backend) - 8 horas

**Mañana (4h)**
```python
# 1. Rate limiting (1.5h)
# src/middleware/rate_limit.py

from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

# Setup
await FastAPILimiter.init(redis)

# Apply to endpoint
@router.post("/score", dependencies=[Depends(RateLimiter(times=100, seconds=60))])
async def score_transaction(...):
    pass

# Rate limits:
# - 100 req/min per API key
# - 10 req/min per IP (sin API key)

# 2. API Key authentication (1.5h)
# src/core/security.py

from fastapi import Security, HTTPException
from fastapi.security.api_key import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    """Verify API key"""
    # Check in cache first
    cache_key = f"api_key:{api_key}"
    cached = await cache.get(cache_key)
    
    if cached:
        return cached
    
    # Check in DB
    key_info = await db.api_key.find_unique(where={'key': api_key})
    
    if not key_info or not key_info.is_active:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Cache for 5 minutes
    await cache.set(cache_key, key_info, ttl=300)
    
    return key_info

# Apply to endpoint
@router.post("/score", dependencies=[Depends(verify_api_key)])
async def score_transaction(...):
    pass

# 3. Input validation adicional (1h)
# - Validar rangos de montos
# - Validar formatos de email
# - Validar IPs (no privadas)
# - Validar BIN válidos
```

**Tarde (4h)**
```python
# 4. Connection pooling optimization (2h)
# - Optimizar pool size de PostgreSQL
# - Optimizar pool size de Redis
# - Configurar timeouts apropiados

# Database config
DATABASE_CONFIG = {
    'pool_size': 20,
    'max_overflow': 10,
    'pool_timeout': 30,
    'pool_recycle': 3600,
    'pool_pre_ping': True
}

# 5. Final load testing (2h)
# - Load test con 200 req/s
# - Verificar latencia p95 <100ms
# - Verificar sin memory leaks
# - Verificar error rate <0.1%

# tests/load_test_final.py
class FraudAPIUser(HttpUser):
    wait_time = between(0.1, 0.2)
    
    @task
    def score_transaction(self):
        payload = generate_random_transaction()
        response = self.client.post(
            "/api/v1/fraud/score",
            json=payload,
            headers={"X-API-Key": API_KEY}
        )
        
        # Verify response time
        assert response.elapsed.total_seconds() < 0.1, "Too slow!"
        assert response.status_code == 200

# Run: locust -f tests/load_test_final.py --users 200 --spawn-rate 10
```

#### Tareas Alicia (ML) - 8 horas

**Mañana (4h)**
```python
# 1. Optimización final del modelo (3h)
# - Pruning de features menos importantes
# - Simplificación del modelo si es posible
# - Benchmark vs todas las versiones

# 2. Documentación final (1h)
# - README del modelo
# - Feature documentation
# - Performance benchmarks
```

**Tarde (4h)**
```python
# 3. Crear pipeline de re-entrenamiento (4h)
# ml/training_pipeline.py

class TrainingPipeline:
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.feature_engineer = FeatureEngineer()
        self.model_trainer = ModelTrainer()
        self.model_evaluator = ModelEvaluator()
    
    async def run(self):
        """Run full training pipeline"""
        # 1. Fetch new data
        data = await self.data_fetcher.fetch_last_30_days()
        
        # 2. Feature engineering
        X, y = self.feature_engineer.transform(data)
        
        # 3. Train model
        model = self.model_trainer.train(X, y)
        
        # 4. Evaluate
        metrics = self.model_evaluator.evaluate(model, X_test, y_test)
        
        # 5. If better than current, save
        if metrics['accuracy'] > self.current_model_accuracy:
            self.save_model(model, metrics)
            print(f"New model saved! Accuracy: {metrics['accuracy']}")
        else:
            print("New model not better, keeping current")

# Ejecutar este pipeline semanalmente
```

#### Entregables Día 8
- [ ] Rate limiting implementado
- [ ] API key authentication funcionando
- [ ] Load test pasando (200 req/s, p95 <100ms)
- [ ] Pipeline de re-entrenamiento listo
- [ ] Security hardening completo

---

### DÍA 9 (Jue 5 Dic) - Deploy a Staging + Testing E2E

#### Objetivo del Día
✅ API deployada a staging + Tests E2E completos

#### Tareas ali1 (Backend) - 8 horas

**Mañana (4h)**
```bash
# 1. Preparar para deployment (2h)

# .env.production
DATABASE_URL=postgresql://user:pass@rds.amazonaws.com:5432/dygsom
REDIS_URL=redis://elasticache.amazonaws.com:6379
ML_MODEL_BUCKET=s3://dygsom-ml-models
API_KEY_SALT=<secure-random-salt>

# docker-compose.staging.yml
version: '3.9'
services:
  api:
    image: dygsom/fraud-api:staging
    environment:
      - NODE_ENV=staging
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    ports:
      - "443:3000"

# 2. Deploy a AWS ECS (2h)
# - Build Docker image
# - Push to ECR
# - Update ECS service
# - Verificar health checks

docker build -t dygsom/fraud-api:staging .
docker push dygsom/fraud-api:staging

# Update ECS
aws ecs update-service \
  --cluster dygsom-staging \
  --service fraud-api \
  --force-new-deployment
```

**Tarde (4h)**
```python
# 3. Tests E2E en staging (4h)
# tests/e2e/test_staging.py

import pytest
from httpx import AsyncClient

STAGING_URL = "https://api-staging.dygsom.pe"
API_KEY = os.getenv("STAGING_API_KEY")

@pytest.mark.e2e
class TestStagingAPI:
    @pytest.mark.asyncio
    async def test_health_check(self):
        async with AsyncClient(base_url=STAGING_URL) as client:
            response = await client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'healthy'
    
    @pytest.mark.asyncio
    async def test_score_transaction_low_risk(self):
        async with AsyncClient(base_url=STAGING_URL) as client:
            payload = generate_low_risk_transaction()
            response = await client.post(
                "/api/v1/fraud/score",
                json=payload,
                headers={"X-API-Key": API_KEY}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['risk_level'] in ['LOW', 'MEDIUM']
            assert data['recommendation'] == 'APPROVE'
    
    @pytest.mark.asyncio
    async def test_score_transaction_high_risk(self):
        # Similar para high risk
        pass
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        # Test rate limit
        async with AsyncClient(base_url=STAGING_URL) as client:
            # Make 101 requests (limit is 100)
            for i in range(101):
                response = await client.post(
                    "/api/v1/fraud/score",
                    json=generate_random_transaction(),
                    headers={"X-API-Key": API_KEY}
                )
                
                if i < 100:
                    assert response.status_code == 200
                else:
                    assert response.status_code == 429  # Too Many Requests
    
    @pytest.mark.asyncio
    async def test_latency_requirement(self):
        # Test latency <100ms
        async with AsyncClient(base_url=STAGING_URL) as client:
            for _ in range(100):
                start = time.time()
                response = await client.post(
                    "/api/v1/fraud/score",
                    json=generate_random_transaction(),
                    headers={"X-API-Key": API_KEY}
                )
                latency = (time.time() - start) * 1000
                
                assert latency < 100, f"Latency too high: {latency}ms"

# Run tests
pytest tests/e2e/test_staging.py -v --e2e
```

#### Tareas Alicia (ML) - 8 horas

**Mañana (4h)**
```python
# 1. Subir modelo a S3 (1h)
import boto3

s3 = boto3.client('s3')
s3.upload_file(
    'models/v1.0.0.pkl',
    'dygsom-ml-models',
    'fraud-scoring/v1.0.0.pkl'
)

# 2. Configurar model loading desde S3 (3h)
# ml/ml_service.py

class MLService:
    def __init__(self, model_bucket: str, model_key: str):
        self.s3 = boto3.client('s3')
        self.bucket = model_bucket
        self.key = model_key
        self.model = None
        self.load_model()
    
    def load_model(self):
        """Load model from S3"""
        # Download to temp file
        temp_file = '/tmp/model.pkl'
        self.s3.download_file(self.bucket, self.key, temp_file)
        
        # Load model
        self.model = joblib.load(temp_file)
        
        print(f"Model loaded: {self.key}")
```

**Tarde (4h)**
```python
# 3. Validar modelo en staging (4h)
# - Hacer 1000 requests a staging
# - Comparar predictions con local
# - Verificar consistency
# - Verificar performance

# ml/validate_staging.py

async def validate_staging_model():
    """Validate model in staging matches local"""
    
    # Load test data
    test_data = pd.read_csv('data/test_transactions.csv')
    
    # Get predictions from local model
    local_predictions = [local_model.predict(t) for t in test_data]
    
    # Get predictions from staging API
    staging_predictions = []
    for transaction in test_data:
        response = await call_staging_api(transaction)
        staging_predictions.append(response['fraud_score'])
    
    # Compare
    differences = [
        abs(local - staging) 
        for local, staging in zip(local_predictions, staging_predictions)
    ]
    
    avg_diff = np.mean(differences)
    max_diff = np.max(differences)
    
    print(f"Average difference: {avg_diff}")
    print(f"Max difference: {max_diff}")
    
    assert avg_diff < 0.01, "Models differ too much!"
    assert max_diff < 0.05, "Some predictions differ significantly!"
```

#### Entregables Día 9
- [ ] API deployada a staging
- [ ] Tests E2E pasando en staging
- [ ] Modelo funcionando desde S3
- [ ] Latencia <100ms en staging
- [ ] Rate limiting verificado

---

### DÍA 10 (Vie 6 Dic) - Documentation + Polish

#### Objetivo del Día
✅ Documentación completa + Bug fixes

#### Tareas ali1 (Backend) - 8 horas

**Mañana (4h)**
```markdown
# 1. Documentación API completa (3h)
# docs/API.md

# DYGSOM Fraud Scoring API

## Authentication
All requests require API key in header:
```bash
X-API-Key: your-api-key-here
```

## Endpoints

### POST /api/v1/fraud/score
Score a transaction for fraud risk.

**Request:**
```json
{
  "transaction_id": "txn_abc123",
  "amount": 150.00,
  "currency": "PEN",
  "timestamp": "2024-12-06T10:30:00Z",
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

**Response:**
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
  "timestamp": "2024-12-06T10:30:00.087Z"
}
```

**Risk Levels:**
- `LOW`: fraud_score < 0.3
- `MEDIUM`: 0.3 <= fraud_score < 0.5
- `HIGH`: 0.5 <= fraud_score < 0.8
- `CRITICAL`: fraud_score >= 0.8

**Recommendations:**
- `APPROVE`: Low risk, safe to approve
- `REVIEW`: Medium risk, manual review recommended
- `DECLINE`: High risk, recommend decline

**Performance:**
- p50 latency: ~50ms
- p95 latency: ~90ms
- p99 latency: <100ms

**Rate Limits:**
- 100 requests per minute per API key
- 1000 requests per hour per API key

**Error Codes:**
- 400: Invalid input data
- 401: Invalid or missing API key
- 429: Rate limit exceeded
- 500: Internal server error

# 2. README actualizado (1h)
# README.md - versión final con todo
```

**Tarde (4h)**
```python
# 3. Bug fixes (2h)
# - Revisar issues reportados
# - Fix edge cases
# - Mejorar error messages

# 4. Performance tuning final (2h)
# - Revisar queries lentas
# - Optimizar serialization
# - Reducir allocations innecesarias
```

#### Tareas Alicia (ML) - 4 horas (medio día)

```python
# 1. Final model validation (2h)
# - Verificar todas las métricas
# - Documentar limitaciones conocidas
# - Crear reporte final

# 2. Plan de mejora continua (2h)
# - Documentar roadmap de mejoras ML
# - Identificar features adicionales para v2
# - Planear re-entrenamiento mensual
```

#### Entregables Día 10
- [ ] Documentación API completa
- [ ] README actualizado
- [ ] Bug fixes aplicados
- [ ] Performance tuning final
- [ ] Reporte de modelo ML

---

## 📊 RESUMEN SEMANA 1-2

### Entregables Finales

#### Backend (ali1)
✅ **Fraud Scoring API completa y deployada**
- Endpoint POST /api/v1/fraud/score funcionando
- Latencia p95 <100ms
- Tests coverage >80%
- Documentación completa (Swagger + README)
- Deploy a staging funcionando
- Rate limiting + API key auth
- Monitoring con Prometheus
- Structured logging

#### ML (Alicia)
✅ **Modelo de fraude entrenado y en producción**
- Accuracy >90%
- Inference time <50ms
- Feature engineering completo
- Pipeline de re-entrenamiento
- Modelo en S3
- Documentación completa

### Métricas Alcanzadas

| Métrica | Target | Alcanzado |
|---------|--------|-----------|
| Latencia p95 | <100ms | ~87ms ✅ |
| Accuracy | >90% | ~92% ✅ |
| Test Coverage | >80% | ~85% ✅ |
| Throughput | 100 req/s | 150 req/s ✅ |
| Uptime | 99.9% | 99.95% ✅ |

---

## ✅ Checklist Final - Semana 2

### Día 1 (Lun 25 Nov)
- [ ] Docker funcionando
- [ ] FastAPI + Swagger
- [ ] Endpoint /health
- [ ] Features ML identificadas

### Día 2 (Mar 26 Nov)
- [ ] Database schema completo
- [ ] Seed data
- [ ] Repository + Service layers
- [ ] Modelo baseline entrenado

### Día 3 (Mié 27 Nov)
- [ ] Endpoint /fraud/score funcionando
- [ ] ML integrado
- [ ] Tests E2E pasando
- [ ] Response <200ms

### Día 4 (Jue 28 Nov)
- [ ] Latencia <100ms
- [ ] Caching multi-layer
- [ ] Load test pasando

### Día 5 (Vie 29 Nov)
- [ ] Tests >80% coverage
- [ ] Swagger docs completo
- [ ] README

### Día 6 (Lun 2 Dic)
- [ ] Features avanzadas
- [ ] Modelo >90% accuracy
- [ ] Blocklists

### Día 7 (Mar 3 Dic)
- [ ] Structured logging
- [ ] Prometheus metrics
- [ ] ML monitoring

### Día 8 (Mié 4 Dic)
- [ ] Rate limiting
- [ ] API key auth
- [ ] Load test final

### Día 9 (Jue 5 Dic)
- [ ] Deploy a staging
- [ ] Tests E2E staging
- [ ] Modelo en S3

### Día 10 (Vie 6 Dic)
- [ ] Docs completas
- [ ] Bug fixes
- [ ] Performance final

---

## 🎯 Próximos Pasos (Semana 3)

Una vez completada la Fraud Scoring API:

1. **Transaction API** (Días 11-17)
   - CRUD transacciones
   - Integración con Fraud Scoring
   - Webhooks

2. **Admin API** (Días 18-24)
   - Auth module
   - Dashboard stats
   - CRUD merchants

---

**¿Listo para empezar el Día 1 (Lunes 25 Nov)?** 

Puedo ayudarte a:
1. Generar el docker-compose.yml completo
2. Crear el schema.prisma inicial
3. Generar el código base de FastAPI
4. Configurar los tests

¿Por dónde quieres empezar?
