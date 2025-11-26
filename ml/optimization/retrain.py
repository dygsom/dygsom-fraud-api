"""
Automated model retraining script.
Retrains model with latest data and compares performance.
"""

import logging
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple
import pandas as pd
import joblib

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from ml.training.prepare_data import prepare_training_data
from ml.training.train import train_xgboost_model, evaluate_model

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def retrain_model(
    days_back: int = 30,
    min_accuracy: float = 0.85,
    output_path: str = "ml/models/fraud_model_new.joblib",
) -> Dict[str, Any]:
    """
    Retrain model with latest data.
    
    Steps:
    1. Load transactions from last N days
    2. Prepare features
    3. Train model
    4. Evaluate performance
    5. Save if accuracy >= min_accuracy
    
    Args:
        days_back: Number of days of data to use
        min_accuracy: Minimum accuracy threshold to save model
        output_path: Path to save new model
        
    Returns:
        Dict with retraining results
    """
    try:
        logger.info(
            "Starting model retraining",
            extra={"days_back": days_back, "min_accuracy": min_accuracy},
        )
        
        # 1. Load recent transactions
        # Note: This requires database connection
        # For now, we'll use a placeholder
        logger.warning(
            "Database connection not implemented - using placeholder training data"
        )
        training_data_path = "ml/training/training_data.csv"
        
        if not os.path.exists(training_data_path):
            logger.error(f"Training data not found: {training_data_path}")
            return {
                "success": False,
                "error": "Training data not found",
                "path": training_data_path,
            }
        
        # 2. Load data
        df = pd.read_csv(training_data_path)
        logger.info(f"Loaded {len(df)} transactions for retraining")
        
        # 3. Train model
        logger.info("Training new model...")
        model, feature_names = train_xgboost_model(df)
        
        # 4. Evaluate model
        logger.info("Evaluating new model...")
        metrics = evaluate_model(model, df, feature_names)
        
        accuracy = metrics.get("accuracy", 0.0)
        logger.info(
            "Model evaluation complete",
            extra={
                "accuracy": accuracy,
                "precision": metrics.get("precision", 0.0),
                "recall": metrics.get("recall", 0.0),
            },
        )
        
        # 5. Save if meets threshold
        if accuracy >= min_accuracy:
            joblib.dump(
                {"model": model, "feature_names": feature_names}, output_path
            )
            logger.info(
                f"New model saved to {output_path}",
                extra={"accuracy": accuracy, "threshold": min_accuracy},
            )
            
            result = {
                "success": True,
                "saved": True,
                "output_path": output_path,
                "accuracy": accuracy,
                "metrics": metrics,
                "feature_count": len(feature_names),
                "training_size": len(df),
            }
        else:
            logger.warning(
                f"Model accuracy {accuracy} below threshold {min_accuracy}, not saving"
            )
            result = {
                "success": True,
                "saved": False,
                "reason": f"Accuracy {accuracy} < threshold {min_accuracy}",
                "accuracy": accuracy,
                "metrics": metrics,
                "training_size": len(df),
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Error retraining model: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


def compare_models(
    old_model_path: str,
    new_model_path: str,
    test_data_path: str,
) -> Dict[str, Any]:
    """
    Compare performance of old and new models.
    
    Args:
        old_model_path: Path to current production model
        new_model_path: Path to newly trained model
        test_data_path: Path to test data
        
    Returns:
        Dict with comparison results
    """
    try:
        logger.info(
            "Comparing models",
            extra={
                "old_model": old_model_path,
                "new_model": new_model_path,
                "test_data": test_data_path,
            },
        )
        
        # Load models
        if not os.path.exists(old_model_path):
            return {
                "success": False,
                "error": f"Old model not found: {old_model_path}",
            }
        
        if not os.path.exists(new_model_path):
            return {
                "success": False,
                "error": f"New model not found: {new_model_path}",
            }
        
        if not os.path.exists(test_data_path):
            return {
                "success": False,
                "error": f"Test data not found: {test_data_path}",
            }
        
        old_data = joblib.load(old_model_path)
        new_data = joblib.load(new_model_path)
        test_df = pd.read_csv(test_data_path)
        
        old_model = old_data["model"]
        old_features = old_data["feature_names"]
        
        new_model = new_data["model"]
        new_features = new_data["feature_names"]
        
        # Evaluate both models
        logger.info("Evaluating old model...")
        old_metrics = evaluate_model(old_model, test_df, old_features)
        
        logger.info("Evaluating new model...")
        new_metrics = evaluate_model(new_model, test_df, new_features)
        
        # Compare
        comparison = {
            "success": True,
            "old_model": {
                "path": old_model_path,
                "accuracy": old_metrics.get("accuracy", 0.0),
                "precision": old_metrics.get("precision", 0.0),
                "recall": old_metrics.get("recall", 0.0),
                "roc_auc": old_metrics.get("roc_auc", 0.0),
            },
            "new_model": {
                "path": new_model_path,
                "accuracy": new_metrics.get("accuracy", 0.0),
                "precision": new_metrics.get("precision", 0.0),
                "recall": new_metrics.get("recall", 0.0),
                "roc_auc": new_metrics.get("roc_auc", 0.0),
            },
            "improvement": {
                "accuracy": new_metrics.get("accuracy", 0.0)
                - old_metrics.get("accuracy", 0.0),
                "precision": new_metrics.get("precision", 0.0)
                - old_metrics.get("precision", 0.0),
                "recall": new_metrics.get("recall", 0.0)
                - old_metrics.get("recall", 0.0),
            },
            "recommendation": "upgrade"
            if new_metrics.get("accuracy", 0.0) > old_metrics.get("accuracy", 0.0)
            else "keep_current",
        }
        
        logger.info(
            "Model comparison complete",
            extra={
                "recommendation": comparison["recommendation"],
                "accuracy_improvement": comparison["improvement"]["accuracy"],
            },
        )
        
        return comparison
        
    except Exception as e:
        logger.error(f"Error comparing models: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    # Example usage
    print("=== Model Retraining ===")
    result = retrain_model(days_back=30, min_accuracy=0.85)
    print(f"\nResult: {result}")
    
    if result.get("saved"):
        print("\n=== Model Comparison ===")
        comparison = compare_models(
            old_model_path="ml/models/fraud_model.joblib",
            new_model_path="ml/models/fraud_model_new.joblib",
            test_data_path="ml/training/training_data.csv",
        )
        print(f"\nComparison: {comparison}")
