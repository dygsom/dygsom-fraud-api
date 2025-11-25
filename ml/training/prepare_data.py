"""
Data preparation script for fraud detection model training.

Loads transactions from database and extracts features using FeatureEngineer.
Saves training data to CSV for model training.

Usage:
    python -m ml.training.prepare_data --output training_data.csv --limit 10000
"""

import asyncio
import argparse
import sys
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
from datetime import datetime
import logging
import os

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
os.chdir(str(project_root))

from prisma import Prisma
from src.ml.features.feature_engineering import FeatureEngineer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def load_transactions(limit: int = None) -> List[Dict[str, Any]]:
    """Load transactions from database
    
    Args:
        limit: Maximum number of transactions to load
        
    Returns:
        List of transaction dictionaries
    """
    logger.info(f"Loading transactions (limit={limit})")
    
    prisma = Prisma()
    await prisma.connect()
    
    try:
        # Query transactions (simple, no includes since schema is flat)
        if limit:
            transactions = await prisma.transaction.find_many(
                take=limit,
                order={'created_at': 'desc'}
            )
        else:
            transactions = await prisma.transaction.find_many(
                order={'created_at': 'desc'}
            )
        
        logger.info(f"Loaded {len(transactions)} transactions")
        
        # Convert to dictionaries with nested structure for feature extraction
        transaction_dicts = []
        for tx in transactions:
            tx_dict = {
                'id': tx.id,
                'transaction_id': tx.transaction_id,
                'amount': float(tx.amount),
                'currency': tx.currency,
                'timestamp': tx.timestamp.isoformat() if tx.timestamp else datetime.utcnow().isoformat(),
                'customer': {
                    'customer_id': tx.customer_id or 'unknown',
                    'email': tx.customer_email or 'unknown@example.com',
                    'phone': tx.customer_phone or '',
                    'ip_address': tx.customer_ip or '0.0.0.0'
                },
                'payment_method': {
                    'type': 'credit_card',  # Default
                    'card': {
                        'bin': tx.card_bin or '000000',
                        'last4': tx.card_last4 or '0000',
                        'brand': tx.card_brand or 'UNKNOWN'
                    }
                },
                'merchant': {
                    'category': 'unknown'  # Default
                },
                'fraud_score': float(tx.fraud_score) if tx.fraud_score else 0.0,
                'risk_level': tx.risk_level,
                'decision': tx.decision
            }
            transaction_dicts.append(tx_dict)
        
        return transaction_dicts
        
    except Exception as e:
        logger.error(f"Error loading transactions: {str(e)}", exc_info=True)
        raise
    finally:
        await prisma.disconnect()


async def extract_features_for_transactions(
    transactions: List[Dict[str, Any]],
    use_velocity: bool = True
) -> pd.DataFrame:
    """Extract features from transactions
    
    Args:
        transactions: List of transaction dictionaries
        use_velocity: Whether to include velocity features
        
    Returns:
        DataFrame with extracted features
    """
    logger.info(f"Extracting features for {len(transactions)} transactions")
    
    feature_engineer = FeatureEngineer()
    
    # Note: Velocity features will be skipped for now as they require Redis
    # They can be calculated separately or added during real-time prediction
    if use_velocity:
        logger.warning("Velocity features disabled for training data preparation")
        use_velocity = False
    
    # Extract features for each transaction
    all_features = []
    for i, tx in enumerate(transactions):
        try:
            # Create velocity features placeholder (zeros)
            velocity_features = {
                'customer_tx_count_1h': 0,
                'customer_tx_count_24h': 0,
                'customer_tx_count_7d': 0,
                'customer_amount_1h': 0.0,
                'customer_amount_24h': 0.0,
                'customer_amount_7d': 0.0,
                'ip_tx_count_1h': 0,
                'ip_tx_count_24h': 0,
                'device_tx_count_1h': 0,
                'device_tx_count_24h': 0
            }
            
            # Extract features
            features = feature_engineer.extract_all_features(tx, velocity_features)
            
            # Add target variable (fraud label)
            fraud_score = tx.get('fraud_score', 0.0)
            # Convert score to binary label (threshold 0.7)
            features['is_fraud'] = int(fraud_score >= 0.7)
            
            # Add transaction ID for reference
            features['transaction_id'] = tx.get('transaction_id', '')
            
            all_features.append(features)
            
            if (i + 1) % 100 == 0:
                logger.info(f"Processed {i + 1}/{len(transactions)} transactions")
                
        except Exception as e:
            logger.warning(f"Error extracting features for transaction {tx.get('id')}: {e}")
            continue
    
    # Convert to DataFrame
    df = pd.DataFrame(all_features)
    
    logger.info(
        f"Feature extraction complete",
        extra={
            "total_transactions": len(transactions),
            "successful_extractions": len(df),
            "total_features": len(df.columns),
            "fraud_count": df['is_fraud'].sum() if 'is_fraud' in df.columns else 0
        }
    )
    
    return df


async def prepare_training_data(
    output_file: str,
    limit: int = None,
    use_velocity: bool = True
) -> None:
    """Prepare training data and save to CSV
    
    Args:
        output_file: Path to output CSV file
        limit: Maximum number of transactions to load
        use_velocity: Whether to include velocity features
    """
    logger.info("Starting data preparation")
    
    try:
        # Load transactions
        transactions = await load_transactions(limit)
        
        if not transactions:
            logger.error("No transactions loaded")
            return
        
        # Extract features
        df = await extract_features_for_transactions(transactions, use_velocity)
        
        if df.empty:
            logger.error("No features extracted")
            return
        
        # Save to CSV
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        df.to_csv(output_path, index=False)
        
        logger.info(
            f"Training data saved to {output_path}",
            extra={
                "rows": len(df),
                "columns": len(df.columns),
                "fraud_percentage": (df['is_fraud'].sum() / len(df) * 100) if 'is_fraud' in df.columns else 0
            }
        )
        
        # Print summary statistics
        print("\n=== Data Preparation Summary ===")
        print(f"Total transactions: {len(df)}")
        print(f"Total features: {len(df.columns)}")
        if 'is_fraud' in df.columns:
            print(f"Fraud transactions: {df['is_fraud'].sum()} ({df['is_fraud'].sum() / len(df) * 100:.2f}%)")
            print(f"Legitimate transactions: {(~df['is_fraud'].astype(bool)).sum()}")
        print(f"\nOutput file: {output_path.absolute()}")
        print("=" * 35)
        
    except Exception as e:
        logger.error(f"Error preparing training data: {str(e)}", exc_info=True)
        raise


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Prepare training data for fraud detection model"
    )
    parser.add_argument(
        '--output',
        type=str,
        default='ml/training/training_data.csv',
        help='Output CSV file path'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Maximum number of transactions to load'
    )
    parser.add_argument(
        '--no-velocity',
        action='store_true',
        help='Exclude velocity features'
    )
    
    args = parser.parse_args()
    
    # Run preparation
    asyncio.run(prepare_training_data(
        output_file=args.output,
        limit=args.limit,
        use_velocity=not args.no_velocity
    ))


if __name__ == '__main__':
    main()
