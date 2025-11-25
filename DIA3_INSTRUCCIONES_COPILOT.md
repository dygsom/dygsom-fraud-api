# 📋 DÍA 3: Endpoint POST /fraud/score - Instrucciones para Copilot

> **IMPORTANTE**: Estas instrucciones están 100% sincronizadas con el código existente del Día 1-2.

---

## ✅ Estado Actual del Proyecto (Ya Implementado)

### Archivos que YA EXISTEN y NO deben modificarse:

1. **src/main.py** - FastAPI app básica con health check
2. **src/services/fraud_service.py** - ✅ COMPLETO con toda la lógica de negocio
3. **src/repositories/transaction_repository.py** - ✅ COMPLETO con queries
4. **src/repositories/base_repository.py** - ✅ COMPLETO con CRUD
5. **src/schemas/transaction_schemas.py** - ✅ COMPLETO con DTOs y validators
6. **prisma/schema.prisma** - ✅ COMPLETO con 4 tablas

### Lo que el Día 1-2 ya implementó:

✅ **FraudService está COMPLETO** con:
- `score_transaction()` - Lógica completa de scoring
- `_extract_velocity_features()` - Extracción de features
- `_calculate_fraud_score()` - Scoring con reglas (placeholder para ML)
- `_calculate_risk_level()` - Clasificación LOW/MEDIUM/HIGH/CRITICAL
- `_generate_recommendation()` - APPROVE/REVIEW/DECLINE
- `_save_transaction()` - Guardado en DB
- Velocity checks completos
- Logging estructurado completo

✅ **TransactionRepository está COMPLETO** con queries específicas para fraud detection

✅ **DTOs están COMPLETOS** con validadores custom muy robustos

---

## 🎯 Lo que FALTA Implementar en Día 3

### Archivos NUEVOS a crear (en orden):

1. **src/ml/__init__.py** - Package marker
2. **src/ml/ml_service.py** - Servicio ML básico
3. **src/dependencies.py** - Dependency injection
4. **src/api/v1/endpoints/fraud.py** - Endpoint POST /score
5. **Actualizar src/api/v1/router.py** - Incluir endpoint
6. **Actualizar src/main.py** - Incluir router

---

## 🎨 ESTILO DE CÓDIGO (Debe ser IDÉNTICO al existente)

### 1. Imports (siempre en este orden):

```python
"""
Docstring del módulo
Explicación de qué hace el archivo
"""

# Standard library
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

# Third-party
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

# Local
from src.services.fraud_service import FraudService
from src.schemas.transaction_schemas import CreateTransactionDto

logger = logging.getLogger(__name__)
```

### 2. Constantes (siempre al inicio después de imports):

```python
# SIEMPRE usar UPPER_SNAKE_CASE para constantes
MAX_FRAUD_SCORE = 1.0
MIN_FRAUD_SCORE = 0.0
DEFAULT_MODEL_VERSION = "v1.0.0-baseline"
```

### 3. Funciones (siempre con docstrings estilo Google):

```python
async def nombre_funcion(parametro: str, otro: int = 0) -> Dict[str, Any]:
    """Descripción breve en una línea
    
    Descripción más detallada si es necesario. Explica qué hace
    la función y cualquier detalle relevante.
    
    Args:
        parametro: Descripción del parámetro
        otro: Descripción con valor default
        
    Returns:
        Dict con la estructura de respuesta
        
    Raises:
        Exception: Cuándo y por qué se lanza
    """
    try:
        # Implementation
        pass
    except Exception as e:
        logger.error("Mensaje de error", extra={"key": "value"})
        raise
```

### 4. Logging (siempre estructurado con extra):

```python
# ✅ CORRECTO (como está en fraud_service.py)
logger.info(
    "Mensaje descriptivo",
    extra={
        "transaction_id": transaction_id,
        "fraud_score": fraud_score,
        "processing_time_ms": processing_time_ms
    }
)

# ❌ INCORRECTO (no usar)
print(f"Transaction scored: {transaction_id}")
logger.info(f"Transaction scored: {transaction_id}")  # Sin extra dict
```

### 5. Exception Handling (siempre capturar y loggear):

```python
try:
    result = await some_operation()
    return result
except Exception as e:
    logger.error(
        "Descripción del error",
        extra={
            "transaction_id": transaction_id,
            "error": str(e),
            "error_type": type(e).__name__
        },
        exc_info=True
    )
    raise
```

---

## 📁 Estructura Final Esperada

```
src/
├── ml/                          ← CREAR ESTA CARPETA
│   ├── __init__.py             ← CREAR (vacío)
│   └── ml_service.py           ← CREAR
├── api/
│   └── v1/
│       ├── endpoints/
│       │   └── fraud.py        ← CREAR
│       └── router.py           ← ACTUALIZAR
├── dependencies.py             ← CREAR
└── main.py                     ← ACTUALIZAR
```

---

## 🔨 PASO 1: Crear src/ml/ml_service.py

### Archivo: `src/ml/ml_service.py`

```python
"""
Machine Learning Service for fraud prediction.

Day 3 implementation uses rule-based scoring (placeholder).
Day 6 will integrate actual XGBoost model trained by Alicia.
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# Model configuration constants
MODEL_VERSION_BASELINE = "v1.0.0-baseline"


class MLService:
    """Machine Learning service for fraud prediction
    
    Currently implements rule-based scoring as placeholder until
    actual ML model is trained and integrated.
    
    Attributes:
        model_version: Version identifier for the model
    """
    
    def __init__(self):
        """Initialize MLService with baseline configuration
        
        In Day 6, this will load actual trained model from S3 or local storage.
        """
        self.model_version = MODEL_VERSION_BASELINE
        logger.info(f"MLService initialized with version: {self.model_version}")
    
    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Predict fraud probability for transaction
        
        Day 3 Implementation: Uses simple rule-based scoring.
        Day 6 Implementation: Will use trained XGBoost model.
        
        Args:
            features: Dict containing transaction features for prediction
                Required keys:
                - amount: float - Transaction amount
                - customer_tx_count_1h: int - Transactions in last hour
                - customer_tx_count_24h: int - Transactions in last 24h
                - customer_amount_24h: float - Total amount in last 24h
                - ip_tx_count_1h: int - IP transactions in last hour
                
        Returns:
            Dict with prediction results:
                - fraud_score: float (0-1) - Probability of fraud
                - risk_level: str - Risk classification
                - recommendation: str - Business recommendation
                - model_version: str - Model version used
                
        Raises:
            ValueError: If required features are missing
            Exception: If prediction fails
        """
        try:
            logger.debug(
                "Starting ML prediction",
                extra={"features_count": len(features)}
            )
            
            # Validate required features
            required_features = [
                "amount",
                "customer_tx_count_1h", 
                "customer_tx_count_24h",
                "customer_amount_24h",
                "ip_tx_count_1h"
            ]
            
            missing_features = [f for f in required_features if f not in features]
            if missing_features:
                raise ValueError(f"Missing required features: {missing_features}")
            
            # Calculate fraud score using rule-based approach (Day 3)
            fraud_score = self._calculate_rule_based_score(features)
            
            # Determine risk level and recommendation
            risk_level = self._get_risk_level(fraud_score)
            recommendation = self._get_recommendation(risk_level)
            
            logger.debug(
                "ML prediction completed",
                extra={
                    "fraud_score": fraud_score,
                    "risk_level": risk_level,
                    "recommendation": recommendation
                }
            )
            
            return {
                "fraud_score": fraud_score,
                "risk_level": risk_level,
                "recommendation": recommendation,
                "model_version": self.model_version
            }
            
        except ValueError as e:
            logger.error(f"Validation error in ML prediction: {str(e)}")
            raise
        except Exception as e:
            logger.error(
                "Error during ML prediction",
                extra={"error": str(e), "error_type": type(e).__name__},
                exc_info=True
            )
            raise
    
    def _calculate_rule_based_score(self, features: Dict[str, Any]) -> float:
        """Calculate fraud score using rule-based approach
        
        This is a placeholder implementation for Day 3.
        Day 6 will replace this with actual ML model prediction.
        
        Rules:
        - High velocity transactions increase score
        - Large amounts increase score
        - Multiple transactions from same IP increase score
        
        Args:
            features: Transaction features dict
            
        Returns:
            Fraud score between 0.0 and 1.0
        """
        score = 0.0
        
        # Rule 1: High transaction count in last hour (max 20 points)
        customer_tx_1h = features.get("customer_tx_count_1h", 0)
        if customer_tx_1h > 5:
            score += 0.20
        elif customer_tx_1h > 3:
            score += 0.10
        
        # Rule 2: High transaction count in last 24h (max 20 points)
        customer_tx_24h = features.get("customer_tx_count_24h", 0)
        if customer_tx_24h > 20:
            score += 0.20
        elif customer_tx_24h > 10:
            score += 0.10
        
        # Rule 3: High amount in last 24h (max 20 points)
        customer_amount_24h = features.get("customer_amount_24h", 0)
        if customer_amount_24h > 10000:
            score += 0.20
        elif customer_amount_24h > 5000:
            score += 0.10
        
        # Rule 4: High IP transaction count (max 20 points)
        ip_tx_1h = features.get("ip_tx_count_1h", 0)
        if ip_tx_1h > 10:
            score += 0.20
        elif ip_tx_1h > 5:
            score += 0.10
        
        # Rule 5: Large transaction amount (max 20 points)
        amount = features.get("amount", 0)
        if amount > 5000:
            score += 0.20
        elif amount > 2000:
            score += 0.10
        
        # Cap at 1.0
        score = min(score, 1.0)
        
        # Round to 4 decimal places
        return round(score, 4)
    
    def _get_risk_level(self, fraud_score: float) -> str:
        """Determine risk level from fraud score
        
        Business rules:
        - LOW: score < 0.3
        - MEDIUM: 0.3 <= score < 0.5
        - HIGH: 0.5 <= score < 0.8
        - CRITICAL: score >= 0.8
        
        Args:
            fraud_score: Fraud probability score (0-1)
            
        Returns:
            Risk level string
        """
        if fraud_score < 0.3:
            return "LOW"
        elif fraud_score < 0.5:
            return "MEDIUM"
        elif fraud_score < 0.8:
            return "HIGH"
        else:
            return "CRITICAL"
    
    def _get_recommendation(self, risk_level: str) -> str:
        """Get business recommendation based on risk level
        
        Business rules:
        - LOW → APPROVE
        - MEDIUM → REVIEW
        - HIGH → DECLINE
        - CRITICAL → DECLINE
        
        Args:
            risk_level: Risk level string
            
        Returns:
            Recommendation string
        """
        if risk_level == "LOW":
            return "APPROVE"
        elif risk_level == "MEDIUM":
            return "REVIEW"
        else:  # HIGH or CRITICAL
            return "DECLINE"
```

---

## 🔨 PASO 2: Crear src/ml/__init__.py

### Archivo: `src/ml/__init__.py`

```python
"""ML module for DYGSOM Fraud API"""

from src.ml.ml_service import MLService

__all__ = ["MLService"]
```

---

## 🔨 PASO 3: Crear src/dependencies.py

### Archivo: `src/dependencies.py`

```python
"""
Dependency injection for FastAPI.
Provides instances of services and repositories with proper initialization.
"""

from prisma import Prisma
from src.services.fraud_service import FraudService
from src.repositories.transaction_repository import TransactionRepository
from src.ml.ml_service import MLService
import logging

logger = logging.getLogger(__name__)

# Global Prisma client instance
# In production, this should be managed with proper lifecycle
_prisma_client = None


async def get_prisma() -> Prisma:
    """Get Prisma client instance
    
    Creates and connects Prisma client if not already connected.
    
    Returns:
        Connected Prisma client instance
        
    Raises:
        Exception: If Prisma connection fails
    """
    global _prisma_client
    
    if _prisma_client is None:
        logger.info("Initializing Prisma client")
        _prisma_client = Prisma()
        await _prisma_client.connect()
        logger.info("Prisma client connected successfully")
    
    return _prisma_client


async def get_fraud_service() -> FraudService:
    """Get FraudService instance with dependencies
    
    Dependency injection for FraudService.
    Creates all required dependencies (Prisma, Repository, MLService).
    
    Returns:
        FraudService instance ready to use
        
    Raises:
        Exception: If service initialization fails
    """
    try:
        logger.debug("Initializing FraudService dependencies")
        
        # Get Prisma client
        prisma = await get_prisma()
        
        # Create repository
        transaction_repo = TransactionRepository(prisma)
        
        # Create ML service (Day 3: rule-based, Day 6: actual model)
        # ml_service = MLService()
        # For now, FraudService doesn't use MLService yet
        # It will be integrated when we refactor fraud_service.py
        
        # Create and return fraud service
        fraud_service = FraudService(transaction_repo=transaction_repo)
        
        logger.debug("FraudService initialized successfully")
        return fraud_service
        
    except Exception as e:
        logger.error(
            "Error initializing FraudService",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True
        )
        raise
```

---

## 🔨 PASO 4: Crear src/api/v1/endpoints/fraud.py

### Archivo: `src/api/v1/endpoints/fraud.py`

```python
"""
Fraud detection endpoint.
Implements POST /score for transaction fraud scoring.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
import time
from datetime import datetime
import logging

from src.schemas.transaction_schemas import CreateTransactionDto
from src.services.fraud_service import FraudService
from src.dependencies import get_fraud_service

logger = logging.getLogger(__name__)

# Create router with prefix and tags
router = APIRouter(prefix="/fraud", tags=["Fraud Detection"])


@router.post(
    "/score",
    status_code=status.HTTP_200_OK,
    summary="Score transaction for fraud",
    description="""
    Score a transaction for fraud risk using machine learning and velocity checks.
    
    **Returns:**
    - fraud_score (0-1): Probability of fraud
    - risk_level: LOW, MEDIUM, HIGH, or CRITICAL
    - recommendation: APPROVE, REVIEW, or DECLINE
    - processing_time_ms: API processing time
    
    **Performance:**
    - Target latency: <100ms (p95)
    - Current Day 3: <200ms (will optimize in Day 4)
    
    **Risk Levels:**
    - LOW: fraud_score < 0.3 → Safe to approve
    - MEDIUM: 0.3 <= fraud_score < 0.5 → Review recommended
    - HIGH: 0.5 <= fraud_score < 0.8 → High risk
    - CRITICAL: fraud_score >= 0.8 → Very high risk
    
    **Business Rules:**
    - Velocity checks on customer email and IP
    - Transaction amount analysis
    - Pattern detection based on historical data
    """,
    responses={
        200: {
            "description": "Transaction scored successfully",
            "content": {
                "application/json": {
                    "example": {
                        "transaction_id": "txn_abc123xyz789",
                        "fraud_score": 0.23,
                        "risk_level": "LOW",
                        "recommendation": "APPROVE",
                        "processing_time_ms": 87,
                        "timestamp": "2024-11-27T10:30:00.087Z",
                        "details": {
                            "amount": 150.50,
                            "currency": "PEN",
                            "customer_email": "juan.perez@gmail.com",
                            "velocity_checks": {
                                "customer_tx_count_1h": 1,
                                "customer_tx_count_24h": 3,
                                "customer_amount_24h": 450.00,
                                "ip_tx_count_1h": 1,
                                "ip_tx_count_24h": 5
                            }
                        }
                    }
                }
            }
        },
        400: {
            "description": "Invalid request data",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Validation error: Invalid email format"
                    }
                }
            }
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Internal server error while scoring transaction"
                    }
                }
            }
        }
    }
)
async def score_transaction(
    transaction_data: CreateTransactionDto,
    fraud_service: Annotated[FraudService, Depends(get_fraud_service)]
):
    """Score transaction for fraud risk
    
    Validates transaction data, calculates fraud score using ML and velocity checks,
    determines risk level and recommendation, then saves to database.
    
    Args:
        transaction_data: Validated transaction data from request body
        fraud_service: Injected FraudService instance
        
    Returns:
        Dict with fraud scoring results and processing metrics
        
    Raises:
        HTTPException 400: If validation fails
        HTTPException 500: If internal processing fails
    """
    start_time = time.time()
    
    try:
        logger.info(
            "Incoming fraud score request",
            extra={
                "transaction_id": transaction_data.transaction_id,
                "amount": transaction_data.amount,
                "currency": transaction_data.currency,
                "customer_email": transaction_data.customer.email,
                "customer_ip": transaction_data.customer.ip_address
            }
        )
        
        # Score transaction using FraudService
        # This calls the complete fraud detection pipeline:
        # 1. Extract velocity features from DB
        # 2. Calculate fraud score (rule-based for Day 3)
        # 3. Determine risk level
        # 4. Generate recommendation
        # 5. Save to database
        result = await fraud_service.score_transaction(transaction_data)
        
        # Calculate total processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Update result with actual processing time
        result["processing_time_ms"] = processing_time_ms
        
        logger.info(
            "Transaction scored successfully",
            extra={
                "transaction_id": transaction_data.transaction_id,
                "fraud_score": result["fraud_score"],
                "risk_level": result["risk_level"],
                "recommendation": result["recommendation"],
                "processing_time_ms": processing_time_ms
            }
        )
        
        return result
        
    except ValueError as e:
        # Validation errors (should be caught by Pydantic, but just in case)
        logger.error(
            "Validation error in fraud scoring",
            extra={
                "transaction_id": transaction_data.transaction_id,
                "error": str(e),
                "error_type": "ValidationError"
            }
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}"
        )
        
    except Exception as e:
        # Unexpected errors
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        logger.error(
            "Error scoring transaction",
            extra={
                "transaction_id": transaction_data.transaction_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "processing_time_ms": processing_time_ms
            },
            exc_info=True
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while scoring transaction"
        )
```

---

## 🔨 PASO 5: Actualizar src/api/v1/router.py

### Archivo: `src/api/v1/router.py` (ACTUALIZAR)

```python
"""
API Router V1
Main router for API version 1
"""

from fastapi import APIRouter

# Create main router
api_router = APIRouter()

# Import endpoint routers
from src.api.v1.endpoints import fraud

# Include sub-routers
api_router.include_router(fraud.router, prefix="/fraud", tags=["Fraud Detection"])


# Keep existing health endpoint if you have one
# Or add it here if needed
```

---

## 🔨 PASO 6: Actualizar src/main.py

### Archivo: `src/main.py` (ACTUALIZAR - agregar estas líneas)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

# ADD THIS IMPORT
from src.api.v1.router import api_router

app = FastAPI(
    title="DYGSOM Fraud API", description="Fraud detection API", version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
    }


@app.get("/")
async def root():
    return {"message": "Welcome to DYGSOM Fraud API", "docs": "/docs"}


# ADD THIS LINE - Include API router
app.include_router(api_router, prefix="/api/v1")
```

---

## ✅ Checklist de Verificación Día 3

Después de implementar, verifica:

### Código Creado
- [ ] `src/ml/__init__.py` existe y es correcto
- [ ] `src/ml/ml_service.py` implementado completamente
- [ ] `src/dependencies.py` implementado completamente
- [ ] `src/api/v1/endpoints/fraud.py` implementado completamente
- [ ] `src/api/v1/router.py` actualizado con import de fraud
- [ ] `src/main.py` actualizado con include_router

### Estilo de Código
- [ ] Todos los archivos tienen docstrings completos
- [ ] Type hints en todas las funciones
- [ ] Logging estructurado con `logger + extra dict`
- [ ] Constantes en UPPER_SNAKE_CASE
- [ ] Exception handling apropiado con try/except
- [ ] Async/await usado correctamente
- [ ] NO se usa `print()` ni `any` type

### Funcionalidad
- [ ] `docker compose restart api` ejecutado sin errores
- [ ] Swagger docs muestra endpoint `/api/v1/fraud/score`
- [ ] POST request funciona con ejemplo de Swagger
- [ ] Response incluye fraud_score, risk_level, recommendation
- [ ] Response incluye processing_time_ms
- [ ] Logs estructurados aparecen en `docker compose logs api`

### Performance
- [ ] Latencia <200ms (objetivo para Día 3)
- [ ] No hay errores 500 en requests válidos
- [ ] Validación Pydantic funciona (400 para datos inválidos)

---

## 🧪 Testing del Endpoint

### Usando Swagger UI

1. Abrir: http://localhost:3000/docs
2. Buscar: `POST /api/v1/fraud/score`
3. Click en "Try it out"
4. Usar este payload de ejemplo:

```json
{
  "transaction_id": "txn_test_dia3_001",
  "amount": 150.50,
  "currency": "PEN",
  "timestamp": "2024-11-27T10:30:00Z",
  "customer": {
    "id": "cust_123456",
    "email": "juan.perez@gmail.com",
    "phone": "+51987654321",
    "ip_address": "181.67.45.123",
    "device_fingerprint": "fp_abc123xyz"
  },
  "payment_method": {
    "type": "credit_card",
    "bin": "411111",
    "last4": "1111",
    "brand": "Visa"
  }
}
```

5. Click "Execute"
6. Verificar respuesta 200 OK

### Usando cURL

```bash
curl -X POST "http://localhost:3000/api/v1/fraud/score" \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "txn_test_curl_001",
    "amount": 150.50,
    "currency": "PEN",
    "timestamp": "2024-11-27T10:30:00Z",
    "customer": {
      "email": "test@example.com",
      "ip_address": "181.67.45.123"
    },
    "payment_method": {
      "type": "credit_card",
      "bin": "411111",
      "last4": "1111",
      "brand": "Visa"
    }
  }'
```

### Response Esperada

```json
{
  "transaction_id": "txn_test_dia3_001",
  "fraud_score": 0.1,
  "risk_level": "LOW",
  "recommendation": "APPROVE",
  "processing_time_ms": 87,
  "timestamp": "2024-11-27T10:30:00Z",
  "details": {
    "amount": 150.50,
    "currency": "PEN",
    "customer_email": "juan.perez@gmail.com",
    "velocity_checks": {
      "customer_tx_count_1h": 0,
      "customer_tx_count_24h": 0,
      "customer_amount_24h": 0.0,
      "ip_tx_count_1h": 0,
      "ip_tx_count_24h": 0
    }
  }
}
```

---

## 🔍 Ver Logs

```bash
# Ver logs en tiempo real
docker compose logs -f api

# Ver últimas 50 líneas
docker compose logs api --tail=50
```

Deberías ver logs estructurados como:

```
{"timestamp":"2024-11-27T10:30:00.000Z","level":"INFO","logger":"src.api.v1.endpoints.fraud","message":"Incoming fraud score request","transaction_id":"txn_test_dia3_001","amount":150.5,"currency":"PEN"}
{"timestamp":"2024-11-27T10:30:00.050Z","level":"INFO","logger":"src.services.fraud_service","message":"Starting fraud scoring","transaction_id":"txn_test_dia3_001"}
{"timestamp":"2024-11-27T10:30:00.087Z","level":"INFO","logger":"src.api.v1.endpoints.fraud","message":"Transaction scored successfully","transaction_id":"txn_test_dia3_001","fraud_score":0.1,"risk_level":"LOW","processing_time_ms":87}
```

---

## 🎯 Resultado Final Esperado

Al completar el Día 3, deberías tener:

✅ Endpoint `/api/v1/fraud/score` funcionando completamente
✅ Integración con FraudService existente
✅ Logging estructurado en todos los niveles
✅ Swagger docs completo con ejemplos
✅ Validación robusta con Pydantic
✅ Exception handling apropiado
✅ Latencia <200ms (optimizaremos a <100ms en Día 4)
✅ Código 100% consistente con estilo existente

---

## 📝 Notas Importantes

1. **NO modificar fraud_service.py** - Ya está completo y funcionando
2. **NO modificar transaction_repository.py** - Ya está completo
3. **NO modificar transaction_schemas.py** - Ya tiene todos los DTOs
4. **Carpeta ml/** debe estar en `src/ml/` (no fuera de src)
5. **MLService** por ahora es independiente, se integrará con FraudService en Día 6
6. **Seguir EXACTAMENTE el estilo** de código mostrado en los ejemplos

---

## 🚀 ¡Listo para Implementar!

Ahora Copilot tiene TODAS las instrucciones necesarias, 100% consistentes con tu código existente.

**Orden de implementación:**
1. Crear `src/ml/__init__.py` (vacío)
2. Crear `src/ml/ml_service.py` (código completo arriba)
3. Crear `src/dependencies.py` (código completo arriba)
4. Crear `src/api/v1/endpoints/fraud.py` (código completo arriba)
5. Actualizar `src/api/v1/router.py` (agregar import y include_router)
6. Actualizar `src/main.py` (agregar include_router)
7. Restart: `docker compose restart api`
8. Probar en Swagger: http://localhost:3000/docs

**¡Buena suerte con la implementación!** 🎉
