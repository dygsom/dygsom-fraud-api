"""
Model training script for fraud detection using XGBoost.

Trains XGBoost classifier on prepared training data.
Evaluates model and saves trained model to disk.

Usage:
    python -m ml.training.train --input training_data.csv --output fraud_model.joblib
"""

import argparse
from pathlib import Path
from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report
)
import xgboost as xgb
import joblib
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_training_data(file_path: str) -> Tuple[pd.DataFrame, pd.Series]:
    """Load training data from CSV
    
    Args:
        file_path: Path to training data CSV
        
    Returns:
        Tuple of (features DataFrame, target Series)
    """
    logger.info(f"Loading training data from {file_path}")
    
    df = pd.read_csv(file_path)
    
    logger.info(
        f"Loaded {len(df)} rows, {len(df.columns)} columns",
        extra={
            "rows": len(df),
            "columns": len(df.columns)
        }
    )
    
    # Separate features and target
    if 'is_fraud' not in df.columns:
        raise ValueError("Target column 'is_fraud' not found in data")
    
    # Drop non-feature columns
    drop_columns = ['is_fraud', 'transaction_id']
    feature_columns = [col for col in df.columns if col not in drop_columns]
    
    X = df[feature_columns]
    y = df['is_fraud']
    
    logger.info(
        f"Features: {len(feature_columns)}, Target distribution: {y.value_counts().to_dict()}"
    )
    
    return X, y


def train_xgboost_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series
) -> xgb.XGBClassifier:
    """Train XGBoost classifier
    
    Args:
        X_train: Training features
        y_train: Training target
        X_val: Validation features
        y_val: Validation target
        
    Returns:
        Trained XGBoost model
    """
    logger.info("Training XGBoost model")
    
    # Calculate scale_pos_weight for imbalanced data
    fraud_count = y_train.sum()
    legit_count = len(y_train) - fraud_count
    scale_pos_weight = legit_count / fraud_count if fraud_count > 0 else 1.0
    
    logger.info(
        f"Class balance: Fraud={fraud_count}, Legitimate={legit_count}, "
        f"scale_pos_weight={scale_pos_weight:.2f}"
    )
    
    # Initialize model
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        objective='binary:logistic',
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        use_label_encoder=False,
        eval_metric='logloss'
    )
    
    # Train with early stopping
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        early_stopping_rounds=10,
        verbose=False
    )
    
    logger.info(
        f"Training complete. Best iteration: {model.best_iteration}",
        extra={"best_iteration": model.best_iteration}
    )
    
    return model


def evaluate_model(
    model: xgb.XGBClassifier,
    X_test: pd.DataFrame,
    y_test: pd.Series
) -> Dict[str, Any]:
    """Evaluate model performance
    
    Args:
        model: Trained model
        X_test: Test features
        y_test: Test target
        
    Returns:
        Dictionary with evaluation metrics
    """
    logger.info("Evaluating model")
    
    # Predictions
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    # Calculate metrics
    metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred, zero_division=0),
        'recall': recall_score(y_test, y_pred, zero_division=0),
        'f1_score': f1_score(y_test, y_pred, zero_division=0),
        'roc_auc': roc_auc_score(y_test, y_pred_proba) if len(np.unique(y_test)) > 1 else 0.0
    }
    
    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    
    metrics['confusion_matrix'] = {
        'true_negative': int(cm[0][0]),
        'false_positive': int(cm[0][1]),
        'false_negative': int(cm[1][0]),
        'true_positive': int(cm[1][1])
    }
    
    logger.info(
        "Evaluation complete",
        extra={
            "accuracy": f"{metrics['accuracy']:.4f}",
            "precision": f"{metrics['precision']:.4f}",
            "recall": f"{metrics['recall']:.4f}",
            "f1_score": f"{metrics['f1_score']:.4f}",
            "roc_auc": f"{metrics['roc_auc']:.4f}"
        }
    )
    
    return metrics


def print_evaluation_report(metrics: Dict[str, Any]) -> None:
    """Print formatted evaluation report
    
    Args:
        metrics: Dictionary with evaluation metrics
    """
    print("\n" + "=" * 50)
    print("MODEL EVALUATION REPORT")
    print("=" * 50)
    
    print(f"\nAccuracy:  {metrics['accuracy']:.4f} ({metrics['accuracy']*100:.2f}%)")
    print(f"Precision: {metrics['precision']:.4f} ({metrics['precision']*100:.2f}%)")
    print(f"Recall:    {metrics['recall']:.4f} ({metrics['recall']*100:.2f}%)")
    print(f"F1 Score:  {metrics['f1_score']:.4f}")
    print(f"ROC AUC:   {metrics['roc_auc']:.4f}")
    
    cm = metrics['confusion_matrix']
    print("\nConfusion Matrix:")
    print(f"  True Negative:  {cm['true_negative']:>6}")
    print(f"  False Positive: {cm['false_positive']:>6}")
    print(f"  False Negative: {cm['false_negative']:>6}")
    print(f"  True Positive:  {cm['true_positive']:>6}")
    
    # Check if targets are met
    print("\n" + "-" * 50)
    print("TARGET METRICS:")
    print("-" * 50)
    
    targets_met = []
    targets_met.append(("Accuracy > 85%", metrics['accuracy'] > 0.85, metrics['accuracy']))
    targets_met.append(("Precision > 80%", metrics['precision'] > 0.80, metrics['precision']))
    targets_met.append(("Recall > 75%", metrics['recall'] > 0.75, metrics['recall']))
    
    for target_name, met, value in targets_met:
        status = "✓ PASS" if met else "✗ FAIL"
        print(f"{status} - {target_name}: {value*100:.2f}%")
    
    all_met = all(met for _, met, _ in targets_met)
    
    print("\n" + "=" * 50)
    if all_met:
        print("✓ ALL TARGET METRICS MET")
    else:
        print("✗ SOME TARGET METRICS NOT MET")
    print("=" * 50 + "\n")


def save_model(model: xgb.XGBClassifier, output_file: str) -> None:
    """Save trained model to disk
    
    Args:
        model: Trained model
        output_file: Path to save model
    """
    logger.info(f"Saving model to {output_file}")
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save with joblib
    joblib.dump(model, output_path)
    
    logger.info(f"Model saved successfully to {output_path.absolute()}")


def train_fraud_model(
    input_file: str,
    output_file: str,
    test_size: float = 0.2,
    val_size: float = 0.1
) -> None:
    """Train fraud detection model
    
    Args:
        input_file: Path to training data CSV
        output_file: Path to save trained model
        test_size: Proportion of data for testing
        val_size: Proportion of training data for validation
    """
    logger.info("Starting model training")
    
    try:
        # Load data
        X, y = load_training_data(input_file)
        
        # Split data: train, validation, test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        X_train, X_val, y_train, y_val = train_test_split(
            X_train, y_train, test_size=val_size, random_state=42, stratify=y_train
        )
        
        logger.info(
            f"Data split: Train={len(X_train)}, Val={len(X_val)}, Test={len(X_test)}"
        )
        
        # Train model
        model = train_xgboost_model(X_train, y_train, X_val, y_val)
        
        # Evaluate on test set
        metrics = evaluate_model(model, X_test, y_test)
        
        # Print report
        print_evaluation_report(metrics)
        
        # Save model
        save_model(model, output_file)
        
        logger.info("Training pipeline complete")
        
    except Exception as e:
        logger.error(f"Error during training: {str(e)}", exc_info=True)
        raise


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Train fraud detection model with XGBoost"
    )
    parser.add_argument(
        '--input',
        type=str,
        default='ml/training/training_data.csv',
        help='Input training data CSV file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='ml/models/fraud_model.joblib',
        help='Output model file path'
    )
    parser.add_argument(
        '--test-size',
        type=float,
        default=0.2,
        help='Proportion of data for testing (default: 0.2)'
    )
    parser.add_argument(
        '--val-size',
        type=float,
        default=0.1,
        help='Proportion of training data for validation (default: 0.1)'
    )
    
    args = parser.parse_args()
    
    # Run training
    train_fraud_model(
        input_file=args.input,
        output_file=args.output,
        test_size=args.test_size,
        val_size=args.val_size
    )


if __name__ == '__main__':
    main()
