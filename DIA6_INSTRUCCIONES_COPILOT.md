# 📋 DÍA 6: ML Avanzado + Feature Engineering - Instrucciones para Copilot

> **Objetivo**: Reemplazar modelo rule-based con XGBoost real + Feature engineering avanzado

---

## ✅ Estado Actual (Días 1-5 Completados)

### Lo que YA existe:
- ✅ API funcionando con security completa
- ✅ Caching multi-layer optimizado
- ✅ MLService básico con reglas simples
- ✅ Config centralizado en `settings`
- ✅ Healthchecks avanzados
- ✅ Connection manager con lifecycle

### Problema actual:
**ML Service usa reglas hardcodeadas:**
```python
# En ml_service.py - reglas simples
if customer_tx_1h > 5:
    score += 0.20
```

**Objetivo Día 6:**
- 🎯 Modelo XGBoost real entrenado
- 🎯 70+ features avanzados
- 🎯 Accuracy objetivo: >85%
- 🎯 Latencia objetivo: <50ms para predicción

---

## 🎯 Lo que Implementaremos Hoy

### PARTE A: Feature Engineering Avanzado (Prioridad 1)

1. **Velocity Features** (ya existen, mejorar)
2. **Time Features** - hora del día, día semana, es_fin_semana
3. **Amount Features** - normalización, ratios, desviaciones
4. **Email Features** - dominio, es_temporal, longitud
5. **Device Features** - fingerprint, es_nuevo
6. **Geographic Features** - país IP, distancia transacciones
7. **Behavioral Features** - patrones de gasto, velocidad

### PARTE B: ML Model Real (Prioridad 1)

8. **Training Pipeline** - Script para entrenar XGBoost
9. **Model Storage** - Guardar/cargar modelo en disco
10. **MLService Actualizado** - Integrar XGBoost real
11. **Feature Store** - Cache de features calculados

### PARTE C: Testing & Validation (Prioridad 2)

12. **Model Evaluation** - Métricas (precision, recall, F1)
13. **Tests de ML** - Validar predicciones
14. **Monitoring de Modelo** - Track de performance

---

## 📁 Estructura de Archivos

### Archivos NUEVOS a crear:

```
src/
├── ml/
│   ├── features/
│   │   ├── __init__.py              ← NUEVO
│   │   ├── base_feature.py          ← NUEVO - Feature extractor base
│   │   ├── velocity_features.py     ← NUEVO - Velocity features
│   │   ├── time_features.py         ← NUEVO - Time-based features
│   │   ├── amount_features.py       ← NUEVO - Amount features
│   │   ├── email_features.py        ← NUEVO - Email features
│   │   ├── device_features.py       ← NUEVO - Device features
│   │   └── feature_engineering.py   ← NUEVO - Orquestador de features
│   ├── model_manager.py             ← NUEVO - Load/save models
│   └── ml_service.py                ← ACTUALIZAR - Integrar XGBoost

ml/
├── models/                          ← NUEVO - Carpeta para modelos
│   └── .gitkeep
├── notebooks/                       ← NUEVO - Jupyter notebooks
│   └── train_model.ipynb           ← NUEVO - Training notebook
├── training/                        ← NUEVO - Scripts de training
│   ├── train.py                    ← NUEVO - Training script
│   ├── evaluate.py                 ← NUEVO - Evaluation script
│   └── prepare_data.py             ← NUEVO - Data preparation

tests/
└── test_ml_features.py             ← NUEVO - Tests de features
```

### Archivos a ACTUALIZAR:

```
src/services/fraud_service.py       ← Integrar feature engineering
src/core/config.py                  ← Agregar ML configs
requirements.txt                    ← Agregar ML dependencies
```

---

## 🔨 PARTE A: FEATURE ENGINEERING

### PASO 1: Crear src/ml/features/base_feature.py

**Especificaciones:**

```python
"""
Base class for feature extractors.
All feature extractors inherit from this class.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class BaseFeatureExtractor(ABC):
    """
    Abstract base class for feature extraction.
    
    All feature extractors must implement extract() method.
    """
    
    def __init__(self, name: str):
        """
        Initialize feature extractor.
        
        Args:
            name: Feature group name (e.g., "velocity", "time")
        """
        self.name = name
        logger.debug(f"Initialized {self.name} feature extractor")
    
    @abstractmethod
    def extract(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract features from transaction data.
        
        Args:
            transaction_data: Transaction data dictionary
            
        Returns:
            Dict with extracted features
            
        Raises:
            Exception: If feature extraction fails
        """
        pass
    
    def get_feature_names(self) -> List[str]:
        """
        Get list of feature names that this extractor produces.
        
        Returns:
            List of feature names
        """
        return []
    
    def validate_data(self, transaction_data: Dict[str, Any]) -> bool:
        """
        Validate that required data is present.
        
        Args:
            transaction_data: Transaction data to validate
            
        Returns:
            True if data is valid
        """
        return True
```

---

### PASO 2: Crear src/ml/features/time_features.py

**Especificaciones:**

```python
"""
Time-based feature extraction.
Extracts temporal patterns from transaction timestamp.
"""

from typing import Dict, Any
from datetime import datetime
import logging
from src.ml.features.base_feature import BaseFeatureExtractor

logger = logging.getLogger(__name__)


class TimeFeatureExtractor(BaseFeatureExtractor):
    """Extract time-based features from transaction"""
    
    def __init__(self):
        super().__init__("time")
    
    def extract(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract time features.
        
        Features:
        - hour_of_day (0-23)
        - day_of_week (0=Monday, 6=Sunday)
        - is_weekend (0 or 1)
        - is_night (22:00-06:00)
        - is_business_hours (09:00-18:00)
        - day_of_month (1-31)
        - is_month_start (first 3 days)
        - is_month_end (last 3 days)
        
        Args:
            transaction_data: Must contain 'timestamp'
            
        Returns:
            Dict with time features
        """
        # TODO:
        # 1. Get timestamp from transaction_data
        # 2. Extract hour, day_of_week, day_of_month
        # 3. Calculate derived features (is_weekend, is_night, etc.)
        # 4. Return dict with all features
        # 5. Log extraction
        pass
    
    def get_feature_names(self) -> List[str]:
        """Return list of feature names"""
        return [
            "hour_of_day",
            "day_of_week",
            "is_weekend",
            "is_night",
            "is_business_hours",
            "day_of_month",
            "is_month_start",
            "is_month_end"
        ]
```

---

### PASO 3: Crear src/ml/features/amount_features.py

**Especificaciones:**

```python
"""
Amount-based feature extraction.
Analyzes transaction amount patterns.
"""

from typing import Dict, Any, List
import logging
import math
from src.ml.features.base_feature import BaseFeatureExtractor

logger = logging.getLogger(__name__)


class AmountFeatureExtractor(BaseFeatureExtractor):
    """Extract amount-based features"""
    
    def __init__(self):
        super().__init__("amount")
    
    def extract(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract amount features.
        
        Features:
        - amount (original)
        - amount_log (log transform for normalization)
        - amount_rounded (round number flag)
        - amount_decimal_places
        - is_high_value (>1000 PEN)
        - is_very_high_value (>5000 PEN)
        - amount_percentile (estimated based on typical distribution)
        
        Args:
            transaction_data: Must contain 'amount'
            
        Returns:
            Dict with amount features
        """
        # TODO:
        # 1. Get amount from transaction_data
        # 2. Calculate log transform: log(amount + 1)
        # 3. Check if round number (e.g., 100.00, 500.00)
        # 4. Count decimal places
        # 5. Calculate thresholds (high value, very high)
        # 6. Estimate percentile (0-100)
        # 7. Return all features
        pass
    
    def get_feature_names(self) -> List[str]:
        return [
            "amount",
            "amount_log",
            "amount_rounded",
            "amount_decimal_places",
            "is_high_value",
            "is_very_high_value",
            "amount_percentile"
        ]
```

---

### PASO 4: Crear src/ml/features/email_features.py

**Especificaciones:**

```python
"""
Email-based feature extraction.
Analyzes customer email patterns for fraud signals.
"""

from typing import Dict, Any, List
import re
import logging
from src.ml.features.base_feature import BaseFeatureExtractor

logger = logging.getLogger(__name__)

# Known temporary/disposable email domains
DISPOSABLE_DOMAINS = {
    "tempmail.com", "guerrillamail.com", "10minutemail.com",
    "mailinator.com", "maildrop.cc", "throwaway.email"
}


class EmailFeatureExtractor(BaseFeatureExtractor):
    """Extract email-based features"""
    
    def __init__(self):
        super().__init__("email")
    
    def extract(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract email features.
        
        Features:
        - email_length
        - email_domain
        - is_disposable_email (0 or 1)
        - is_gmail (0 or 1)
        - is_yahoo (0 or 1)
        - is_corporate_email (has company domain)
        - email_has_numbers (0 or 1)
        - email_numeric_ratio
        
        Args:
            transaction_data: Must contain customer.email
            
        Returns:
            Dict with email features
        """
        # TODO:
        # 1. Get email from transaction_data["customer"]["email"]
        # 2. Extract domain
        # 3. Check if disposable
        # 4. Check major providers (gmail, yahoo)
        # 5. Analyze username pattern (numbers, length)
        # 6. Calculate numeric ratio
        # 7. Return all features
        pass
    
    def get_feature_names(self) -> List[str]:
        return [
            "email_length",
            "email_domain",
            "is_disposable_email",
            "is_gmail",
            "is_yahoo",
            "is_corporate_email",
            "email_has_numbers",
            "email_numeric_ratio"
        ]
```

---

### PASO 5: Crear src/ml/features/feature_engineering.py

**Especificaciones:**

```python
"""
Feature engineering orchestrator.
Coordinates all feature extractors and combines features.
"""

from typing import Dict, Any, List
import logging
from src.ml.features.time_features import TimeFeatureExtractor
from src.ml.features.amount_features import AmountFeatureExtractor
from src.ml.features.email_features import EmailFeatureExtractor
# Import otros extractors cuando estén listos

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    Orchestrates feature extraction from multiple sources.
    
    Combines features from:
    - Time patterns
    - Amount patterns
    - Email patterns
    - Velocity checks (from existing fraud_service)
    - Device patterns
    - Geographic patterns
    """
    
    def __init__(self):
        """Initialize all feature extractors"""
        self.extractors = [
            TimeFeatureExtractor(),
            AmountFeatureExtractor(),
            EmailFeatureExtractor(),
            # Agregar más extractors aquí
        ]
        
        logger.info(
            "FeatureEngineer initialized",
            extra={"num_extractors": len(self.extractors)}
        )
    
    def extract_all_features(
        self,
        transaction_data: Dict[str, Any],
        velocity_features: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Extract all features for ML model.
        
        Args:
            transaction_data: Transaction data dict
            velocity_features: Pre-calculated velocity features (optional)
            
        Returns:
            Dict with all features combined
        """
        all_features = {}
        
        # Extract from each feature extractor
        for extractor in self.extractors:
            try:
                features = extractor.extract(transaction_data)
                all_features.update(features)
                
                logger.debug(
                    f"Extracted {extractor.name} features",
                    extra={"num_features": len(features)}
                )
            except Exception as e:
                logger.error(
                    f"Error extracting {extractor.name} features",
                    extra={"error": str(e)},
                    exc_info=True
                )
        
        # Add velocity features if provided
        if velocity_features:
            all_features.update(velocity_features)
        
        logger.info(
            "All features extracted",
            extra={"total_features": len(all_features)}
        )
        
        return all_features
    
    def get_all_feature_names(self) -> List[str]:
        """Get list of all feature names"""
        all_names = []
        for extractor in self.extractors:
            all_names.extend(extractor.get_feature_names())
        return all_names
    
    def get_feature_count(self) -> int:
        """Get total number of features"""
        return len(self.get_all_feature_names())
```

---

## 🔨 PARTE B: ML MODEL REAL

### PASO 6: Crear ml/training/prepare_data.py

**Especificaciones:**

```python
"""
Data preparation script for ML training.
Loads transaction data from database and prepares training dataset.
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from prisma import Prisma
from src.ml.features.feature_engineering import FeatureEngineer


async def load_transactions(days_back: int = 30) -> pd.DataFrame:
    """
    Load transactions from database.
    
    Args:
        days_back: Number of days of historical data to load
        
    Returns:
        DataFrame with transactions
    """
    # TODO:
    # 1. Connect to Prisma
    # 2. Query transactions from last N days
    # 3. Convert to pandas DataFrame
    # 4. Return DataFrame
    pass


async def prepare_training_data(output_file: str = "training_data.csv"):
    """
    Prepare training dataset with features.
    
    Steps:
    1. Load transactions from database
    2. Extract features for each transaction
    3. Add labels (fraud or not)
    4. Save to CSV
    
    Args:
        output_file: Path to save prepared data
    """
    # TODO:
    # 1. Load transactions
    # 2. Initialize FeatureEngineer
    # 3. Extract features for each transaction
    # 4. Create DataFrame with features + labels
    # 5. Save to CSV
    # 6. Print statistics (fraud rate, feature count, etc.)
    pass


if __name__ == "__main__":
    asyncio.run(prepare_training_data())
```

---

### PASO 7: Crear ml/training/train.py

**Especificaciones:**

```python
"""
XGBoost model training script.
Trains fraud detection model and saves to disk.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score, precision_recall_curve
import xgboost as xgb
import joblib
from datetime import datetime
import json


def load_training_data(filepath: str = "training_data.csv") -> tuple:
    """
    Load and split training data.
    
    Returns:
        (X_train, X_test, y_train, y_test)
    """
    # TODO:
    # 1. Load CSV
    # 2. Separate features (X) and labels (y)
    # 3. Split train/test (80/20)
    # 4. Return splits
    pass


def train_xgboost_model(X_train, y_train, X_test, y_test):
    """
    Train XGBoost classifier.
    
    Args:
        X_train, y_train: Training data
        X_test, y_test: Test data
        
    Returns:
        Trained model
    """
    # TODO:
    # 1. Configure XGBoost parameters:
    #    - max_depth: 6
    #    - learning_rate: 0.1
    #    - n_estimators: 100
    #    - objective: 'binary:logistic'
    #    - scale_pos_weight: (ratio for imbalanced data)
    # 2. Train model with fit()
    # 3. Evaluate on test set
    # 4. Print metrics (accuracy, precision, recall, F1, ROC-AUC)
    # 5. Return trained model
    pass


def save_model(model, feature_names: list, output_dir: str = "../models"):
    """
    Save trained model to disk.
    
    Args:
        model: Trained XGBoost model
        feature_names: List of feature names
        output_dir: Directory to save model
    """
    # TODO:
    # 1. Create output directory if not exists
    # 2. Generate model filename with timestamp
    # 3. Save model with joblib
    # 4. Save feature names as JSON
    # 5. Save metadata (training date, version, metrics)
    # 6. Print save location
    pass


if __name__ == "__main__":
    # Load data
    X_train, X_test, y_train, y_test = load_training_data()
    
    # Train model
    model = train_xgboost_model(X_train, y_train, X_test, y_test)
    
    # Save model
    feature_names = X_train.columns.tolist()
    save_model(model, feature_names)
    
    print("✅ Model training completed successfully!")
```

---

### PASO 8: Crear src/ml/model_manager.py

**Especificaciones:**

```python
"""
Model manager for loading and managing ML models.
Handles model versioning and caching.
"""

from typing import Optional, Dict, Any
import joblib
import json
import os
from pathlib import Path
import logging
from src.core.config import settings

logger = logging.getLogger(__name__)


class ModelManager:
    """
    Manages ML model lifecycle.
    
    Features:
    - Load model from disk
    - Model caching (singleton)
    - Version management
    - Feature validation
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize model manager.
        
        Args:
            model_path: Path to model file (optional, uses settings)
        """
        self.model_path = model_path or settings.ML_MODEL_PATH
        self.model = None
        self.feature_names = []
        self.model_metadata = {}
        self._loaded = False
    
    def load_model(self) -> bool:
        """
        Load model from disk.
        
        Returns:
            True if model loaded successfully
            
        Raises:
            FileNotFoundError: If model file doesn't exist
            Exception: If model loading fails
        """
        # TODO:
        # 1. Check if model_path exists
        # 2. Load model with joblib
        # 3. Load feature_names from JSON
        # 4. Load metadata from JSON
        # 5. Set self._loaded = True
        # 6. Log successful load
        # 7. Return True
        pass
    
    def predict(self, features: Dict[str, Any]) -> float:
        """
        Predict fraud probability for transaction.
        
        Args:
            features: Dict with all required features
            
        Returns:
            Fraud probability (0-1)
            
        Raises:
            ValueError: If model not loaded or features missing
        """
        # TODO:
        # 1. Check if model loaded
        # 2. Validate features (all required features present)
        # 3. Convert features dict to numpy array in correct order
        # 4. Call model.predict_proba()
        # 5. Return fraud probability (probability of class 1)
        # 6. Log prediction
        pass
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "loaded": self._loaded,
            "model_path": self.model_path,
            "feature_count": len(self.feature_names),
            "metadata": self.model_metadata
        }
    
    def validate_features(self, features: Dict[str, Any]) -> tuple[bool, list]:
        """
        Validate that all required features are present.
        
        Returns:
            (valid: bool, missing_features: list)
        """
        missing = [f for f in self.feature_names if f not in features]
        return (len(missing) == 0, missing)


# Global model manager instance
model_manager = ModelManager()
```

---

### PASO 9: Actualizar src/ml/ml_service.py

**Cambios a realizar:**

```python
"""
Machine Learning Service for fraud prediction.
Now uses real XGBoost model instead of rules.
"""

from typing import Dict, Any
import logging
from src.ml.model_manager import model_manager
from src.ml.features.feature_engineering import FeatureEngineer
from src.core.config import settings

logger = logging.getLogger(__name__)


class MLService:
    """
    ML service with XGBoost model.
    
    Replaces rule-based scoring with trained ML model.
    """
    
    def __init__(self):
        """Initialize ML service"""
        self.model_version = settings.ML_MODEL_VERSION
        self.feature_engineer = FeatureEngineer()
        
        # Load model on initialization
        try:
            model_manager.load_model()
            logger.info(f"ML model loaded: {self.model_version}")
        except Exception as e:
            logger.error(f"Failed to load ML model: {e}")
            logger.warning("Falling back to rule-based scoring")
    
    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict fraud probability using XGBoost model.
        
        Args:
            features: Dict with all extracted features
            
        Returns:
            Dict with prediction results
        """
        try:
            # Use ML model if loaded
            if model_manager._loaded:
                fraud_score = model_manager.predict(features)
                
                logger.debug(
                    "ML prediction completed",
                    extra={
                        "fraud_score": fraud_score,
                        "feature_count": len(features)
                    }
                )
            else:
                # Fallback to rule-based if model not loaded
                fraud_score = self._calculate_rule_based_score(features)
                logger.warning("Using rule-based fallback")
            
            # Determine risk level and recommendation
            risk_level = self._get_risk_level(fraud_score)
            recommendation = self._get_recommendation(risk_level)
            
            return {
                "fraud_score": fraud_score,
                "risk_level": risk_level,
                "recommendation": recommendation,
                "model_version": self.model_version
            }
            
        except Exception as e:
            logger.error(
                "Error in ML prediction",
                extra={"error": str(e)},
                exc_info=True
            )
            raise
    
    def _calculate_rule_based_score(self, features: Dict[str, Any]) -> float:
        """
        Fallback rule-based scoring.
        Used if ML model fails to load.
        """
        # Keep existing rule-based logic as fallback
        # ... (código actual de reglas) ...
        pass
    
    # Keep _get_risk_level() and _get_recommendation() unchanged
```

---

### PASO 10: Actualizar src/services/fraud_service.py

**Cambios a realizar:**

```python
# AGREGAR imports:
from src.ml.features.feature_engineering import FeatureEngineer

class FraudService:
    def __init__(
        self,
        transaction_repo: TransactionRepository,
        cache_repo: CacheRepository = None,
        ml_service: MLService = None  # Ya existe
    ):
        self.transaction_repo = transaction_repo
        self.cache_repo = cache_repo
        self.ml_service = ml_service
        
        # AGREGAR:
        self.feature_engineer = FeatureEngineer()
        
        logger.info("FraudService initialized with FeatureEngineer")
    
    async def score_transaction(self, transaction_data: CreateTransactionDto):
        """Score transaction with advanced ML"""
        try:
            # 1. Extract velocity features (existing logic)
            velocity_features = await self._extract_velocity_features(transaction_data)
            
            # 2. NUEVO: Extract ALL features usando FeatureEngineer
            all_features = self.feature_engineer.extract_all_features(
                transaction_data.dict(),
                velocity_features
            )
            
            logger.debug(
                "Features extracted for ML",
                extra={
                    "feature_count": len(all_features),
                    "transaction_id": transaction_data.transaction_id
                }
            )
            
            # 3. Get ML prediction
            ml_prediction = self.ml_service.predict(all_features)
            
            fraud_score = ml_prediction["fraud_score"]
            risk_level = ml_prediction["risk_level"]
            recommendation = ml_prediction["recommendation"]
            
            # 4. Save transaction (existing logic)
            await self._save_transaction(
                transaction_data,
                fraud_score,
                risk_level,
                recommendation
            )
            
            # 5. Build response
            # ... (mantener lógica existente) ...
            
            return response
            
        except Exception as e:
            # ... (mantener exception handling) ...
```

---

## 🔨 PARTE C: TESTING & VALIDATION

### PASO 11: Crear tests/test_ml_features.py

**Especificaciones:**

```python
"""
Tests for ML feature extraction.
Validates that features are extracted correctly.
"""

import pytest
from datetime import datetime
from src.ml.features.time_features import TimeFeatureExtractor
from src.ml.features.amount_features import AmountFeatureExtractor
from src.ml.features.email_features import EmailFeatureExtractor


def test_time_features_extraction():
    """Test time feature extraction"""
    extractor = TimeFeatureExtractor()
    
    transaction_data = {
        "timestamp": datetime(2024, 11, 25, 14, 30, 0)  # Monday, 2:30 PM
    }
    
    features = extractor.extract(transaction_data)
    
    assert features["hour_of_day"] == 14
    assert features["day_of_week"] == 0  # Monday
    assert features["is_weekend"] == 0
    assert features["is_business_hours"] == 1


def test_amount_features_extraction():
    """Test amount feature extraction"""
    extractor = AmountFeatureExtractor()
    
    transaction_data = {"amount": 150.50}
    
    features = extractor.extract(transaction_data)
    
    assert features["amount"] == 150.50
    assert features["amount_log"] > 0
    assert features["is_high_value"] == 0
    assert "amount_decimal_places" in features


def test_email_features_extraction():
    """Test email feature extraction"""
    extractor = EmailFeatureExtractor()
    
    transaction_data = {
        "customer": {
            "email": "test123@gmail.com"
        }
    }
    
    features = extractor.extract(transaction_data)
    
    assert features["email_domain"] == "gmail.com"
    assert features["is_gmail"] == 1
    assert features["is_disposable_email"] == 0
    assert features["email_has_numbers"] == 1
```

---

## ✅ Checklist de Verificación Día 6

### Feature Engineering:
- [ ] TimeFeatureExtractor funciona (8+ features)
- [ ] AmountFeatureExtractor funciona (7+ features)
- [ ] EmailFeatureExtractor funciona (8+ features)
- [ ] FeatureEngineer orquesta todos los extractors
- [ ] Total 70+ features extraídos

### ML Model:
- [ ] Script prepare_data.py genera CSV con features
- [ ] Script train.py entrena XGBoost
- [ ] Modelo guardado en ml/models/
- [ ] ModelManager carga modelo correctamente
- [ ] MLService usa modelo XGBoost (no reglas)

### Integration:
- [ ] FraudService integra FeatureEngineer
- [ ] Endpoint /fraud/score funciona con ML real
- [ ] Latencia <50ms para predicción
- [ ] Accuracy >85% (validar con test set)
- [ ] Fallback a reglas si modelo falla

### Testing:
- [ ] Tests de feature extraction pasan
- [ ] Tests de ML prediction pasan
- [ ] Logs muestran "ML prediction completed"

---

## 🧪 Testing Manual

### 1. Preparar Datos

```bash
cd ml/training
python prepare_data.py

# Esperado: training_data.csv con 1000+ rows, 70+ columns
```

### 2. Entrenar Modelo

```bash
python train.py

# Esperado:
# Accuracy: >85%
# Precision: >80%
# Recall: >75%
# Model saved: ml/models/xgboost_model_YYYYMMDD.pkl
```

### 3. Probar Endpoint

```bash
curl -X POST "http://localhost:3000/api/v1/fraud/score" \
  -H "X-API-Key: dygsom_..." \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "test_ml_001",
    "amount": 150.50,
    "currency": "PEN",
    "timestamp": "2024-11-25T14:30:00Z",
    "customer": {
      "email": "test@gmail.com",
      "ip_address": "181.67.45.123"
    },
    "payment_method": {
      "type": "credit_card",
      "bin": "411111",
      "last4": "1111",
      "brand": "Visa"
    }
  }'

# Esperado: fraud_score calculado con XGBoost
# Ver logs: "ML prediction completed" con feature_count
```

### 4. Ver Logs ML

```bash
docker compose logs api --tail=50 | grep "ML"

# Esperado:
# ML model loaded: v1.0.0
# Features extracted for ML: feature_count=72
# ML prediction completed: fraud_score=0.23
```

---

## 📝 Notas Importantes

### 1. Feature Scaling

XGBoost no requiere feature scaling obligatorio, pero puede ayudar:

```python
# Opcional en prepare_data.py:
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
```

### 2. Class Imbalance

Dataset típicamente tiene 95% legítimas, 5% fraud:

```python
# En train.py:
scale_pos_weight = len(y_train[y_train == 0]) / len(y_train[y_train == 1])

model = xgb.XGBClassifier(
    scale_pos_weight=scale_pos_weight  # Balancea clases
)
```

### 3. Feature Importance

```python
# Después de entrenar:
import matplotlib.pyplot as plt

xgb.plot_importance(model, max_num_features=20)
plt.savefig("feature_importance.png")

# Revisar qué features son más importantes
```

### 4. Model Versioning

```python
# Guardar con timestamp:
model_filename = f"xgboost_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"

# En config.py:
ML_MODEL_PATH = "ml/models/xgboost_model_20241125_143000.pkl"
```

---

## 🎯 Resultado Final Esperado

Al completar Día 6:

✅ **Feature Engineering completo:**
- 70+ features extraídos automáticamente
- Patrones temporales, de monto, email, device
- FeatureEngineer orquesta todo

✅ **ML Model real:**
- XGBoost entrenado con >1000 transacciones
- Accuracy >85%, Precision >80%
- Modelo guardado y versionado
- ModelManager carga modelo

✅ **Production-ready:**
- Endpoint usa ML real (no reglas)
- Latencia <50ms para predicción
- Fallback a reglas si modelo falla
- Logging completo de features y predictions

✅ **Testing:**
- Tests de feature extraction
- Model evaluation metrics
- Integration tests

---

## 🚀 Orden de Implementación

1. Feature extractors (base, time, amount, email)
2. FeatureEngineer (orquestador)
3. prepare_data.py (genera training data)
4. train.py (entrena XGBoost)
5. ModelManager (load/save models)
6. Actualizar MLService (integrar XGBoost)
7. Actualizar FraudService (usar FeatureEngineer)
8. Tests (feature extraction + ML)
9. Restart y probar endpoint

**Tiempo estimado: 6-8 horas** (o dividir en 2 días)

¡ML avanzado listo para producción! 🤖
